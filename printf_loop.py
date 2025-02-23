from ctypes import *
import time
import os

# changed to make a private namespace reference
counter = 0

while 1:
    cdll.msvcrt.printf(c_char_p("Loop iteration %d!\n" % counter))
    time.sleep(2)
    counter += 1
