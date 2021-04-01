#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import unittest
import six

@unittest.skipIf(sys.platform.startswith("lin"), "Windows only.")
class PydbgBasicTest(unittest.TestCase):
    """
    Test pydbg import and creation.
    """

    def test_create_pydbg(self):
        import pydbg
        from pydbg import defines
        from pydbg import utils

        tst_pydbg = pydbg.pydbg()


if __name__ == '__main__':
    unittest.main()
