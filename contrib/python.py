#!/usr/bin/env python2.7

import os
import pushlib
from fabric.api import env, execute, local, hide, lcd, settings, path, shell_env
from fabric.colors import yellow


# load some defaults. these are set here so that they may be overridden by
# other parts of the system if necessary.
def load_defaults():
    with hide('running'):
        env.python = local("which python", capture=True).strip()

        # it's ok if we don't find these
        with settings(hide('warnings'), warn_only=True):
            env.python_virtualenv = local("which virtualenv", capture=True).strip()
            env.python_pip = local("which pip", capture=True).strip()
            env.python_pep8 = local("which pep8", capture=True).strip()
            env.python_nose = local("which nosetests", capture=True).strip()
            env.python_coverage = local("which coverage", capture=True).strip()
            env.python_coverage_dir = "{}/cover_db".format(env.test_dir)

        # these are settings that define where built stuff gets put
        env.python_release_dir = env.release_dir
        env.python_release_lib_dir = "lib/python"
        env.python_release_bin_dir = "bin"
        env.python_virtualenv_root_dir = "{}/sbin/venv".format(env.release_dir)


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
            local("mkdir -p {}".format(env.python_virtualenv_root_dir))

            # create the virtualenv
            with lcd(env.python_virtualenv_root_dir):
                local("{} {}".format(env.python_virtualenv, virtualenv_name))
                local("{} --relocatable {}".format(env.python_virtualenv, virtualenv_name))

            with settings(path("{}/{}/bin".format(env.python_virtualenv_root_dir, virtualenv_name), behavior="prepend"),
                          shell_env(VIRTUAL_ENV="{}/{}".format(env.python_virtualenv_root_dir, virtualenv_name))):
                # re-load the default paths to make it uses the virtualenv python
                load_defaults()

                # load requirements into virtualenv
                if (os.path.isfile("{}/requirements.txt".format(env.build_dir))):
                    local("{} install -r {}/requirements.txt".format(env.python_pip, env.build_dir))

                # really build
                self._build()
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

            # get rid of cruft that isn't useful to us
            local("find {}/{} -type f -name \"*.egg-info\" -delete".format(env.python_release_dir, env.python_release_lib_dir))


class PythonTestTask(pushlib.TestTask):
    __doc__ = pushlib.TestTask.__doc__

    def after(self):
        super(PythonTestTask, self).after()

        # run python tests
        if (str(env.get("skip_tests", False)) not in ["True", "1"]):
            with lcd(env.build_dir):
                self.test()
        else:
            print(yellow("Not tests because 'skip_tests' is set."))

    def test(self):
        # if we're running a virtualenv the we need to reload the defaults
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
        if (env.get("python_nose", "") != ""):
            if (env.get("python_coverage", "") != ""):
                local("{} --with-xunit --xunit-file={}/nosetests.xml --no-byte-compile --exe --all-modules --traverse-namespace --with-coverage --cover-inclusive --cover-branches --cover-html --cover-html-dir={} --cover-xml-file={}/coverage.xml".format(env.python_nose, env.test_dir, env.python_coverage_dir, env.python_coverage_dir))
            else:
                local("{} --with-xunit --xunit-file={}/nosetests.xml --no-byte-compile --exe --all-modules --traverse-namespace".format(env.python_nose, env.test_dir))

        if (env.get("python_pep8", "") != ""):
            pep8linted = "{}/.pep8linted".format(env.test_dir)
            if (not os.path.exists(pep8linted)):
                local("touch -m -t 200001010000 {}".format(pep8linted))

            # find python files modified since we last ran pep8
            python_files = local("find {} -type f -newer {} -name \"*.py\"".format(env.build_dir, pep8linted), capture=True).strip()
            python_bin_files = local("find {} -type f -newer {} -not -name .pushrc -exec awk '/^#!.*python/{{print FILENAME}} {{nextfile}}' {{}} +".format(env.build_dir, pep8linted), capture=True).strip()

            if (python_files):
                for file in python_files.split("\n"):
                    local("{} {} --ignore=E501,E221,E241".format(env.python_pep8, file))

            if (python_bin_files):
                for file in python_bin_files.split("\n"):
                    local("{} {} --ignore=E501,E221,E241".format(env.python_pep8, file))

            local("touch {}".format(pep8linted))


class PythonArchiveTask(pushlib.ArchiveTask):
    __doc__ = pushlib.ArchiveTask.__doc__


class PythonLiveTask(pushlib.LiveTask):
    __doc__ = pushlib.LiveTask.__doc__


class PythonCloneTask(pushlib.CloneTask):
    __doc__ = pushlib.CloneTask.__doc__


class PythonDeployTask(pushlib.DeployTask):
    __doc__ = pushlib.DeployTask.__doc__


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
