#!/usr/bin/env python2.7

from fabric.api import env, hide, local

# this is the path to where the sources are located for the clone system. this
# might be something like "/clone/sources".
env.clone_base_dir = "/clone/sources"

# this is the path to the source directory to use on the clone system. this
# might be something like "push/common" and should be set in the project's
# .pushrc file but you can put a default value here.
env.clone_path = "push/common"

# this is the path on the remote system to which the project should be
# deployed. this might be something like "/srv/wwwdata" and it should be set in
# the project's .pushrc file but you can set a default value here.
env.host_path = "/srv/wwwdata"

# this is the user to which we will sudo when on the remote system in order to
# install the project. this might be something like "wwwdata" and should be set
# in the project's .pushrc file but you can set a default value here.
env.host_user = "wwwdata"

# define paths to tools. by using "hide" we avoid showing that we are running
# these commands because nobody cares.
with hide('running'):
    env.tools = {}
    env.tools['ls']    = local("which ls", capture=True).strip()
    env.tools['ln']    = local("which ln", capture=True).strip()
    env.tools['mv']    = local("which mv", capture=True).strip()
    env.tools['rm']    = local("which rm", capture=True).strip()
    env.tools['mkdir'] = local("which mkdir", capture=True).strip()
    env.tools['git']   = local("which git", capture=True).strip()
    env.tools['make']  = local("which make", capture=True).strip()
    env.tools['rsync'] = local("which rsync", capture=True).strip()
    env.tools['tar']   = local("which tar", capture=True).strip()
    env.tools['find']  = local("which find", capture=True).strip()
    env.tools['which'] = local("which which", capture=True).strip()
    env.tools['make']  = local("which make", capture=True).strip()
    env.tools['touch'] = local("which touch", capture=True).strip()
    env.tools['awk']   = local("which awk", capture=True).strip()
