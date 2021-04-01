import my_debugger
from my_debugger_defines import *
from multiprocessing import Pool, Process
import sys
import printf_random
from pydbg import *
from pydbg.defines import *


def static_load(debugger_type=None):
    print("Loading static PID debugger using calc.exe...")
    if(debugger_type == 'pydbg'):
        debugger = pydbg()
    else:
        debugger = my_debugger.debugger()

    if(sys.maxsize > 2**32):
        debugger.load("C:\Windows\SysWOW64\calc.exe")
    else:
        debugger.load("C:\Windows\System32\calc.exe")

    debugger.run()
    debugger.detach()


def printf_infinite():
    import printf_loop


def dyn_load(debugger_type=None, pid=None, function_name=None):
    print("Loading dynamic PID debugger...")
    if(debugger_type == 'pydbg'):
        debugger = pydbg()
    else:
        debugger = my_debugger.debugger()
    debugger.attach(int(pid))
    if(function_name == None):
        printf_address = debugger.func_resolve("msvcrt.dll", "printf")
    else:
        printf_address = debugger.func_resolve("msvcrt.dll", function_name)
    print("[*] Address of printf: 0x%08x" % printf_address)
    # soft breakpoint
    # debugger.bp_set(printf_address)
    # hard breakpoint
    # debugger.bp_set_hw(printf, 1, HW_EXECUTE)
    debugger.run()
    debugger.detach()


def getRegs():
    list = debugger.enumerate_threads()
    # For each thread in the list we want to
    # grab the value of each of the registers38 Chapter 3
    for thread in list:
        thread_context = debugger.get_thread_context(thread)
        # Now let's output the contents of some of the registers
        print("[*] Dumping registers for thread ID: 0x%08x" % thread)
        print("[**] EIP: 0x%08x" % thread_context.Eip)
        print("[**] ESP: 0x%08x" % thread_context.Esp)
        print("[**] EBP: 0x%08x" % thread_context.Ebp)
        print("[**] EAX: 0x%08x" % thread_context.Eax)
        print("[**] EBX: 0x%08x" % thread_context.Ebx)
        print("[**] ECX: 0x%08x" % thread_context.Ecx)
        print("[**] EDX: 0x%08x" % thread_context.Edx)
        print("[*] END DUMP")


if __name__ == '__main__':
    if(len(sys.argv) > 1):
        processes = []
        if(len(sys.argv) > 2):
            pid = int(input("Enter the PID of the process to attach to: "))
        else:
            p1 = Process(target=printf_infinite)
            p1.start()
            pid = p1.pid

        if(sys.argv[1] == 'pydbg'):
            p0 = Process(target=printf_random.run, args=(pid,))
        elif(sys.argv[1][:3] == 'dyn'):
            p0 = Process(target=dyn_load, args=(pid,))

        p0.start()
        p0.join()
        p1.join()
    else:
        static_load()
