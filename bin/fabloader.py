#!/usr/bin/env python2.7

import os
import config
from fabric.api import abort

# try to import the servers list but it's ok if we can't
try:
    import servers
except ImportError:
    pass

# this is the name of the file we're looking for
# this will be updated to have the full, absolute path to the real file
rc = ".pushrc"

# start looking in the current directory and work toward the filesystem root
path = "."

# stop before falling off root of filesystem (should be platform agnostic)
while os.path.split(os.path.abspath(path))[1]:
    joined = os.path.join(path, rc)
    if os.path.exists(joined):
        rc = os.path.abspath(joined)
        break
    path = os.path.join('..', path)

# load the file
execfile(rc)
