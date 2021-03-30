from ctypes import *
import time
import os

# changed to make a private namespace reference
msvcrt = CDLL('msvcrt')
counter = 0

while counter < 10:
    msvcrt.printf(b"Loop iteration %d!\n" % counter)
    time.sleep(2)
    counter += 1
