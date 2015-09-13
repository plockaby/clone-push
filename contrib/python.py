#!/usr/bin/env python2.7

import os
import pushlib
from fabric.api import env, execute, local, hide, lcd
from fabric.colors import yellow


# load some defaults
with hide('running'):
    env.python = local("which python", capture=True)
    env.python_nose = local("which nosetests", capture=True)
    env.python_pep8 = local("which pep8", capture=True)
    env.python_cover_dir = "{}/cover_db".format(env.test_dir)

    env.python_release_dir = env.release_dir
    env.python_release_lib_dir = "lib/python"
    env.python_release_bin_dir = "bin"


class PythonCleanTask(pushlib.CleanTask):
    __doc__ = pushlib.CleanTask.__doc__


class PythonMostlyCleanTask(pushlib.MostlyCleanTask):
    __doc__ = pushlib.MostlyCleanTask.__doc__


class PythonBuildTask(pushlib.BuildTask):
    __doc__ = pushlib.BuildTask.__doc__

    def run(self):
        super(PythonBuildTask, self).run()

        layout = """--root={release_directory} \
                    --install-purelib={release_lib_directory} \
                    --install-platlib={release_lib_directory} \
                    --install-scripts={release_bin_directory} \
                    --install-data=""".format(
                        release_directory=env.python_release_dir,
                        release_lib_directory=env.python_release_lib_dir,
                        release_bin_directory=env.python_release_bin_dir,
                    )

        # build the project using python's build system
        if (os.path.isfile("{}/setup.py".format(env.build_dir))):
            with lcd(env.build_dir):
                local("{} setup.py install {}".format(env.python, layout))
                local("find {}/{} -type f -name \"*.egg-info\" -delete".format(env.python_release_dir, env.python_release_lib_dir))

        for path in ['etc', 'web', 'www']:
            execute(pushlib.CopyDirectoryTask(), path)


class PythonTestTask(pushlib.TestTask):
    __doc__ = pushlib.TestTask.__doc__

    def run(self):
        super(PythonTestTask, self).run()

        # run python tests
        if ("skip_tests" not in env or (str(env.skip_tests) != "True" and str(env.skip_tests) != "1")):
            # run unit tests first
            with lcd(env.build_dir):
                local("{} --with-xunit --xunit-file={}/nosetests.xml --no-byte-compile --exe --all-modules --traverse-namespace --with-coverage --cover-inclusive --cover-branches --cover-html --cover-html-dir={} --cover-xml-file={}/coverage.xml".format(env.python_nose, env.test_dir, env.python_cover_dir, env.python_cover_dir))

            pep8linted = "{}/.pep8linted".format(env.test_dir)

            if (not os.path.exists(pep8linted)):
                local("touch -m -t 200001010000 {}".format(pep8linted))

            python_files = local("find {} -newer {} -type f -name \"*.py\"".format(env.build_dir, pep8linted), capture=True)
            python_bin_files = local("find {} -newer {} -type f -not -name .pushrc -exec awk '/^#!.*python/{{print FILENAME}} {{nextfile}}' {{}} +".format(env.build_dir, pep8linted), capture=True)

            if (python_files):
                for file in python_files.split("\n"):
                    local("{} {} --ignore=E501,E221,E241".format(env.python_pep8, file))

            if (python_bin_files):
                for file in python_bin_files.split("\n"):
                    local("{} {} --ignore=E501,E221,E241".format(env.python_pep8, file))

            local("touch {}".format(pep8linted))
        else:
            print(yellow("Not running tests because 'skip_tests' is set."))


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


cleanTask       = PythonCleanTask()
mostlyCleanTask = PythonMostlyCleanTask()
buildTask       = PythonBuildTask()
testTask        = PythonTestTask()
archiveTask     = PythonArchiveTask()
liveTask        = PythonLiveTask()
cloneTask       = PythonCloneTask()
deployTask      = PythonDeployTask()
