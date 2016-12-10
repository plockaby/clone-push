#!/usr/bin/env python2.7

import os
import sys
import socket
from fabric.tasks import Task
from fabric.api import env, task, settings, hide, execute, local, sudo, abort, warn, put, run, lcd
from fabric.colors import red, cyan, green, yellow
from fabric.contrib.console import confirm


# don't import anything into public when someone loads us
__all__ = []

# colorize errors because!
env.colorize_errors = True

# define paths for doing work
env.current_dir     = os.getcwd()
env.push_dir        = os.path.dirname(os.path.realpath(sys.argv[0]))
env.containment_dir = "{}/.push".format(env.current_dir)
env.build_dir       = "{}/build".format(env.containment_dir)
env.test_dir        = "{}/test".format(env.containment_dir)
env.archive_dir     = "{}/archive".format(env.containment_dir)
env.release_dir     = "{}/release".format(env.containment_dir)
env.temp_dir        = "{}/temp".format(env.containment_dir)

# keep track of what tasks we have run so that we don't run them again. yes,
# fabric has a "runs_once" option but we want to be able to reset it when we
# call "clean" and this lets us do that.
env.completed_tasks = {}

# the path to the root of the git repository
with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
    env.git_root_dir = local("{} rev-parse --show-toplevel".format(env.tools['git']), capture=True)

# get the latest commit/tag and branch of the repo or HEAD if no commit/tag and/or branch
with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
    if (int(local("{} {}/.git/refs/heads/ | wc -l | tr -d ' '".format(env.tools['ls'], env.git_root_dir), capture=True)) != 0):
        env.repo_commit_name = local("{} describe --always --tags".format(env.tools['git']), capture=True)
        env.repo_branch_name = local("{} rev-parse --abbrev-ref HEAD".format(env.tools['git']), capture=True)
        env.repo_tag_name = local("{} describe --tags --exact-match".format(env.tools['git']), capture=True)

    if (env.get("repo_commit_name", "") == ""):
        env.repo_commit_name = "HEAD"
    if (env.get("repo_branch_name", "") == ""):
        env.repo_branch_name = "HEAD"
    if (env.get("repo_tag_name", "") == ""):
        env.repo_tag_name = None

# is set to "true" if the repository is dirty
with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
    if (str(local("{} status -s".format(env.tools['git']), capture=True)) != ""):
        env.repo_is_dirty = True
    else:
        env.repo_is_dirty = False

# the name of the current directory, used as the tool name when doing certain tasks
env.project_name = os.path.basename(os.path.normpath(os.getcwd()))

# the name of the archive we will create when asked to create the archive
# if the thing is dirty the append "dirty" to it
env.repo_version = "{}{}".format(env.repo_commit_name, ("-dirty" if env.repo_is_dirty else ""))
env.archive_name = "{}-version-{}.tar.gz".format(env.project_name, env.repo_version)


class CleanTask(Task):
    """
        removes all built content
    """

    name = "clean"

    def run(self):
        # clean absolutely everything, including the list of tasks that have been run
        env.completed_tasks = {}

        local("{} -rf {}".format(env.tools['rm'], env.containment_dir))
        print(green("Finished cleaning project."))


class MostlyCleanTask(Task):
    """
        removes everything but test output
    """

    name = "mostlyclean"

    def run(self):
        # clean absolutely everything, including the list of tasks that have been run
        env.completed_tasks = {}

        local("{} -rf {}".format(env.tools['rm'], env.build_dir))
        local("{} -rf {}".format(env.tools['rm'], env.archive_dir))
        local("{} -rf {}".format(env.tools['rm'], env.release_dir))
        local("{} -rf {}".format(env.tools['rm'], env.temp_dir))
        print(green("Finished cleaning project."))


class BuildTask(Task):
    """
        builds a copy of the project for testing and deployment
    """

    name = "build"

    def before(self):
        pass

    def after(self):
        pass

    def run(self):
        # don't run this class more than once
        if (env.completed_tasks.get(self.__class__.__name__, False)):
            return

        # run prereqs
        execute('mostlyclean')

        # call before hooks
        self.before()

        # create release directories, build directory gets created by rsync
        local("{} -p {}".format(env.tools['mkdir'], env.release_dir))

        # copy the root directory into the .push/build directory. need to
        # append the trailing slash to make rsync copy the contents of the
        # current directory rather than the current directory itself.
        execute(CopyDirectoryTask(), "{}/".format(env.current_dir), env.build_dir)

        # call after hooks
        self.after()

        print(green("Finished building project."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class TestTask(Task):
    """
        run tests
    """

    name = "test"

    def before(self):
        pass

    def after(self):
        pass

    def run(self):
        # don't run this class more than once
        if (env.completed_tasks.get(self.__class__.__name__, False)):
            return

        # run prereqs
        execute('build')

        # call before hooks
        self.before()

        # no tests by default
        local("{} -p {}".format(env.tools['mkdir'], env.test_dir))

        # call after hooks
        self.after()

        print(green("Finished testing project."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class ArchiveTask(Task):
    """
        creates an archive for deployment
    """

    name = "archive"

    def before(self):
        pass

    def after(self):
        pass

    def run(self):
        # don't run this class more than once
        if (env.completed_tasks.get(self.__class__.__name__, False)):
            return

        # run prereqs
        execute('test')

        # call before hooks
        self.before()

        # can't do anything if there is no release directory
        if (not os.path.isdir(env.release_dir)):
            abort("No release directory found. Cannot create archive.")

        # create the archive
        local("{} -p {}".format(env.tools['mkdir'], env.archive_dir))
        local("{} -czf {}/{} -C {} -p .".format(env.tools['tar'], env.archive_dir, env.archive_name, env.release_dir))

        # call after hooks
        self.after()

        print(green("Finished creating archive."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class LiveTask(Task):
    """
        deploy the project locally or use "live:nickname" to deploy to a particular server
    """

    name = "live"

    def before(self):
        pass

    def after(self):
        pass

    def run(self, *roles):
        # run prereqs
        execute('archive')

        # call before hooks
        self.before()

        # these are all the hosts we're going to deploy to
        hosts = []

        # add any hosts defined using the -H option
        if (len(env.hosts) != 0):
            hosts += env.hosts

        if (len(roles) == 0):
            # if there are no roles given then deploy to localhost but do it
            # through our public interface.
            hosts.append(socket.getfqdn())
        else:
            # look at everything in the argument list and if it is a defined
            # role then add the defined role. if it is not a defined role then
            # add it verbatim because maybe it's a hostname.
            for role in roles:
                if ("servers" in env and role in env.servers):
                    if (isinstance(env.servers[role], list)):
                        hosts += env.servers[role]
                    else:
                        hosts.append(env.servers[role])
                else:
                    warn("Ignoring \"{}\" because it is not in the configured list of servers.".format(role))

        # if we didn't find any hosts then explode
        if (len(hosts) == 0):
            abort("No hosts found for deployment")

        # don't do it in parallel, sometimes the plugin modules have prompts.
        for host in hosts:
            with settings(hosts=host):
                execute("deploy",
                        archive_file="{}/{}".format(env.archive_dir, env.archive_name),
                        remote_user=env.host_user,
                        remote_path=env.host_path,
                        )

        # call after hooks
        self.after()

        print(green("Finished deploying project."))


class CloneTask(Task):
    """
        deploys the project to clone
    """

    name = "clone"

    def before(self):
        pass

    def after(self):
        pass

    def run(self):
        # run prereqs
        execute('archive')

        # call before hooks
        self.before()

        if (str(env.get("no_tag", os.environ.get("NO_TAG", False))) not in ["True", "1"]):
            if (env.repo_is_dirty and not confirm(red("Repository is dirty and thus not tagged. Deploy anyway?"))):
                abort("Aborting at user request.")
            if (env.repo_tag_name is None and not confirm(red("This revision is not tagged. Deploy anyway?"))):
                abort("Aborting at user request.")
                warn("This revision is not tagged.")

            if (not env.repo_is_dirty and env.repo_tag_name is not None):
                print(green("Project is tagged at version {} and ready for release.".format(env.repo_tag_name)))
            else:
                if (env.repo_is_dirty):
                    warn("Repository is dirty and thus not tagged.")
                if (env.repo_tag_name is None):
                    warn("This revision is not tagged.")
        else:
            print(yellow("Not checking to see if the project is tagged because 'no_tag' is set."))

        if ("servers" in env and "clone" in env.servers):
            hosts = []
            if (isinstance(env.servers["clone"], list)):
                hosts += env.servers["clone"]
            else:
                hosts.append(env.servers["clone"])

            for host in hosts:
                with settings(hosts=host):
                    execute("deploy",
                            archive_file="{}/{}".format(env.archive_dir, env.archive_name),
                            remote_user=env.host_user,
                            remote_path="{}/{}{}".format(env.clone_base_dir, env.clone_path, env.host_path),
                            )
        else:
            abort("Could not find \"clone\" in configured list of servers.")

        # call after hooks
        self.after()

        print(green("Finished cloning project."))


class DeployTask(Task):
    """
        deploys the given file to the given host as the given user -- defaults to localhost
    """

    name = "deploy"

    def before(self, **kwargs):
        pass

    def after(self, **kwargs):
        pass

    def run(self, **kwargs):
        # run prereqs
        execute('archive')

        # set default arguments. this is being set like this so that when we
        # forward the arguments to "before" and "after" that they get the
        # default values that we set in here.
        kwargs['archive_file'] = kwargs.get('archive_file', "{}/{}".format(env.archive_dir, env.archive_name))
        kwargs['remote_user'] = kwargs.get('remote_user', env.host_user)
        kwargs['remote_path'] = kwargs.get('remote_path', env.host_path)

        # now get the values we're going to use
        archive_file = kwargs.get('archive_file')
        remote_user = kwargs.get('remote_user')
        remote_path = kwargs.get('remote_path')

        print(cyan("Deploying {} to {}:{} as user {}.".format(archive_file, env.host_string, remote_path, remote_user)))

        # call before hooks
        self.before(**kwargs)

        if (not os.path.isfile("{}/{}".format(env.archive_dir, env.archive_name))):
            abort("No archive file found. Cannot distribute project.")

        # we're going to put it into /tmp
        remote_archive_file = "/tmp/{}".format(os.path.basename(archive_file))

        # figure out where things are on the remote host
        remote_rm = run("which rm", quiet=True)
        remote_mkdir = run("which mkdir", quiet=True)
        remote_tar = run("which tar", quiet=True)

        put(archive_file, remote_archive_file)
        sudo("{} -p {}".format(remote_mkdir, remote_path), user=remote_user)
        sudo("{} zxf {} -C {} -p --no-same-owner --overwrite-dir".format(remote_tar, remote_archive_file, remote_path), user=remote_user)
        run("{} -f {}".format(remote_rm, remote_archive_file))

        # call after hooks
        self.after(**kwargs)


class CleanUpTask(Task):
    def run(self, remote_path, remote_user):
        go_forth = False

        # if the "force_clean_remote" flag is not set then ask the user if they want to delete things
        if (str(env.get("force_clean_remote", False)) in ["True", "1"]):
            go_forth = True
        else:
            if (confirm(red("Are you sure you wish to remove {} on {}? (You can skip this question by setting env.force_clean_remote to True.)".format(remote_path, env.host_string)))):
                go_forth = True

        if (go_forth is True):
            print(cyan("Removing {} from {}.".format(remote_path, env.host_string)))

            # figure out where things are on the remote host
            remote_rm = run("which rm", quiet=True)

            sudo("{} -rf {}".format(remote_rm, remote_path), user=remote_user)


class CopyDirectoryTask(Task):
    def run(self, source, destination=env.release_dir):
        # if the source is not a full path then prepend it with the build
        # directory.
        if (not os.path.isabs(source)):
            source = "{}/{}".format(env.build_dir, source)

        # if the destination is not a full path then prepend it with the
        # release directory.
        if (not os.path.isabs(destination)):
            destination = "{}/{}".format(env.release_dir, destination)

        if (os.path.isdir(source)):
            local("{} -p {}".format(env.tools['mkdir'], destination))
            local("{} -ah --numeric-ids --exclude=.git --exclude=.gitignore --exclude={}/.gitignore --exclude-from=.gitignore --exclude-from={}/.gitignore {} {}".format(env.tools['rsync'], env.git_root_dir, env.git_root_dir, source, destination))
