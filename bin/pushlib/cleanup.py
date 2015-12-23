#!/usr/bin/env python2.7

import pushlib
from fabric.api import env, sudo
from fabric.colors import cyan, red
from fabric.contrib.console import confirm
from fabric.tasks import Task


# this is an extra implementation
class CleanUpTask(Task):
    def run(self, remote_path, remote_user):
        go_forth = False

        # if the "force_clean_remote" flag is not set then ask the user if they want to delete things
        if ("force_clean_remote" in env and (str(env.force_clean_remote) == "True" or str(env.force_clean_remote) == "1")):
            go_forth = True
        else:
            if (confirm(red("Are you sure you wish to remove {} on {}? (You can skip this question by setting env.force_clean_remote to True.)".format(remote_path, env.host_string)))):
                go_forth = True

        if (go_forth is True):
            print(cyan("Removing {} from {}.".format(remote_path, env.host_string)))
            sudo("rm -rf {}".format(remote_path), user=remote_user)