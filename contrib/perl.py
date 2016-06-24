#!/usr/bin/env python2.7

import os
import pushlib
from fabric.api import env, execute, local, hide, lcd, settings, shell_env
from fabric.colors import yellow


# load some defaults. these are set here so that they may be overridden by
# other parts of the system if necessary.
def load_defaults():
    with hide('running'):
        env.perl = local("{} perl".format(env.tools['which']), capture=True)

        # it's ok if we don't find these
        with settings(hide('warnings'), warn_only=True):
            env.perl_prove = local("{} prove".format(env.tools['which']), capture=True)
            env.perl_prove_dir = "{}/prove_db".format(env.test_dir)

        # these are settings that define where built stuff gets put
        env.perl_release_dir = env.release_dir
        env.perl_release_lib_dir = "{}/lib/perl".format(env.perl_release_dir)
        env.perl_release_bin_dir = "{}/bin".format(env.perl_release_dir)
        env.perl_release_man_dir = "{}/man".format(env.perl_release_dir)


class PerlCleanTask(pushlib.CleanTask):
    __doc__ = pushlib.CleanTask.__doc__


class PerlMostlyCleanTask(pushlib.MostlyCleanTask):
    __doc__ = pushlib.MostlyCleanTask.__doc__


class PerlBuildTask(pushlib.BuildTask):
    __doc__ = pushlib.BuildTask.__doc__

    def after(self):
        super(PerlBuildTask, self).after()

        # build the project using perl's build system.
        with lcd(env.build_dir):
            self.build()

        # we are NOT copying bin or lib because perl handles those for us.
        # but we do still care about these other ones.
        for path in ['etc', 'web', 'www']:
            execute(pushlib.CopyDirectoryTask(), path)

    def build(self):
        # this is define din here to allow it to change based on any changes to env
        layout = """PREFIX={release_directory} \
                    LIB={release_lib_directory} \
                    INSTALLSCRIPT={release_bin_directory} \
                    INSTALLBIN={release_bin_directory} \
                    INSTALLMAN1DIR={release_man_directory}/man1 \
                    INSTALLMAN3DIR={release_man_directory}/man3 \
                    INSTALLSITESCRIPT={release_bin_directory} \
                    INSTALLSITEBIN={release_bin_directory} \
                    INSTALLSITEMAN1DIR={release_man_directory}/man1 \
                    INSTALLSITEMAN3DIR={release_man_directory}/man3 \
                    INSTALLVENDORSCRIPT={release_bin_directory} \
                    INSTALLVENDORBIN={release_bin_directory} \
                    INSTALLVENDORMAN1DIR={release_man_directory}/man1 \
                    INSTALLVENDORMAN3DIR={release_man_directory}/man3""".format(
                        release_directory=env.perl_release_dir,
                        release_lib_directory=env.perl_release_lib_dir,
                        release_bin_directory=env.perl_release_bin_dir,
                        release_man_directory=env.perl_release_man_dir
                    )

        if (os.path.isfile("{}/Makefile.PL".format(env.build_dir))):
            local("{} Makefile.PL {}".format(env.perl, layout))
            local("{} install".format(env.tools['make']))

            # get rid of cruft that isn't useful to us
            local("{} {} -type f -name .packlist -delete".format(env.tools['find'], env.perl_release_lib_dir))
            local("{} {} -type f -name perllocal.pod -delete".format(env.tools['find'], env.perl_release_lib_dir))
            local("{} {} -type d -empty -delete".format(env.tools['find'], env.perl_release_lib_dir))


class PerlTestTask(pushlib.TestTask):
    __doc__ = pushlib.TestTask.__doc__

    def after(self):
        super(PerlTestTask, self).after()

        # run perl tests
        if (str(env.get("skip_tests", False)) not in ["True", "1"]):
            with lcd(env.build_dir):
                self.test()
        else:
            print(yellow("Not tests because 'skip_tests' is set."))

    def test(self):
        if (env.get("perl_prove", "") != ""):
            with shell_env(FORMATTER_OUTPUT_DIR="{}".format(env.perl_prove_dir)):
                local("{} -l -r --timer t 1> {}/perltests.xml".format(env.perl_prove, env.test_dir))


class PerlArchiveTask(pushlib.ArchiveTask):
    __doc__ = pushlib.ArchiveTask.__doc__


class PerlLiveTask(pushlib.LiveTask):
    __doc__ = pushlib.LiveTask.__doc__


class PerlCloneTask(pushlib.CloneTask):
    __doc__ = pushlib.CloneTask.__doc__


class PerlDeployTask(pushlib.DeployTask):
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
cleanTask       = PerlCleanTask()
mostlyCleanTask = PerlMostlyCleanTask()
buildTask       = PerlBuildTask()
testTask        = PerlTestTask()
archiveTask     = PerlArchiveTask()
liveTask        = PerlLiveTask()
cloneTask       = PerlCloneTask()
deployTask      = PerlDeployTask()
