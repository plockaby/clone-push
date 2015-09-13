#!/usr/bin/env python2.7

import pushlib
from fabric.api import execute


class CopyCleanTask(pushlib.CleanTask):
    __doc__ = pushlib.CleanTask.__doc__


class CopyMostlyCleanTask(pushlib.MostlyCleanTask):
    __doc__ = pushlib.MostlyCleanTask.__doc__


class CopyBuildTask(pushlib.BuildTask):
    __doc__ = pushlib.BuildTask.__doc__

    def run(self):
        super(CopyBuildTask, self).run()

        for path in ['bin', 'lib', 'etc', 'web', 'www']:
            execute(pushlib.CopyDirectoryTask(), path)


class CopyTestTask(pushlib.TestTask):
    __doc__ = pushlib.TestTask.__doc__


class CopyArchiveTask(pushlib.ArchiveTask):
    __doc__ = pushlib.ArchiveTask.__doc__


class CopyLiveTask(pushlib.LiveTask):
    __doc__ = pushlib.LiveTask.__doc__


class CopyCloneTask(pushlib.CloneTask):
    __doc__ = pushlib.CloneTask.__doc__


class CopyDeployTask(pushlib.DeployTask):
    __doc__ = pushlib.DeployTask.__doc__


# being passed along so it gets imported into .pushrc
# not exported to fabric and not an executable task
class CopyDirectoryTask(pushlib.CopyDirectoryTask):
    pass


cleanTask       = CopyCleanTask()
mostlyCleanTask = CopyMostlyCleanTask()
buildTask       = CopyBuildTask()
testTask        = CopyTestTask()
archiveTask     = CopyArchiveTask()
liveTask        = CopyLiveTask()
cloneTask       = CopyCloneTask()
deployTask      = CopyDeployTask()
