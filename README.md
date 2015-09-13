# push

### About

This is a tool to build, test, and deploy your projects to either another
server or to a [clone](https://github.com/plockaby/clone) system for deployment
by `clone`.


### Installing

The installation for `push` is not the most standard. Configuration files must
be written before it can be deployed. So follow these steps to get those
created.


1. Edit `bin/config.py`. You can change the paths in here for things like `ssh`
and `rsync`. However, there are a few specific configuration value that MUST be
set. These can all be overridden in a project's `.pushrc` file.


    * `env.clone_base_dir` is the path on your clone system (see
      [clone](https://github.com/plockaby/clone)) to where all sources can be
      found. This should be set to something like `/clone/sources`.

    * `env.clone_path` is the default clone source directory to use on the
      `clone` system when deploying projects. This might be something like
      `push/common` and is appended to the `env.clone_base_dir`. This should
      generally be set by the project's `.pushrc` file but you can set a
      default value here.

    * `env.host_path` is the default root directory on the remote host to which
      projects will be deployed. This might be something like `/srv/www` and,
      when deploying to the `clone` system, this will be appended to
      `env.clone_path`.

    * `env.host_user` is the default user on the remote host that the project
      will be deployed as. This user must be one that the user can `sudo` to on
      remote the remote hosts to which one will be deploying. This might be
      something like `www` or `ops`.


2. Copy `bin/servers.py.example` to `bin/servers.py`. This is where you set all
   of the servers to which you might deploy manually. There is only one mostly
   required server on this list:


    * `clone` should be to the hostname of the server where the `clone`
       system is installed.


3. You may decide to install `push` to the `clone` system so that it may be
   installed later using `clone` or you may decide to install it directly to a
   host to start using now.


    * To deploy to the local host you can run this:

          ./push live

      That will deploy the project to the same system on which you are
      currently running. It will do the deployment with `ssh` and `sudo`.

    * To deploy to a host defined in `bin/servers.py` you can run this:

          ./push live:some-host

      That will deploy the project to the system defined in your server
      configuration list. It will do the deplyment with `ssh` and `sudo`.

    * To deploy to an abritrary host you can use Fabric options:

          ./push -H random-host live

    * To deploy to the `clone` system you can run this:

          ./push clone

      That will deploy the project to the defined `clone` host using `ssh` and
      `sudo`.


### Using

To use `push` to deploy your project, you need to create a file called
`.pushrc` in the root directory of your project. Decide what type of deployment
you need to have. Only one type of deployment is included by default but there
are examples of other deployment types in the `/contrib` directory.


* **copy**

  This type of deployment is for just copying a project's files to the remote
  location. The default only copies five directories: `bin`, `lib`, `etc`,
  `www`, and `web`. Examples of how to copy others are detailed below.

  Here is an example `.pushrc` using the `copy` deployment type that will put
  your project into the `push/common` directory on your `clone` system:


      #!/usr/bin/env python2.7
      from pushlib.copy import *
      from fabric.api import env
      env.clone_path = "push/common"


  You can make it copy more than just `bin`, `lib`, `etc`, `www`, and `web`. To
  make it also copy the `foobar` directory, for example:


      #!/usr/bin/env python2.7
      from pushlib.copy import *
      from fabric.api import env, execute
      env.clone_path = "push/common"


      class CustomBuildTask(CopyBuildTask):
          __doc__ = pushlib.BuildTask.__doc__

          def run(self):
              super(CustomBuildTask, self).run()

              for path in ['bin', 'lib', 'etc', 'web', 'www', 'foobar']:
                  execute(CopyDirectoryTask(), path)


      buildTask = CustomBuildTask()


  To override where files go -- for example, to have files in the project's bin
  directory deploy to foobar/bin -- you can use this example:


      execute(CopyDirectoryTask(), 'bin', 'foobar/bin')


You can combine multiple deployment types using multiple inheritance. For
example, if you have a deployment type for Perl projects and you want to run
JSLint against your project, too, you might write a `.pushrc` file like this:


    #!/usr/bin/env python2.7
    from pushlib.perl import *
    from pushlib.jslint import *
    from fabric.api import env
    env.clone_path = "push/common"

    class CustomCleanTask(PerlCleanTask, JSLintCleanTask):
        __doc__ = pushlib.CleanTask.__doc__


    class CustomMostlyCleanTask(PerlMostlyCleanTask, JSLintMostlyCleanTask):
        __doc__ = pushlib.MostlyCleanTask.__doc__


    class CustomBuildTask(PerlBuildTask, JSLintBuildTask):
        __doc__ = pushlib.BuildTask.__doc__


    class CustomTestTask(PerlTestTask, JSLintTestTask):
        __doc__ = pushlib.TestTask.__doc__


    class CustomArchiveTask(PerlArchiveTask, JSLintArchiveTask):
        __doc__ = pushlib.ArchiveTask.__doc__


    class CustomLiveTask(PerlLiveTask, JSLintLiveTask):
        __doc__ = pushlib.LiveTask.__doc__


    class CustomCloneTask(PerlCloneTask, JSLintCloneTask):
        __doc__ = pushlib.CloneTask.__doc__


    class CustomDeployTask(PerlDeployTask, JSLintDeployTask):
        __doc__ = pushlib.DeployTask.__doc__


    cleanTask       = CustomCleanTask()
    mostlyCleanTask = CustomMostlyCleanTask()
    buildTask       = CustomBuildTask()
    testTask        = CustomTestTask()
    archiveTask     = CustomArchiveTask()
    liveTask        = CustomLiveTask()
    cloneTask       = CustomCloneTask()
    deployTask      = CustomDeployTask()


It may seem like a waste of time to write all those empty classes. However, you
will not always know which tasks are implemented by the modules you are using.
To ensure maximum compatibiity, it is safest to write empty classes for all
tasks.

`push` is just a series of Fabric scripts. After configuring your project's
`.pushrc` file you can see what tasks you may run using `push -l`:


    $ push -l
    Available commands:

        archive      creates an archive for deployment
        build        builds a copy of the project for testing and deployment
        clean        removes all built content
        clone        deploys the project to clone
        deploy       given a username, the path to an archive file, and the path on the remote host, untar the file on the remote hosts as the given user
        live         deploy the project locally or use "live:nickname" to deploy to a particular server
        mostlyclean  remove all build artifacts except test output
        test         run tests


You can add more tasks in your project's `.pushrc` file like this:


    from fabric.api import env, task, local

    @task
    def foo():
        local("ls {}".format(env.release_dir))


You can also implement a subclassed version of one of the existing targets to
override its functionality. Going the subclassed route is probably best because
it ensures the enforcement of prerequisites for each target.

An important note is that by default `push` only adds new files. `push` does
not remove files from remote hosts that have been removed from your project.
You must remove those from the remote host yourself.

The following are the default tasks available by default when using `push`.
Each task is implemented by Python class and can be overridden to add or
remove functionality. Each of the above described modules does just that and
implements its own class that can also be overridden in the same way.

* **clean**

Cleans up all build artifacts.

* **mostlyclean**

Cleans up all build artifacts **except** test output.

* **build**

Builds the project but does not run tests.

* **test**

After building the project this will run all tests.

* **archive**

After building and testing the project this creates a deployment archive of the
project. The deployment archive is exactly what will get sent to the host.

* **live**

Installs the project on the local host. It does this over `ssh`. All files are
installed using `sudo` to the configured user. The archived file is placed
under `/tmp` before deployment and then removed after deployment.

* **live:nickname**

Installs the project on a remote host where the nickname is the host alias
defined in the `servers.py` file. It does this over `ssh`. All files are
installed using `sudo` on the remote host to the configured user. The archived
file is placed under `/tmp` before deployment and then removed after
deployment.

* **deploy:username,archive,path**

Takes an archive and untars it into the given path as the given user on the
hostnames in the given list. This task is usually called by the *live* task but
this is the task that should be overridden when one wants to run something on
each host when deploying. The hostname can be found in `env.host_string`.

* **clone**

Installs the project into the defined `clone_path` directory on the `clone`
host. It does this over `ssh`. All files are installed using `sudo` on the
defined `clone` host to the configured user. The archived file is placed under
`/tmp` before deployment and then removed after deployment.


### Controlling `push`

There are several flags that can be used to control the operation of push.
These flags can all be passed to push like this:

    push --set=no_tag=1 ...

The values "True" or "1" will enable setting and anything else will disable the
setting.

The other way to set this flags is permanently in the project's `.pushrc` file
like this:

    env.no_tag = True
    env.no_tag = 1


#### no_tag

Normally a project will be not be deployed to nocref if the version being deployed is not tagged. This will allow an untagged project to be deployed.


### Extending

This project is just a series of Python scripts with classes that extend Fabric
classes and that can be further extended very easily using more inheritance and
even multiple inheritance. In any extension to `push`, you can access the
following variables using Fabric's global `env` variable.

* `env.current_dir` This is the full path to the current directory from where
  `push` was called.
* `env.containment_dir` This is the root path where `push` does its work.
* `env.build_dir` The full path to the directory where the project is built.
* `env.test_dir` The full path to the directory where test output is sent.
* `env.archive_dir` The full path to the directory where where archives created
  by the archive task will be stored.
* `env.release_dir` The full path to the directory where the release will be
  created. Basically, anything that goes in here will be deployed when the
  project is deployed.
* `env.temp_dir` The full path to a temporary directory that may be used when
  `push` is doing its work.
* `env.git_root_dir` The full path to the root of the git repository in which
  the project is contained.
* `env.repo_commit_name`
* `env.repo_branch_hame`
* `env.repo_tag_name`
* `env.repo_is_dirty`
* `env.project_name` The name of the project derived from the name of the git
  directory.
* `env.archive_name` The name of the archive created when running the archive
  task.
* `env.tar_x_flags` Flags to pass to `tar` when extracting a tar archive.
* `env.tar_c_flags` Flags to pass to `tar` when creating a tar archive.
* `env.rsync_flags` Flags to pass to `rsync`.
* `env.servers` A dict containing all of the servers that are configured for
  deployment.
* `env.clone_base_dir` The root clone source directories.
* `env.clone_path` The clone source directory to use when deploying to `clone`.
* `env.host_path` The directory to deploy your project to on remote systems.
* `env.host_user` The user to `sudo` to when deploying to remote systems.
* `env.git` The path to the `git` program.
* `env.tar` The path to the `tar` program.
* `env.rsync` The path to the `rsync` program.


### Prerequisites

This software requires:

* Python 2.7
* Fabric
* rsync
* GNU tar
* git


### Credits and Copyright

This project is a derivation of a similar project created and used internally
by the University of Washington Information Technology Computing Infrastructure
division. The code seen here was created by Paul Lockaby.
