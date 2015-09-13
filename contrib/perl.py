#!/usr/bin/env python2.7

import os
import pushlib
from fabric.api import env, execute, local, hide, lcd
from fabric.colors import yellow


# load some defaults
with hide('running'):
    env.perl = local("which perl", capture=True)
    env.perl_cover = local("which cover", capture=True)
    env.perl_prove = local("which prove", capture=True)
    env.perl_cover_dir = "{}/cover_db".format(env.test_dir)
    env.perl_prove_dir = "{}/prove_db".format(env.test_dir)

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

    def run(self):
        super(PerlBuildTask, self).run()

        # build the project using perl's build system
        if (os.path.isfile("{}/Makefile.PL".format(env.build_dir))):
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

            with lcd(env.build_dir):
                local("{} Makefile.PL {}".format(env.perl, layout))
                local("make install")
                local("find {} -type f -name .packlist -delete".format(env.perl_release_lib_dir))
                local("find {} -type f -name perllocal.pod -delete".format(env.perl_release_lib_dir))
                local("find {} -type d -empty -delete".format(env.perl_release_lib_dir))

        # now copy any extra directories
        for path in ['etc', 'web', 'www']:
            execute(pushlib.CopyDirectoryTask(), path)


class PerlTestTask(pushlib.TestTask):
    __doc__ = pushlib.TestTask.__doc__

    def run(self):
        super(PerlTestTask, self).run()

        # run perl tests
        if ("skip_tests" not in env or (str(env.skip_tests) != "True" and str(env.skip_tests) != "1")):
            with lcd(env.build_dir):
                local("HARNESS_PERL_SWITCHES=-MDevel::Cover=-db,{} FORMATTER_OUTPUT_DIR={} {} -l -r --timer t 1> {}/perltests.xml".format(env.perl_cover_dir, env.perl_prove_dir, env.perl_prove, env.test_dir))
                local("{} -silent -nosummary -report html_basic -outputdir {} -outputfile index.html {}".format(env.perl_cover, env.perl_cover_dir, env.perl_cover_dir))
                local("{} -silent -nosummary -report clover -outputdir {} -outputfile index.xml {}".format(env.perl_cover, env.perl_cover_dir, env.perl_cover_dir))
        else:
            print(yellow("Not tests because 'skip_tests' is set."))


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


cleanTask       = PerlCleanTask()
mostlyCleanTask = PerlMostlyCleanTask()
buildTask       = PerlBuildTask()
testTask        = PerlTestTask()
archiveTask     = PerlArchiveTask()
liveTask        = PerlLiveTask()
cloneTask       = PerlCloneTask()
deployTask      = PerlDeployTask()
