from ctypes import *
import time
import os

# changed to make a private namespace reference
counter = 0

while 1:
    cdll.msvcrt.printf_s(b"Loop iteration %d!\n" % counter)
    time.sleep(2)
    counter += 1
