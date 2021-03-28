from ctypes import *
from my_debugger_defines import *
import sys
import time

kernel32 = windll.kernel32


class debugger():
    def __init__(self):
        self.h_process = None
        self.pid = None
        self.debugger_active = False
        self.h_thread = None
        self.context = None
        self.exception = None
        self.exception_address = None
        self.breakpoints = {}
        self.first_breakpoint = True
        self.hardware_breakpoints = {}

        # Determine and store the default page size for the system
        system_info = SYSTEM_INFO()
        kernel32.GetSystemInfo(byref(system_info))
        self.page_size = system_info.dwPageSize
        self.guarded_pages = []
        self.memory_breakpoints = {}

    def load(self, path_to_exe):
        # dwCreation flag determines how to create the process
        # set creation_flags = CREATE_NEW_CONSOLE
        # if you want to see the calculator GUI
        creation_flags = DEBUG_PROCESS

        # instantiate the structs
        startupinfo = STARTUPINFO()
        process_information = PROCESS_INFORMATION()

        # The following two options allow the started process to be shown
        # as a separate window. This also illustrates how different
        # settings in the STARTUPINFO struct can affect the debuggee.
        startupinfo.dwFlags = 0x1
        startupinfo.wShowWindow = 0x0

        # We then initialize the cb variable in the STARTUPINFO struct
        # which is just the size of the struct itself
        startupinfo.cb = sizeof(startupinfo)

        if kernel32.CreateProcessW(path_to_exe, None, None, None, None,
                                   creation_flags, None, None,
                                   byref(startupinfo),
                                   byref(process_information)):

            print("[*] We have successfully launched the process!")
            print("[*] The Process ID I have is: %d" %
                  process_information.dwProcessId)
            self.pid = process_information.dwProcessId
            self.h_process = self.open_process(process_information.dwProcessId)
            self.debugger_active = True
        else:
            print("[*] Error with error code %d." % kernel32.GetLastError())

    def open_process(self, pid):
        # PROCESS_ALL_ACCESS = 0x0x001F0FFF
        h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        return h_process

    def attach(self, pid):
        self.h_process = self.open_process(pid)
        # We attempt to attach to the process if this fails we exit the call
        if kernel32.DebugActiveProcess(pid):
            self.debugger_active = True
            self.pid = int(pid)
        else:
            print("[*] Unable to attach to the process.")

    def run(self):
        # Now we have to poll the debuggee for debugging events
        while self.debugger_active == True:
            self.get_debug_event()

    def detach(self):
        if kernel32.DebugActiveProcessStop(self.pid):
            print("[*] Finished debugging. Exiting...")
            return True
        else:
            print("There was an error")
            return False

    def open_thread(self, thread_id):
        h_thread = kernel32.OpenThread(THREAD_ALL_ACCESS, None, thread_id)

        if h_thread is not None:
            return h_thread
        else:
            print("[*] Could not obtain a valid thread handle.")
            return False

    def enumerate_threads(self):
        thread_entry = THREADENTRY32()
        thread_list = []
        snapshot = kernel32.CreateToolhelp32Snapshot(
            TH32CS_SNAPTHREAD, self.pid)

        if snapshot is not None:
            # You have to set the size of the struct or the call will fail
            thread_entry.dwSize = sizeof(thread_entry)
            success = kernel32.Thread32First(snapshot, byref(thread_entry))

            while success:
                if thread_entry.th32OwnerProcessID == self.pid:
                    thread_list.append(thread_entry.th32ThreadID)

                success = kernel32.Thread32Next(snapshot, byref(thread_entry))
            # No need to explain this call, it closes handles so that we don't leak them.
            kernel32.CloseHandle(snapshot)
            return thread_list
        else:
            return False

    def get_thread_context(self, thread_id=None, h_thread=None):
        context = CONTEXT()
        context.ContextFlags = CONTEXT_FULL | CONTEXT_DEBUG_REGISTERS

        # Obtain a handle to the thread
        if h_thread is None:
            self.h_thread = self.open_thread(thread_id)

        if kernel32.GetThreadContext(self.h_thread, byref(context)):
            return context
        else:
            return False

    def get_debug_event(self):
        debug_event = DEBUG_EVENT()
        continue_status = DBG_CONTINUE

        if kernel32.WaitForDebugEvent(byref(debug_event), INFINITE):
            # Let's obtain the thread and context information
            self.h_thread = self.open_thread(debug_event.dwThreadId)
            self.context = self.get_thread_context(self.h_thread)

            print("Event Code: %d Thread ID: %d" %
                  (debug_event.dwDebugEventCode, debug_event.dwThreadId))

            # If the event code is an exception, we want to examine it further.
            if debug_event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT:
                # Obtain the exception code
                self.exception = debug_event.u.Exception.ExceptionRecord.ExceptionCode
                self.exception_address = debug_event.u.Exception.ExceptionRecord.ExceptionAddress

            if self.exception == EXCEPTION_ACCESS_VIOLATION:
                print("Access Violation Detected.")
                # If a breakpoint is detected, we call an internal handler.
            elif self.exception == EXCEPTION_BREAKPOINT:
                continue_status = self.exception_handler_breakpoint()
            elif self.exception == EXCEPTION_GUARD_PAGE:
                print("Guard Page Access Detected.")
            elif self.exception == EXCEPTION_SINGLE_STEP:
                print("Single Stepping.")
                self.exception_handler_single_step()

            kernel32.ContinueDebugEvent(
                debug_event.dwProcessId, debug_event.dwThreadId, continue_status)

    def exception_handler_breakpoint(self):
        print("[*] Inside the breakpoint handler.")
        print("Exception Address: 0x%08x" % self.exception_address)
        return DBG_CONTINUE

    def read_process_memory(self, address, length):
        data = ""
        read_buf = create_string_buffer(length)
        count = c_ulong(0)

        if not kernel32.ReadProcessMemory(self, h_process, address,
                                          read_buf, length, byref(count)):
            return False
        else:
            data += read_buf.raw
            return data

    def write_process_memory(self, address, data):
        count = c_ulong(0)
        length = len(data)
        c_data = c_char_p(data[count.value:])

        if not kernel32.WriteProcessMemory(self.h_process, address,
                                           c_data, length, byref(count)):
            return False
        else:
            return True

    def bp_set(self, address):
        if not address in self.breakpoints:
            try:
                # store the original byte
                original_byte = self.read_process_memory(address, 1)

                # write the IN3 opcode
                self.write_process_memory(address, "\xCC")

                # register the breakpoint in our internal list
                self.breakpoints[address] = (address, original_byte)
            except:
                return False

        return True

    def func_resolve(self, dll, function):
        handle = kernel32.GetModuleHandleA(dll)
        address = kernel32.GetProcAddress(handle, function)
        kernel32.CloseHandle(handle)
        return address

    def bp_set_hw(self, address, length, condition):
        # Check for a valid length value
        if length not in (1, 2, 4):
            return False
        else:
            length -= 1

        # Check for a valid condition
        if condition not in (HW_ACCESS, HW_EXECUTE, HW_WRITE):
            return False

        # Check for available slots
        if not 0 in self.hardware_breakpoints:
            available = 0
        elif not 1 in self.hardware_breakpoints:
            available = 1
        elif not 2 in self.hardware_breakpoints:
            available = 2
        elif not 3 in self.hardware_breakpoints:
            available = 3
        else:
            return False

        # We want to set the dbeug register in every thread
        for thread_id in self.enumerate_threads():
            context = self.get_thread_context(thread_id=thread_id)

            # Enable the appropriate flag in the DR7 register to set the breakpoint
            context.Dr7 |= 1 << (available * 2)

        # Save the address of the breakpoint in the free register that we found
        if available == 0:
            context.Dr0 = address
        elif available == 1:
            context.Dr1 = address
        elif available == 2:
            context.Dr2 = address
        elif available == 3:
            context.Dr3 = address

        # Set the breakpoint condition
        context.Dr7 |= condition << ((available & 4) + 16)

        # Set the length
        context.Dr7 |= length << ((available * 4) + 18)

        # Set thread context with the break set
        h_thread = self.open_thread(thread_id)
        kernel32.SetThreadContext(h_thread, byref(context))

        # update the internal hardware breakpoint array at the used slot index.
        self.hardware_breakpoints[available] = (address, length, condition)
        return True

    def exception_handler_single_step(self):
        # Determine if this single step event occurred in reaction to a hardware breakpoint and grab the hit breakpoint.
        # according to the Intel docs, we should be able to check for the BS flag in Dr6.
        # But it appears that Windows isn't properly propagating that flag down to us.
        if self.context.Dr6 & 0x1 and 0 in self.hardware_breakpoints:
            slot = 0
        elif self.context.Dr6 & 0x2 and 1 in self.hardware_breakpoints:
            slot = 1
        elif self.context.Dr6 & 0x4 and 2 in self.hardware_breakpoints:
            slot = 2
        elif self.context.Dr6 & 0x8 and 3 in self.hardware_breakpoints:
            slot = 3
        else:
            # This wasn't an INT1 generated by a hw breakpoint
            continue_status = DBG_EXCEPTION_NOT_HANDLED

        # Now let's remove the breakpoint from the list
        if self.bp_del_hw(slot):
            continue_status = DBG_CONTINUE

        print("[*] Hardware breakpoint removed")
        return continue_status

    def bp_del_hw(self, slot):
        # Disable the breakpoint for all active threads
        for thread_id in self.enumerate_threads():
            context = self.get_thread_context(thread_id=thread_id)

            # Reset the flags to remove the breakpoint
            context.Dr7 &= ~(1 << (slot * 2))

            # Zero out the address
            if slot == 0:
                context.Dr0 = 0x00000000
            elif slot == 1:
                context.Dr1 = 0x00000000
            elif slot == 2:
                context.Dr2 = 0x00000000
            elif slot == 3:
                context.Dr3 = 0x00000000

            # Remove the condition flag
            context.Dr7 &= ~(3 << ((slot * 4) + 18))

            # Reset the thread's context with the breakpoint removed
            h_thread = self.open_thread(thread_id)
            kernel32.SetThreadContext(h_thread, byref(context))

        # remove the breakpoint from the internal list
        del self.hardware_breakpoints[slot]
        return True

    def bp_set_mem(self, address, size):
        mbi = MEMORY_BASIC_INFORMATION()

        # If our VirtualQueryEx() call doesn't return a full-sized
        # MEMORY_BASIC_INFORMATION then return False
        if kernel32.VirtualQueryEx(self.h_process, address, byref(mbi), sizeof(mbi)) < sizeof(mbi):
            return False

        current_page = mbi.BaseAddress

        # We will set the permissions on all pages that are affected by our memory breakpoint
        while current_page <= address + size:
            # Add the page to the list; this will diferentiate our guarded pages from those that were set by the OS or the debuggee process
            self.guarded_pages.append(current_page)

            old_protection = c_ulong(0)
            if not kernel32.VirtualQueryEx(self.h_process, current_page, size,
                                           mbi.Protect | PAGE_GUARD, byref(old_protection)):
                return False

            # Increase out range by the size of the default system memory page size
            current_page += self.page_size

        # Add the memory breakpoint to our global list
        self.memory_breakpoints[address] = (address, size, mbi)
        return True
