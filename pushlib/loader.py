from invoke import run
from .tools import abort
from . import env
import socket
import pwd
import sys
import os
import re


# this is the name of the host that has clone on it
env.clone_host = "localhost"

# this is the path to where the sources are located for the clone system. this
# might be something like "/clone/sources".
env.clone_base_dir = "/clone/sources"

# this is the path to the source directory to use on the clone system. this
# might be something like "toolop-common" and should be set in the project's
# .pushrc file but you can put a default value here.
env.clone_path = "push/common"

# this is the username that we will use to connect to other hosts. this is
# probably something like "www". this user must be able to install things
# on the remote system
env.host_user = "data"

# this is the path on the remote system to which the project should be
# deployed. this might be something like "/netops" and it can be set in the
# project's .pushrc file but you can set a default value here.
env.host_path = "/srv/data"

# define paths for doing work
env.push_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
env.current_dir = os.getcwd()
env.containment_dir = "{}/.push".format(env.current_dir)
env.build_dir = "{}/build".format(env.containment_dir)
env.archive_dir = "{}/archive".format(env.containment_dir)
env.release_dir = "{}/release".format(env.containment_dir)
env.test_dir = "{}/test".format(env.containment_dir)

# the path to the root of the git repository. this also makes sure that we are
# in a git repository.
env.git_root_dir = run("git rev-parse --show-toplevel", hide=True, warn=True)
if (not env.git_root_dir.ok):
    abort("Could not find root of git repository. Is {} a git repository?".format(env.current_dir))
env.git_root_dir = env.git_root_dir.stdout.strip()

# make sure we have some basic files
if (not os.path.exists("{}/.gitignore".format(env.git_root_dir))):
    abort("Could not find .gitignore file in project root.")
if (not os.path.exists("{}/.pushrc".format(os.getcwd()))):
    abort("Could not find .pushrc file in current directory.")

# get the latest commit/tag and branch of the repo or HEAD if no commit/tag and/or branch
git_branch_count = int(run("ls {}/.git/refs/heads/ | wc -l | tr -d ' '".format(env.git_root_dir), hide=True, warn=True).stdout.strip())
if (git_branch_count > 0):
    env.repo_commit_name = run("git log -1 | head -n 1", hide=True, warn=True).stdout.replace("commit", "").strip()
    env.repo_branch_name = run("git rev-parse --abbrev-ref HEAD", hide=True, warn=True).stdout.strip()
    env.repo_tag_name = run("git describe --tags --exact-match", hide=True, warn=True).stdout.strip()

if (env.get("repo_commit_name", "") == ""):
    env.repo_commit_name = "HEAD"
if (env.get("repo_branch_name", "") == ""):
    env.repo_branch_name = "HEAD"
if (env.get("repo_tag_name", "") == ""):
    env.repo_tag_name = None

# is set to "true" if the repository is dirty
git_dirty_state = run("git status -s", hide=True, warn=True).stdout.strip()
env.repo_is_dirty = (git_dirty_state != "")

# this is the name of the project from which we are deploying
env.git_origin = run("git ls-remote --get-url origin", hide=True, warn=True).stdout.strip()
if (env.git_origin == "origin"):
    abort("Could not find the origin for this git repository.")

# the name of the project is based on the git project and the current directory
project_name_match = re.search(r".*\/(.*)\.git$", env.git_origin)
if (project_name_match):
    env.project_name = project_name_match.group(1)
else:
    abort("Could not extract project name from origin.")

if (os.path.normpath(os.getcwd()) != os.path.normpath(env.git_root_dir)):
    # if we are in a subdirectory to our git project then use that subdirectory
    # as our component name. if there are multiple subdirectories then turn
    # each slash (/) into a hyphen. but we need to ignore the leading hyphen.
    env.project_component = os.path.normpath(os.getcwd()).replace(os.path.normpath(env.git_root_dir), "").replace("/", "-")[1:]
else:
    # otherwise we have no distinct component
    env.project_component = ""

# the name of the archive we will create when asked to create the archive.
env.archive_name = "{}-{}-v{}.tar.gz".format(env.project_name, env.project_component, env.repo_commit_name)

# where am i
env.hostname = socket.getfqdn()

# who am i
env.username = pwd.getpwuid(os.getuid())[0]

# now load tasks from our .pushrc file
try:
    # load the file from the current directory
    exec(open(".pushrc").read())
except Exception as e:
    # this is because printing to stderr in python2 is not the same as python3
    abort("Could not load .pushrc file: {}".format(e))

# now create and assign the deploy class. this way if the user's .pushrc file
# overrides it we can use the overridden version.
env.deploy = DeployTask

# now create all of the tasks based on what was imported most recently
clean_task = CleanTask()
mostlyclean_task = MostlyCleanTask()
build_task = BuildTask(pre=[mostlyclean_task])
test_task = TestTask(pre=[build_task])
archive_task = ArchiveTask(pre=[test_task])
register_task = RegisterTask()
clone_task = CloneTask(pre=[archive_task, register_task])
live_task = LiveTask(pre=[archive_task])
