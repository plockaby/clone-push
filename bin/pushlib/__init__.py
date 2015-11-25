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


# keep track of what tasks we have run so that we don't run them again
env.completed_tasks = {}


# the path to the root of the git repository
with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
    env.git_root_dir = local("{} rev-parse --show-toplevel".format(env.git), capture=True)


# get the latest commit/tag and branch of the repo or HEAD if no commit/tag and/or branch
with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
    if (int(local("ls {}/.git/refs/heads/ | wc -l | tr -d ' '".format(env.git_root_dir), capture=True)) != 0):
        env.repo_commit_name = local("{} describe --always --tags".format(env.git), capture=True).strip()
        env.repo_branch_name = local("{} rev-parse --abbrev-ref HEAD".format(env.git), capture=True).strip()
        env.repo_tag_name = local("{} describe --tags --exact-match".format(env.git), capture=True).strip()

    if ("repo_commit_name" not in env or env.repo_commit_name is None or env.repo_commit_name == ""):
        env.repo_commit_name = "HEAD"
    if ("repo_branch_name" not in env or env.repo_branch_name is None or env.repo_commit_name == ""):
        env.repo_branch_name = "HEAD"
    if ("repo_tag_name" not in env or env.repo_tag_name is None or env.repo_tag_name == ""):
        env.repo_tag_name = None


# is set to "true" if the repository is dirty
with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
    if (str(local("{} status -s".format(env.git), capture=True)) != ""):
        env.repo_is_dirty = True
    else:
        env.repo_is_dirty = False


# the name of the current directory, used as the tool name when doing certain tasks
env.project_name = os.path.basename(os.path.normpath(os.getcwd()))


# the name of the archive we will create when asked to create the archive
# if the thing is dirty the append "dirty" to it
env.repo_version = "{}{}".format(env.repo_commit_name, ("-dirty" if env.repo_is_dirty else ""))
env.archive_name = "{}-version-{}.tar.gz".format(env.project_name, env.repo_version)


# flags for tar and rsync
env.tar_c_flags = "-p"
env.tar_x_flags = "-p --no-same-owner --overwrite-dir"
env.rsync_flags = "-aH --numeric-ids --exclude=.git --exclude=.gitignore --exclude={git_root}/.gitignore --exclude-from=.gitignore --exclude-from={git_root}/.gitignore".format(git_root=env.git_root_dir)


class CleanTask(Task):
    """
        removes all built content
    """

    name = "clean"

    def run(self):
        # clean absolutely everything
        env.completed_tasks = {}

        local("rm -rf {}".format(env.containment_dir))
        print(green("Finished cleaning project."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class MostlyCleanTask(Task):
    """
        remove all build artifacts except test output
    """

    name = "mostlyclean"

    def run(self):
        # clean absolutely everything
        env.completed_tasks = {}

        local("rm -rf {}".format(env.build_dir))
        local("rm -rf {}".format(env.release_dir))
        local("rm -rf {}".format(env.archive_dir))
        local("rm -rf {}".format(env.temp_dir))
        print(green("Finished mostly cleaning project."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class BuildTask(Task):
    """
        builds a copy of the project for testing and deployment
    """

    name = "build"

    def pre_hook(self):
        pass

    def post_hook(self):
        pass

    def run(self):
        # don't run this class more than once
        if (self.__class__.__name__ in env.completed_tasks and env.completed_tasks[self.__class__.__name__]):
            return

        # run prereqs
        execute('clean')

        # call pre hooks
        self.pre_hook()

        # create release directories, build directory gets created by rsync
        local("rm -rf {}".format(env.release_dir))
        local("mkdir -p {}".format(env.release_dir))

        # copy the root directory into the .push/build directory. need to
        # append the trailing slash to make rsync copy the contents of the
        # current directory rather than the current directory itself.
        local("rm -rf {}".format(env.build_dir))
        execute(CopyDirectoryTask(), "{}/".format(env.current_dir), env.build_dir)

        # call post hooks
        self.post_hook()

        print(green("Finished building project."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class TestTask(Task):
    """
        run tests
    """

    name = "test"

    def pre_hook(self):
        pass

    def post_hook(self):
        pass

    def run(self):
        # don't run this class more than once
        if (self.__class__.__name__ in env.completed_tasks and env.completed_tasks[self.__class__.__name__]):
            return

        # run prereqs
        execute('build')

        # call pre hooks
        self.pre_hook()

        # no tests by default
        local("mkdir -p {}".format(env.test_dir))

        # call post hooks
        self.post_hook()

        print(green("Finished testing project."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class ArchiveTask(Task):
    """
        creates an archive for deployment
    """

    name = "archive"

    def pre_hook(self):
        pass

    def post_hook(self):
        pass

    def run(self):
        # don't run this class more than once
        if (self.__class__.__name__ in env.completed_tasks and env.completed_tasks[self.__class__.__name__]):
            return

        # run prereqs
        execute('test')

        # call pre hooks
        self.pre_hook()

        # can't do anything if there is no release directory
        if (not os.path.isdir(env.release_dir)):
            abort("No release directory found. Cannot create archive.")

        # create the archive
        local("mkdir -p {}".format(env.archive_dir))
        local("{tar} -czf {archive_directory}/{archive_name} -C {release_directory} {flags} .".format(tar=env.tar, archive_directory=env.archive_dir, archive_name=env.archive_name, release_directory=env.release_dir, flags=env.tar_c_flags))

        # call post hooks
        self.post_hook()

        print(green("Finished creating archive."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class LiveTask(Task):
    """
        deploy the project locally or use "live:nickname" to deploy to a particular server
    """

    name = "live"

    def pre_hook(self):
        pass

    def post_hook(self):
        pass

    def run(self, *roles):
        # run prereqs
        execute('archive')

        # call pre hooks
        self.pre_hook()

        if (not os.path.isfile("{}/{}".format(env.archive_dir, env.archive_name))):
            abort("No archive file found. Cannot distribute project.")

        if ("no_tag" not in env or (str(env.no_tag) != "True" and str(env.no_tag) != "1")):
            if (env.repo_is_dirty):
                warn("Repository is dirty and thus not tagged.")
            if (env.repo_tag_name is None):
                warn("This revision is not tagged.")

            if (not env.repo_is_dirty and env.repo_tag_name is not None):
                print(green("Project is tagged at version {} and ready for release.".format(env.repo_tag_name)))
        else:
            print(yellow("Not checking to see if the project is tagged because 'no_tag' is set."))

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
                    warn("Ignoring \"{}\" because it is not in the configured list of servers.".format(role, role))

        # if we didn't find any hosts then explode
        if (len(hosts) == 0):
            abort("No hosts found for deployment")

        # don't do it in parallel, sometimes the plugin modules have prompts.
        with settings(hosts=hosts):
            execute("deploy", env.host_user, "{}/{}".format(env.archive_dir, env.archive_name), env.host_path)

        # call post hooks
        self.post_hook()

        print(green("Finished deploying project."))


class CloneTask(Task):
    """
        deploys the project to clone
    """

    name = "clone"

    def pre_hook(self):
        pass

    def post_hook(self):
        pass

    def run(self):
        # run prereqs
        execute('archive')

        # call pre hooks
        self.pre_hook()

        if (not os.path.isfile("{}/{}".format(env.archive_dir, env.archive_name))):
            abort("No archive file found. Cannot distribute project.")

        # see if the repo is clean and tagged before deploying to clone
        # something that isn't "production quality".
        if ("no_tag" not in env or (str(env.no_tag) != "True" and str(env.no_tag) != "1")):
            if (env.repo_is_dirty and not confirm(red("Repository is dirty and thus not tagged. Deploy anyway?"))):
                abort("Aborting at user request.")
            if (env.repo_tag_name is None and not confirm(red("This revision is not tagged. Deploy anyway?"))):
                abort("Aborting at user request.")

            if (not env.repo_is_dirty and env.repo_tag_name is not None):
                print(green("Project is tagged at version {} and ready for release.".format(env.repo_tag_name)))
        else:
            print(yellow("Not checking to see if the project is tagged because 'no_tag' is set."))

        # these are all the hosts we're going to deploy to
        hosts = []

        # add any hosts defined using the -H option
        if (len(env.hosts) != 0):
            hosts += env.hosts

        if ("servers" in env and "clone" in env.servers):
            hosts.append(env.servers["clone"])
        else:
            # if there are no roles given then deploy to localhost but do it
            # through our public interface.
            hosts.append(socket.getfqdn())

        # if we didn't find any hosts then explode
        if (len(hosts) == 0):
            abort("No hosts found for deployment")

        with settings(hosts=hosts):
            execute("deploy", env.host_user, "{}/{}".format(env.archive_dir, env.archive_name), "{}/{}{}".format(env.clone_base_dir, env.clone_path, env.host_path))

        # call post hooks
        self.post_hook()

        print(green("Finished cloning project."))


class CopyDirectoryTask(Task):
    name = "copy"

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
            local("mkdir -p {}".format(destination))
            local("{rsync} {flags} {source} {destination}".format(rsync=env.rsync, flags=env.rsync_flags, source=source, destination=destination))


class DeployTask(Task):
    """
        given a username, the path to an archive file, and the path on the remote host, untar the file on the remote hosts as the given user
    """

    name = "deploy"

    def pre_hook(self):
        pass

    def post_hook(self):
        pass

    def run(self, user, archive_file, remote_path):
        print(cyan("Deploying {} to {} in {} as {}.".format(archive_file, env.host_string, remote_path, user)))

        # call pre hooks
        self.pre_hook()

        # we're going to put it into /tmp
        remote_archive_file = "/tmp/{}".format(os.path.basename(archive_file))

        put(archive_file, remote_archive_file)
        sudo("mkdir -p {prefix}".format(prefix=remote_path), user=user)
        sudo("{tar} zxf {archive} -C {prefix} {flags}".format(tar=env.tar, archive=remote_archive_file, prefix=remote_path, flags=env.tar_x_flags), user=user)
        run("rm -f {}".format(remote_archive_file))

        # call post hooks
        self.post_hook()
