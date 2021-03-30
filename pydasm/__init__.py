import sys

x64 = sys.maxsize > 2**32
python3 = sys.version_info.major == 3

if(x64):
    if(python3):
        import pydasm
    else:
        import amd64
else:
    if(python3):
        import pydasm
    else:
        import x86