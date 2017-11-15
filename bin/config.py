#!/usr/bin/env python2.7

from fabric.api import env, hide, local, settings

# this is the host where our clone system lives.
env.clone_host = "localhost"

# this is the path to where the sources are located for the clone system. this
# might be something like "/clone/sources".
env.clone_base_dir = "/clone/sources"

# this is the path to the source directory to use on the clone system. this
# might be something like "push/common" and should be set in the project's
# .pushrc file but you can put a default value here.
env.clone_path = "push/common"

# this is the path on the remote system to which the project should be
# deployed. this might be something like "/srv/data" and it should be set in
# the project's .pushrc file but you can set a default value here.
env.host_path = "/srv/data"

# this is the user to which we will sudo when on the remote system in order to
# install the project. this might be something like "data" and should be set
# in the project's .pushrc file but you can set a default value here.
env.host_user = "data"

# define paths to tools. by using "hide" we avoid showing that we are running
# these commands because nobody cares. if any of these fails then the whole
# thing will fail.
with hide("running"):
    env.tools = {}
    env.tools["ls"]    = local("which ls", capture=True)
    env.tools["ln"]    = local("which ln", capture=True)
    env.tools["mv"]    = local("which mv", capture=True)
    env.tools["rm"]    = local("which rm", capture=True)
    env.tools["mkdir"] = local("which mkdir", capture=True)
    env.tools["git"]   = local("which git", capture=True)
    env.tools["make"]  = local("which make", capture=True)
    env.tools["rsync"] = local("which rsync", capture=True)
    env.tools["tar"]   = local("which tar", capture=True)
    env.tools["find"]  = local("which find", capture=True)
    env.tools["which"] = local("which which", capture=True)
    env.tools["make"]  = local("which make", capture=True)
    env.tools["touch"] = local("which touch", capture=True)
    env.tools["awk"]   = local("which awk", capture=True)
    env.tools["cat"]   = local("which cat", capture=True)
    env.tools["ssh"]   = local("which ssh", capture=True)

# it's ok if we can't find the dart-config tool.
with settings(hide("running", "warnings"), warn_only=True):
    env.tools["dart"]  = local("which dart-config", capture=True)
