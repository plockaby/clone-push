#!/usr/bin/env python2.7

# ignore PyCrypto errors that appear on RHEL6 when loading fabric
import warnings
from Crypto.pct_warnings import PowmInsecureWarning
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore", PowmInsecureWarning)

# run Fabric like normal
import sys
from fabric.main import main
sys.exit(main())
