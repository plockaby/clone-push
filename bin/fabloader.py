#!/usr/bin/env python2.7

import sys
import config


try:
    # load the file from the current directory
    execfile(".pushrc")
except Exception as e:
    # this is because printing to stderr in python2 is not the same as python3
    sys.stderr.write("Could not load .pushrc file: {}\n".format(str(e)))
    sys.exit(1)
