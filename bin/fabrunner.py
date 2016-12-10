#!/usr/bin/env python2.7

# ignore PyCrypto errors that appear on RHEL6 when loading fabric
try:
    import warnings
    from Crypto.pct_warnings import PowmInsecureWarning
    warnings.filterwarnings("ignore")
    warnings.simplefilter("ignore", PowmInsecureWarning)
except:
    pass

# run Fabric like normal
if __name__ == '__main__':
    import sys
    from fabric.main import main
    sys.exit(main())
