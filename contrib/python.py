from invoke import run
from ..tasks import *
from .. import tools
from .. import env
import os


# we re-export everyting that we've imported from ..tasks
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


# load some defaults. these are set here so that they may be overridden by
# other parts of the system if necessary.
def load_defaults(c):
    env.python = c.run("which python3", hide=True).stdout.strip()
    env.python_virtualenv = c.run("which virtualenv", hide=True, warn=True).stdout.strip()
    env.python_pip = c.run("which pip", hide=True, warn=True).stdout.strip()

    # these are settings that define where built stuff gets put
    env.python_release_dir = env.release_dir
    env.python_release_lib_dir = "lib/python"
    env.python_release_bin_dir = "bin"
    env.python_virtualenv_root_dir = "{}/venv".format(env.release_dir)


class BuildTask(BuildTask):
    def after(self, c):
        super().after(c)

        # figure out where python and things are
        load_defaults(c)

        # build the project using python's build system.
        with c.cd(env.build_dir):
            self.build(c)

        # we are NOT copying bin or lib because python handles those for us.
        # but we do still care about these other ones.
        for path in ["etc", "web", "www"]:
            if (os.path.isdir(path)):
                tools.copy(path)

    def build(self, c):
        # if we're running a virtualenv then we need to reload the defaults
        virtualenv_name = env.get("virtualenv", None)

        if (virtualenv_name is not None):
            # make a place for the virtualenv to exist
            os.makedirs(env.python_virtualenv_root_dir, exist_ok=True)

            # remember where the default python installation went
            system_python_virtualenv = env.python_virtualenv

            # create the virtualenv
            with c.cd(env.python_virtualenv_root_dir):
                c.run("{} {}".format(system_python_virtualenv, virtualenv_name))

            with c.prefix("source {}/{}/bin/activate".format(env.python_virtualenv_root_dir, virtualenv_name)):
                # re-load the default paths to make it uses the virtualenv python
                load_defaults(c)

                # load requirements into virtualenv
                if (os.path.isfile("{}/requirements.txt".format(env.build_dir))):
                    c.run("{} install -r {}/requirements.txt".format(env.python_pip, env.build_dir))

                # really build
                self._build(c)

            # make it so that we can move the virtualenv
            with c.cd(env.python_virtualenv_root_dir):
                c.run("{} --relocatable {}".format(system_python_virtualenv, virtualenv_name))
        else:
            # really build
            self._build(c)

    def _build(self, c):
        # this is defined in here to allow it to change based on any changes to env
        layout = """--root={release_directory} \
                    --install-purelib={release_lib_directory} \
                    --install-platlib={release_lib_directory} \
                    --install-scripts={release_bin_directory} \
                    --install-data=""".format(
                        release_directory=env.python_release_dir,
                        release_lib_directory=env.python_release_lib_dir,
                        release_bin_directory=env.python_release_bin_dir,
                    )  # noqa

        if (os.path.isfile("{}/setup.py".format(env.build_dir))):
            # build the project using python's build system
            c.run("{} setup.py install {}".format(env.python, layout))


class TestTask(TestTask):
    def after(self, c):
        super().after(c)

        # figure out where python and things are
        load_defaults(c)

        # run python tests
        with c.cd(env.build_dir):
            self.test(c)

    def test(self, c):
        # if we're running a virtualenv the we need to reload the defaults
        virtualenv_name = env.get("virtualenv", None)
        if (virtualenv_name is not None):
            with c.prefix("source {}/{}/bin/activate".format(env.python_virtualenv_root_dir, virtualenv_name)):
                # re-load the default paths to make it uses the virtualenv python
                load_defaults(c)

                # really test
                self._test(c)
        else:
            # really test
            self._test(c)

    def _test(self, c):
        if (os.path.isfile("{}/setup.py".format(env.build_dir))):
            # test the project using python's build system
            c.run("{} setup.py test".format(env.python))


class ArchiveTask(ArchiveTask):
    def before(self, c):
        super().before(c)

        # get rid of cruft that isn't useful to us
        c.run("find {}/{} -name \"*.egg-info\" -exec rm -rf {{}} +".format(env.python_release_dir, env.python_release_lib_dir))
        c.run("find {}/{} -name \".eggs\" -exec rm -rf {{}} +".format(env.python_release_dir, env.python_release_lib_dir))
        c.run("find {} -path {}/venv -prune -o -type d -name \"__pycache__\" -print -exec rm -rf {{}} +".format(env.release_dir, env.release_dir))
        c.run("find {} -path {}/venv -prune -o -type f -name \"*.pyc\" -print -exec rm -rf {{}} +".format(env.release_dir, env.release_dir))

        # remove empty directories
        c.run("find {} -type d -empty -delete".format(env.release_dir))


class DeployTask(DeployTask):
    def before(self):
        super().before()

        if (env.get("virtualenv") is not None):
            # remove the existing venv directory to clean out any old files
            self.clean("venv/{}".format(env.virtualenv))
