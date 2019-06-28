from invoke import Task, run
from .tools import copy, warn, abort, confirm
from . import colors
from . import env
import os


# these are the classes that we will let modules override
__all__ = [
    "CleanTask",
    "MostlyCleanTask",
    "BuildTask",
    "TestTask",
    "ArchiveTask",
    "RegisterTask",
    "CloneTask",
    "LiveTask",
    "DeployTask",
]


# this makes it so that the "run" method on the class will be called when the
# task is run. do not change this implementation without knowing what it will
# do to the functionality of this program.
class TaskWrapper(Task):
    def __init__(self, *args, **kwargs):
        def run(c):
            return self.run(c)

        # the task's documentation will come from the method in our child class
        run.__doc__ = self.run.__doc__

        super().__init__(run, *args, **kwargs)

    def run(self, c):
        raise NotImplementedError("{}: property must be implemented in subclass".format(__name__))

    def before(self, c):
        pass

    def after(self, c):
        pass


class CleanTask(TaskWrapper):
    name = "clean"

    def run(self, c):
        """remove all build artifacts"""
        c.run("rm -rf {}".format(env.containment_dir), hide=True)
        print(colors.green("Finished cleaning project."))


class MostlyCleanTask(TaskWrapper):
    name = "mostlyclean"

    def run(self, c):
        """remove most build artifacts"""
        c.run("rm -rf {}".format(env.build_dir), hide=True)
        c.run("rm -rf {}".format(env.archive_dir), hide=True)
        c.run("rm -rf {}".format(env.release_dir), hide=True)
        c.run("rm -rf {}".format(env.test_dir), hide=True)
        print(colors.green("Finished mostly cleaning project."))


class BuildTask(TaskWrapper):
    name = "build"

    def run(self, c):
        """build the project"""

        # create release directories, build directory gets created by rsync
        os.makedirs(env.release_dir, exist_ok=True)

        # call before hooks
        self.before(c)

        # copy the root directory into the .push/build directory. need to
        # append the trailing slash to make rsync copy the contents of the
        # current directory rather than the current directory itself.
        copy("{}/".format(env.current_dir), env.build_dir)

        # call after hooks
        self.after(c)

        print(colors.green("Finished building project."))


class TestTask(TaskWrapper):
    name = "test"

    def run(self, c):
        """run project tests"""

        # run perl tests
        if (str(env.get("skip_tests", os.environ.get("SKIP_TESTS", False))) not in ["True", "1"]):
            # create release directories, build directory gets created by rsync
            os.makedirs(env.test_dir, exist_ok=True)

            # call before hooks
            self.before(c)

            # call after hooks
            self.after(c)

            # only print success if we actually ran the tests
            print(colors.green("Finished testing project."))
        else:
            print(colors.yellow("Not running tests because 'skip_tests' is set."))


class ArchiveTask(TaskWrapper):
    name = "archive"

    def run(self, c):
        """create deployment archive"""

        # create the archive directory
        os.makedirs(env.archive_dir, exist_ok=True)

        # call before hooks
        self.before(c)

        # can't do anything if there is no release directory
        if (not os.path.isdir(env.release_dir)):
            abort("No release directory found. Cannot create archive.")

        # clean up empty directories but make sure the release directory exists
        # sometimes we have projects that don't actually have any files
        c.run("find {} -type d -empty -delete".format(env.release_dir))
        os.makedirs(env.release_dir, exist_ok=True)

        # create the archive
        c.run("tar -czf {}/{} -C {} -p .".format(env.archive_dir, env.archive_name, env.release_dir))

        # call after hooks
        self.after(c)

        print(colors.green("Finished creating archive."))


class CloneTask(TaskWrapper):
    name = "clone"

    def run(self, c):
        """deploy the project to clone"""

        # don't even bother registering or building if there is no tag
        if (str(env.get("no_tag", os.environ.get("NO_TAG", False))) not in ["True", "1"]):
            if (env.repo_is_dirty and not confirm("Repository is dirty and therefore not properly tagged. Deploy anyway?")):
                abort("Aborting at user request.")
            if (len(env.repo_tag_names) == 0 and not confirm("This revision is not tagged. Deploy anyway?")):
                warn("This revision is not tagged.")
                abort("Aborting at user request.")
        else:
            print(colors.yellow("Not checking to see if the project is tagged because 'no_tag' is set."))

        # call before hooks
        self.before(c)

        # actually send it to clone
        env.deploy(
            archive="{}/{}".format(env.archive_dir, env.archive_name),
            remote_user=env.host_user,
            remote_host=env.clone_host,
            remote_path="{}/{}{}".format(env.clone_base_dir, env.clone_path, env.host_path),
        )

        # call after hooks
        self.after(c)

        print(colors.green("Finished sending project to clone."))


# this task isn't like the others and requires a positional argument
class LiveTask(Task):
    name = "live"
    positional = ["name"]

    def __init__(self, *args, **kwargs):
        def run(c, name):
            """deploy the project using "live nickname" to deploy to a particular host"""
            return self.run(c, name)

        super().__init__(run, *args, **kwargs)

    def before(self, c, hosts):
        pass

    def after(self, c, hosts):
        pass

    def run(self, c, name):
        # this has all of the host information in it
        from .hosts import hosts as _hosts

        # these are the hosts that we might deploy to
        hosts = []

        # is the name a tag name? if it is then get all of the hosts
        # that the tag maps to and add them to the list
        if (name in _hosts["tags"]):
            hosts += _hosts["tags"].get(name, [])

        # is the name a host name?
        if (name in _hosts["servers"]):
            hosts.append(name)

        # if the given name wasn't found then maybe there's a reason for that
        if (len(hosts) == 0):
            if (confirm("No server or tag named \"{}\" found in host list. Should we deploy directly to \"{}\"?".format(name, name))):
                hosts.append(name)
            else:
                warn("Ignoring \"{}\" because it is not a valid server or tag name.".format(name))

        # call before hooks
        self.before(c, hosts)

        # don't do it in parallel, sometimes the plugin modules have prompts.
        for host in sorted(hosts):
            env.deploy(
                archive="{}/{}".format(env.archive_dir, env.archive_name),
                remote_user=env.host_user,
                remote_host=host,
                remote_path=env.host_path,
            )

        # call after hooks
        self.after(c, hosts)

        print(colors.green("Finished deploying project."))


# not a real task
class DeployTask(object):
    def __init__(self, archive, remote_user, remote_host, remote_path):
        # make sure the thing we are deploying exists
        if (not os.path.isfile("{}/{}".format(env.archive_dir, env.archive_name))):
            abort("No archive file found. Cannot distribute project.")

        # keep track of these for hooks
        self.archive = archive
        self.remote_user = remote_user
        self.remote_host = remote_host
        self.remote_path = remote_path

        # call before hook
        self.before()

        # NOW we tell people about it. this makes the output print in the correct order
        print(colors.cyan("Deploying {} to {}:{} as {}.".format(archive, remote_host, remote_path, remote_user)))

        # unpack the tar file over the ssh link. we are assuming that the path
        # to tar on the remote host is the same as it is on the local host.
        run("cat {} | ssh -o ConnectTimeout=10 {} sudo -u {} \"tar zxf - -C {} -p --no-same-owner --overwrite-dir\"".format(archive, remote_host, remote_user, remote_path))

        # call after hook
        self.after()

    def clean(self, path):
        remote_path = os.path.join(self.remote_path, path)
        print(colors.cyan("Removing {}:{} as {}.".format(self.remote_host, remote_path, self.remote_user)))

        # log in to the remote host and remove the path. we are assuming
        # that the path to "rm" on the remote host is the same as it is on
        # the local host.
        run("ssh -o ConnectTimeout=30 {} sudo -u {} \"rm -rf {}\"".format(self.remote_host, self.remote_user, remote_path))

    def before(self, **kwargs):
        pass

    def after(self, **kwargs):
        pass


class RegisterTask(TaskWrapper):
    name = "register"

    def run(self, c):
        """registers the task with dart if a .dartrc file is present"""

        # call before hooks
        self.before(c)

        if (os.path.isfile("{}/.dartrc".format(env.current_dir))):
            print(colors.cyan("Registering .dartrc from {} with dart.".format(env.current_dir)))
            c.run("cat {}/.dartrc | dart-config register -".format(env.current_dir))

        # call after hooks
        self.after(c)
