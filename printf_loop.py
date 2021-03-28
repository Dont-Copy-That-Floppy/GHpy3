from ctypes import *
import time
import os

msvcrt = cdll.msvcrt
counter = 0

while counter < 10:
    msvcrt.printf("Loop iteration %d!\n" % counter)
    time.sleep(2)
    counter += 1
