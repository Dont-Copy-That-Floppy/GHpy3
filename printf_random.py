from pydbg import *
from pydbg.defines import *
import struct
import random
# This is our user defined callback function


def printf_randomizer(dbg):
    # Read in the value of the counter at ESP + 0x8 as a DWORD
    parameter_addr = dbg.context.Esp + 0x8
    counter = dbg.read_process_memory(parameter_addr, 4)

    # When we use read_process_memory, it returns a packed binary string.
    # We must first unpack it before we can use it further. PyDbg-A Pure Python Windows Debugger 59
    counter = struct.unpack("L", counter)[0]
    print("Counter: %d" % int(counter))

    # Generate a random number and pack it into binary format so that it is written correctly back into the process
    random_counter = random.randint(1, 100)
    random_counter = struct.pack("L", random_counter)[0]

    # Now swap in our random number and resume the process
    dbg.write_process_memory(parameter_addr, random_counter)

    return DBG_CONTINUE

def run(pid=None):
    # Instantiate the pydbg class
    dbg = pydbg()
    # Now enter the PID of the printf_loop.py process
    if(pid == None):
        pid = input("Enter the printf_loop.py PID: ")
    # Attach the debugger to that process
    dbg = dbg.attach(int(pid))
    # Set the breakpoint with the printf_randomizer function defined as a callback
    printf_address = dbg.func_resolve("msvcrt", "printf_s")
    #dbg.bp_set(printf_address, description="printf_address", handler=printf_randomizer)
    # Resume the process
    dbg.run()

run(19264)