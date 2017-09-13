#!/usr/bin/env python2.7

import os
import pushlib
from fabric.api import env, execute, local, hide, lcd, settings, path, shell_env
from fabric.colors import yellow


# load some defaults. these are set here so that they may be overridden by
# other parts of the system if necessary.
def load_defaults():
    with hide('running'):
        env.python = local("{} python2".format(env.tools['which']), capture=True)

        # it's ok if we don't find these
        with settings(hide('warnings'), warn_only=True):
            # look in the python2 base directory
            env.python_virtualenv = local("{} virtualenv".format(env.tools['which']), capture=True)
            env.python_pip = local("{} pip2".format(env.tools['which']), capture=True)

        # these are settings that define where built stuff gets put
        env.python_release_dir = env.release_dir
        env.python_release_lib_dir = "lib/python"
        env.python_release_bin_dir = "bin"
        env.python_virtualenv_root_dir = "{}/venv".format(env.release_dir)


class PythonCleanTask(pushlib.CleanTask):
    __doc__ = pushlib.CleanTask.__doc__


class PythonMostlyCleanTask(pushlib.MostlyCleanTask):
    __doc__ = pushlib.MostlyCleanTask.__doc__


class PythonBuildTask(pushlib.BuildTask):
    __doc__ = pushlib.BuildTask.__doc__

    def after(self):
        super(PythonBuildTask, self).after()

        # build the project using python's build system.
        with lcd(env.build_dir):
            self.build()

        # we are NOT copying bin or lib because python handles those for us.
        # but we do still care about these other ones.
        for path in ['etc', 'web', 'www']:
            execute(pushlib.CopyDirectoryTask(), path)

    def build(self):
        # if we're running a virtualenv the we need to reload the defaults
        virtualenv_name = env.get("virtualenv", None)
        if (virtualenv_name is not None):
            # make a place for the virtualenv to exist
            local("{} -p {}".format(env.tools['mkdir'], env.python_virtualenv_root_dir))

            # remember where the default python installation went
            system_python_virtualenv = env.python_virtualenv

            # create the virtualenv
            with lcd(env.python_virtualenv_root_dir):
                local("{} --python={} {}".format(system_python_virtualenv, env.python, virtualenv_name))

            with settings(path("{}/{}/bin".format(env.python_virtualenv_root_dir, virtualenv_name), behavior="prepend"),
                          shell_env(VIRTUAL_ENV="{}/{}".format(env.python_virtualenv_root_dir, virtualenv_name))):
                # re-load the default paths to make it uses the virtualenv python
                load_defaults()

                # load requirements into virtualenv
                if (os.path.isfile("{}/requirements.txt".format(env.build_dir))):
                    local("{} install -r {}/requirements.txt".format(env.python_pip, env.build_dir))

                # really build
                self._build()

            # make it so that we can move the virtualenv
            with lcd(env.python_virtualenv_root_dir):
                local("{} --relocatable {}".format(system_python_virtualenv, virtualenv_name))
        else:
            # really build
            self._build()

    def _build(self):
        # this is defined in here to allow it to change based on any changes to env
        layout = """--root={release_directory} \
                    --install-purelib={release_lib_directory} \
                    --install-platlib={release_lib_directory} \
                    --install-scripts={release_bin_directory} \
                    --install-data=""".format(
            release_directory=env.python_release_dir,
            release_lib_directory=env.python_release_lib_dir,
            release_bin_directory=env.python_release_bin_dir,
        )

        if (os.path.isfile("{}/setup.py".format(env.build_dir))):
            # build the project using python's build system
            local("{} setup.py install {}".format(env.python, layout))


class PythonTestTask(pushlib.TestTask):
    __doc__ = pushlib.TestTask.__doc__

    def after(self):
        super(PythonTestTask, self).after()

        # run python tests
        if (str(env.get("skip_tests", os.environ.get("SKIP_TESTS", False))) not in ["True", "1"]):
            with lcd(env.build_dir):
                self.test()
        else:
            print(yellow("Not running tests because 'skip_tests' is set."))

    def test(self):
        # if we're running a virtualenv then we need to reload the defaults
        virtualenv_name = env.get("virtualenv", None)
        if (virtualenv_name is not None):
            with settings(path("{}/{}/bin".format(env.python_virtualenv_root_dir, virtualenv_name), behavior="prepend"),
                          shell_env(VIRTUAL_ENV="{}/{}".format(env.python_virtualenv_root_dir, virtualenv_name))):
                # re-load the default paths to make it uses the virtualenv python
                load_defaults()

                # really test
                self._test()
        else:
            # really test
            self._test()

    def _test(self):
        if (os.path.isfile("{}/setup.py".format(env.build_dir))):
            # test the project using python's build system
            local("{} setup.py test".format(env.python))


class PythonArchiveTask(pushlib.ArchiveTask):
    __doc__ = pushlib.ArchiveTask.__doc__

    def before(self):
        super(PythonArchiveTask, self).before()

        # get rid of cruft that isn't useful to us
        local("{} {}/{} -name \"*.egg-info\" -exec {} -rf {{}} +".format(env.tools['find'], env.python_release_dir, env.python_release_lib_dir, env.tools['rm']))
        local("{} {} -path {}/venv -prune -o -type f -name \"*.pyc\" -print -exec {} -rf {{}} +".format(env.tools['find'], env.release_dir, env.release_dir, env.tools['rm']))

        # remove empty directories
        local("{} {} -type d -empty -delete".format(env.tools['find'], env.release_dir))

class PythonLiveTask(pushlib.LiveTask):
    __doc__ = pushlib.LiveTask.__doc__


class PythonCloneTask(pushlib.CloneTask):
    __doc__ = pushlib.CloneTask.__doc__


class PythonDeployTask(pushlib.DeployTask):
    __doc__ = pushlib.DeployTask.__doc__

    def before(self, **kwargs):
        if (env.get("virtualenv") is not None):
            # remove the existing venv directory to clean out any old files
            execute(CleanUpTask(), "{}/venv/{}".format(kwargs.get('remote_path'), env.virtualenv), kwargs.get('remote_user'))


# being passed along so it gets imported into .pushrc
# not exported to fabric and not an executable task
class CopyDirectoryTask(pushlib.CopyDirectoryTask):
    pass


# being passed along so it gets imported into .pushrc
# not exported to fabric and not an executable task
class CleanUpTask(pushlib.CleanUpTask):
    pass


load_defaults()
cleanTask       = PythonCleanTask()
mostlyCleanTask = PythonMostlyCleanTask()
buildTask       = PythonBuildTask()
testTask        = PythonTestTask()
archiveTask     = PythonArchiveTask()
liveTask        = PythonLiveTask()
cloneTask       = PythonCloneTask()
deployTask      = PythonDeployTask()
