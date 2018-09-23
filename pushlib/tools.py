from invoke import run
from . import colors
from . import env
import sys
import os


def warn(msg):
    sys.stderr.write(colors.magenta("\nWARNING: {}\n\n".format(msg)))


def abort(msg):
    sys.stderr.write(colors.red("\nFATAL: {}\n\n".format(msg, sys.stderr)))
    sys.stderr.write(colors.red("Aborting.\n"))

    e = SystemExit(1)
    e.message = msg
    raise e


def confirm(question, assume_yes=True):
    suffix = "Y/n" if assume_yes else "y/N"

    # Loop till we get something we like
    while (True):
        response = input(colors.red("{} [{}] ".format(question, suffix)))
        response = response.lower().strip()  # normalize

        # default
        if (not response):
            return assume_yes

        # yes
        if (response in ["y", "yes"]):
            return True

        # no
        if (response in ["n", "no"]):
            return False

        # didn't get empty, yes or no, so complain and loop
        print("I didn't understand you. Please specify '(y)es' or '(n)o'.")


# used to move files around
def copy(src, dst=None):
    # see if the destination needs a default value
    if (dst is None):
        dst = env.release_dir

    # if the source is not a full path then prepend it with the build directory
    if (not os.path.isabs(src)):
        src = "{}/{}".format(env.build_dir, src)

    # if the destination is not a full path then prepend it with the
    # release directory.
    if (not os.path.isabs(dst)):
        dst = "{}/{}".format(env.release_dir, dst)

    # make a destination directory, if it doesn't exist
    os.makedirs(dst, exist_ok=True)

    # .gitignore in git-root is required, also use cwd if present
    exclude_string = "--exclude=.gitignore --exclude-from={}/.gitignore".format(env.git_root_dir)
    exclude_string += " --exclude-from=.gitignore " if os.path.isfile(".gitignore") else ""

    # now rsync the data over
    run("rsync -ah --numeric-ids --exclude=.git {} {} {}".format(exclude_string, src, dst))
