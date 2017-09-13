#!/usr/bin/env python2.7

import os
import sys
import json
import socket
import re
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

with settings(hide("warnings", "running", "stdout", "stderr"), warn_only=True):
    # the path to the root of the git repository
    env.git_root_dir = local("{} rev-parse --show-toplevel".format(env.tools["git"]), capture=True)
    if (not env.git_root_dir):
        abort("Could not find root of git repository.")

    # get the latest commit/tag and branch of the repo or HEAD if no commit/tag and/or branch
    if (int(local("{} {}/.git/refs/heads/ | wc -l | tr -d ' '".format(env.tools["ls"], env.git_root_dir), capture=True)) != 0):
        env.repo_commit_name = local("{} log -1 | head -n 1".format(env.tools["git"]), capture=True).replace("commit", "").strip()
        env.repo_branch_name = local("{} rev-parse --abbrev-ref HEAD".format(env.tools["git"]), capture=True)
        env.repo_tag_name = local("{} describe --tags --exact-match".format(env.tools["git"]), capture=True)

    if (env.get("repo_commit_name", "") == ""):
        env.repo_commit_name = "HEAD"
    if (env.get("repo_branch_name", "") == ""):
        env.repo_branch_name = "HEAD"
    if (env.get("repo_tag_name", "") == ""):
        env.repo_tag_name = None

    # is set to "true" if the repository is dirty
    if (str(local("{} status -s".format(env.tools["git"]), capture=True)) != ""):
        env.repo_is_dirty = True
    else:
        env.repo_is_dirty = False

    # this is the name of the project from which we are deploying
    env.git_origin = local("{} ls-remote --get-url origin".format(env.tools["git"]), capture=True)
    if (env.git_origin == "origin"):
        abort("Could not find the origin for this git repository.")

# make sure we have some basic files
if (not os.path.exists("{}/.gitignore".format(env.git_root_dir) or not os.path.exists("{}/.gitignore".format(os.getcwd())))):
    abort("Could not find .gitignore file in project root or current directory.")
if (not os.path.exists("{}/.pushrc".format(os.getcwd()))):
    abort("Could not find .pushrc file in current directory.")

# the name of the project is based on the git project and the current directory
project_name_match = re.search(".*\/(.*)\.git$", env.git_origin)
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

# collect our host information
with settings(hide("running", "stdout"), warn_only=True):
    env.dart = dict()

    # a dict, keyed by tag, value is an array of hostnames
    env.dart["tags"] = dict()

    # a dict, keyed by hostname, value is an array of nocref targets
    env.dart["servers"] = dict()

    # only load hosts if we're going to do a live push
    load_dart_hosts = False
    for x in env.tasks:
        if (x.startswith("live")):
            load_dart_hosts = True

    if (not env.tools["dart"]):
        warn("Could not find dart-config tool.")

    if (env.tools["dart"] and load_dart_hosts):
        try:
            captured = json.loads(local("{} hosts".format(env.tools["dart"], capture=True)))
            for hostname in captured:
                # add tags and hostnames
                if ("tags" in captured[hostname]):
                    for tag in captured[hostname]["tags"]:
                        if (tag not in env.dart["tags"]):
                            env.dart["tags"][tag] = []
                        env.dart["tags"][tag].append(hostname)

                # create a tag called "all" so we can deploy to every host in one command
                if ("all" not in env.dart["tags"]):
                    env.dart["tags"]["all"] = []
                env.dart["tags"]["all"].append(hostname)

                # add hostname and nocref targets
                env.dart["servers"][hostname] = captured[hostname].get("targets")
        except Exception as e:
            warn("Could not decode dart host list: {}".format(repr(e)))


class CleanTask(Task):
    """
        removes all built content
    """

    name = "clean"

    def run(self):
        # clean absolutely everything, including the list of tasks that have been run
        env.completed_tasks = {}

        local("{} -rf {}".format(env.tools["rm"], env.containment_dir))
        print(green("Finished cleaning project."))


class MostlyCleanTask(Task):
    """
        removes everything but test output
    """

    name = "mostlyclean"

    def run(self):
        # clean absolutely everything, including the list of tasks that have been run
        env.completed_tasks = {}

        local("{} -rf {}".format(env.tools["rm"], env.build_dir))
        local("{} -rf {}".format(env.tools["rm"], env.archive_dir))
        local("{} -rf {}".format(env.tools["rm"], env.release_dir))
        local("{} -rf {}".format(env.tools["rm"], env.temp_dir))
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
        execute("mostlyclean")

        # call before hooks
        self.before()

        # create release directories, build directory gets created by rsync
        local("{} -p {}".format(env.tools["mkdir"], env.release_dir))

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
        execute("build")

        # call before hooks
        self.before()

        # no tests by default
        local("{} -p {}".format(env.tools["mkdir"], env.test_dir))

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
        execute("test")

        # call before hooks
        self.before()

        # can't do anything if there is no release directory
        if (not os.path.isdir(env.release_dir)):
            abort("No release directory found. Cannot create archive.")

        # clean up empty directories but make sure the release directory exists
        # sometimes we have projects that don't actually have any files
        local("{} {} -type d -empty -delete".format(env.tools["find"], env.release_dir))
        local("{} -p {}".format(env.tools["mkdir"], env.release_dir))

        # create the archive
        local("{} -p {}".format(env.tools["mkdir"], env.archive_dir))
        local("{} -czf {}/{} -C {} -p .".format(env.tools["tar"], env.archive_dir, env.archive_name, env.release_dir))

        # call after hooks
        self.after()

        print(green("Finished creating archive."))

        # record that we've run this step
        env.completed_tasks[self.__class__.__name__] = True


class LiveTask(Task):
    """
        deploy the project using "live:nickname" to deploy to a particular server
    """

    name = "live"

    def before(self):
        pass

    def after(self):
        pass

    def run(self, *roles):
        # run prereqs
        execute("archive")

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
                    if (confirm(red("No host or tag named \"{}\" found in server list. Should we deploy to \"{}\" anyway?".format(role, role)))):
                        hosts.append(role)
                    else:
                        warn("Ignoring \"{}\" because it is not in the configured list of servers.".format(role))

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
        execute("archive")

        # call before hooks
        self.before()

        if (str(env.get("no_tag", os.environ.get("NO_TAG", False))) not in ["True", "1"]):
            if (env.repo_is_dirty and not confirm(red("Repository is dirty and therefore not tagged. Deploy anyway?"))):
                abort("Aborting at user request.")
            if (env.repo_tag_name is None and not confirm(red("This revision is not tagged. Deploy anyway?"))):
                warn("This revision is not tagged.")
                abort("Aborting at user request.")

            if (not env.repo_is_dirty and env.repo_tag_name is not None):
                # tag must look like: v#.# or v#.#-asdf
                valid_tag_pattern = re.compile("^v\d+\.\d+($|\-)")
                if (not valid_tag_pattern.match(env.repo_tag_name)):
                    if (not confirm(red("Repository tag {} does not match format vX.Y. Deploy anyway?".format(env.repo_tag_name)))):
                        abort("Aborting at user request.")
                else:
                    print(green("Project is tagged at version {} and ready for release.".format(env.repo_tag_name)))
            else:
                if (env.repo_is_dirty):
                    warn("Repository is dirty and therefore not tagged.")
                if (env.repo_tag_name is None):
                    warn("This revision is not tagged.")
        else:
            print(yellow("Not checking to see if the project is tagged because 'no_tag' is set."))

        with settings(hosts=env.clone_host):
            execute("deploy",
                    archive_file="{}/{}".format(env.archive_dir, env.archive_name),
                    remote_user=env.host_user,
                    remote_path="{}/{}{}".format(env.clone_base_dir, env.clone_path, env.host_path),
                    )

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
        execute("archive")

        # set default arguments. this is being set like this so that when we
        # forward the arguments to "before" and "after" that they get the
        # default values that we set in here.
        kwargs["archive_file"] = kwargs.get("archive_file", "{}/{}".format(env.archive_dir, env.archive_name))
        kwargs["remote_user"] = kwargs.get("remote_user", env.host_user)
        kwargs["remote_path"] = kwargs.get("remote_path", env.host_path)

        # now get the values we're going to use
        archive_file = kwargs.get("archive_file")
        remote_user = kwargs.get("remote_user")
        remote_path = kwargs.get("remote_path")

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
            local("{} -p {}".format(env.tools["mkdir"], destination))
            local("{} -ah --numeric-ids --exclude=.git --exclude=.gitignore --exclude={}/.gitignore --exclude-from=.gitignore --exclude-from={}/.gitignore {} {}".format(env.tools["rsync"], env.git_root_dir, env.git_root_dir, source, destination))
