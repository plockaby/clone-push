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


class BuildTask(BuildTask):
    def after(self, c):
        super().after(c)

        for path in ["bin", "sbin", "lib", "etc", "web", "www"]:
            if (os.path.isdir(path)):
                tools.copy(path)
