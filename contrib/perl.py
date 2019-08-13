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
    "CloneTask",
    "LiveTask",
    "DeployTask",
]


# load some defaults. these are set here so that they may be overridden by
# other parts of the system if necessary.
def load_defaults(c):
    env.perl = c.run("which perl", hide=True).stdout.strip()
    env.perl_prove = c.run("which prove", hide=True).stdout.strip()
    env.perl_prove_dir = "{}/prove_db".format(env.test_dir)

    # these are settings that define where built stuff gets put
    env.perl_release_dir = env.release_dir
    env.perl_release_lib_dir = "{}/lib/perl".format(env.perl_release_dir)
    env.perl_release_bin_dir = "{}/bin".format(env.perl_release_dir)
    env.perl_release_man_dir = "{}/man".format(env.perl_release_dir)


class BuildTask(BuildTask):
    def after(self, c):
        super().after(c)

        # figure out where perl and things are
        load_defaults(c)

        # build the project using perl's build system.
        with c.cd(env.build_dir):
            self.build(c)

        # we are NOT copying bin or lib because perl handles those for us.
        # but we do still care about these other ones.
        for path in ["etc", "web", "www"]:
            if (os.path.isdir(path)):
                tools.copy(path)

    def build(self, c):
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
                        release_man_directory=env.perl_release_man_dir,
                    )  # noqa

        if (os.path.isfile("{}/Makefile.PL".format(env.build_dir))):
            c.run("{} Makefile.PL {}".format(env.perl, layout))
            c.run("make install")

            # get rid of cruft that isn't useful to us
            c.run("find {} -type f -name .packlist -delete".format(env.perl_release_lib_dir))
            c.run("find {} -type f -name perllocal.pod -delete".format(env.perl_release_lib_dir))
            c.run("find {} -type d -empty -delete".format(env.perl_release_lib_dir))


class TestTask(TestTask):
    def after(self, c):
        super().after(c)

        # figure out where perl and things are
        load_defaults(c)

        # run perl tests
        with c.cd(env.build_dir):
            self.test(c)

    def test(self, c):
        with c.prefix("FORMATTER_OUTPUT_DIR={}".format(env.perl_prove_dir)):
            c.run("{} -l -r --timer t 1> {}/perltests.xml".format(env.perl_prove, env.test_dir))
