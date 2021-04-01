# Gray Hat Python 3
## Not Finished
 Tutorial code for [Gray Hat Python](https://nostarch.com/ghpython.htm), rewritten for [Python 3 64bit](https://www.python.org/ftp/python/3.9.2/python-3.9.2-amd64.exe) compatibility.\
 \
Main [downlaod](https://nostarch.com/download/ghpython_src.zip) directory src, is included in the package. (Not refractored for python3)\
Refractored [PyDBG](https://github.com/OpenRCE/pydbg) for python3 is included in the package.\
Pre-compiled version using [pydasm](https://github.com/axcheron/pydasm) are included for pydbg. If you want to build it yourself, use the .msi executable to compile with python2.7.\
\
Simplified the startup procedure for testing my_debugger.py with my_test.py. Now, just use the term dynamic or dyn, to initiate the printf_loop.\
ex: `python my_test.py dyn`\
If you want to attach to a different program, use `python my_test.py dyn *pid*`.
