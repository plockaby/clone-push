from invoke import run
from .. import colors
from .. import env
import os


class WrapperTask(object):
    def __init__(self):
        # do bin/sbin wrapper links
        if (str(env.get("skip_wrappers", os.environ.get("SKIP_WRAPPERS", False))) not in ["True", "1"]):
            for wrap in ["bin", "sbin"]:
                if (os.path.isdir("{}/{}".format(env.release_dir, wrap))):
                    os.makedirs(os.path.join(env.release_dir, wrap, ".{}".format(wrap)), exist_ok=True)
                    files = [os.path.join(env.release_dir, wrap, f) for f in os.listdir(os.path.join(env.release_dir, wrap)) if not os.path.isdir(os.path.join(env.release_dir, wrap, f))]
                    for f in files:
                        path = os.path.dirname(f)
                        base = os.path.basename(f)
                        run("mv {} {}/.{}".format(f, path, wrap))
                        run("ln -sf .wrapper {}".format(f))
        else:
            print(colors.yellow("Not creating wrappers because 'skip_wrappers' is set."))
