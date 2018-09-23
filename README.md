# push

### About

This is a tool to build, test, and deploy your projects to either another
server or to a [clone](https://github.com/plockaby/clone) system for deployment
by `clone`.


### Installing

The installation for `push` is not the most standard. Configuration files must
be written before it can be deployed. So follow these steps to get those
created.


1. Edit `pushlib/loader.py`. There are a few specific configuration value that
MUST be set. These can all be overridden in a project's `.pushrc` file.


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


2. Maybe modify `pushlib/hosts.py`. This is where hosts are defined by either
   name or tag. Right now the host is list loaded from a tool called
   [dart](https://github.com/plockaby/dart) but you can get the list of hosts
   from wherever you want.


3. You may decide to install `push` to the `clone` system so that it may be
   installed later using `clone` or you may decide to install it directly to a
   host to start using now.


    * To deploy to the local host you can run this:

          ./push live localhost

      That will deploy the project to the same system on which you are
      currently running. It will do the deployment with `ssh` and `sudo`.

    * To deploy to a host defined in `bin/servers.py` you can run this:

          ./push live some-host

      That will deploy the project to the system defined in your server
      configuration list. It will do the deplyment with `ssh` and `sudo`.

    * To deploy to an abritrary host you can use that host name and confirm
      that you're ok with deploying to that host.

          ./push live random-host

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


      # vi:syntax=python
      from pushlib.modules.perl import *
      env.clone_path = "push/common"


  You can make it copy more than just `bin`, `lib`, `etc`, `www`, and `web`. To
  make it also copy the `foobar` directory, for example:


      # vi:syntax=python
      from pushlib.modules.perl import *
      from pushlib.tools import copy
      env.clone_path = "push/common"


      class BuildTask(BuildTask):
          def before(self, c):
              super().before(c)

              for path in ["foobar"]:
                  copy("foobar")


  To override where files go -- for example, to have files in the project's bin
  directory deploy to foobar/bin -- you can use this example:


      copy("bin", "foobar/bin")


If the multiple deployment types implement other tasks such as `Clean` or
`Archive` then you will have to write those into your script as well.

`push` is just a series of Fabric scripts. After configuring your project's
`.pushrc` file you can see what tasks you may run using `push -l`:


    $ push -l
    Subcommands:

      archive       create deployment archive
      build         build the project
      clean         remove all build artifacts
      clone         deploy the project to clone
      live          deploy the project using "live nickname" to deploy to a particular host
      mostlyclean   remove most build artifacts
      register      registers the task with dart if a .dartrc file is present
      test          run project tests


You can implement a subclassed version of one of these tasks to override its
functionality. Going the subclassed route is probably best because it ensures
the enforcement of prerequisites for each target.

An important note is that by default `push` only adds new files. `push` does
not remove files from remote hosts that have been removed from your project.
You must remove those from the remote host yourself.

The following are the default tasks available by default when using `push`.
Each task is implemented by Python class and can be overridden to add or
remove functionality. Each of the above described modules does just that and
implements its own class that can also be overridden in the same way.

* **clean**

Cleans up all build artifacts.

* **build**

Builds the project but does not run tests.

* **test**

After building the project this will run all tests.

* **archive**

After building and testing the project this creates a deployment archive of the
project. The deployment archive is exactly what will get sent to the host.

* **live nickname**

Installs the project on a remote host where the nickname is the host alias
defined in the `hosts.py` file. It does this over `ssh`. All files are
installed using `sudo` on the remote host to the configured user.

* **clone**

Installs the project into the defined `clone_path` directory on the `clone`
host. It does this over `ssh`. All files are installed using `sudo` on the
defined `clone` host to the configured user.


### Controlling `push`

There are several flags that can be used to control the operation of push.
These flags can all be passed to push like this:

    NO_TAG=1 push ...

The values "True" or "1" will enable setting and anything else will disable the
setting. The other way to set this flags is permanently in the project's
`.pushrc` file like this:

    env.no_tag = True
    env.no_tag = 1


#### no_tag

Normally a project will be not be deployed to the clone host if the version
being deployed is not tagged. This will allow an untagged project to be
deployed.


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
* `env.clone_base_dir` The root clone source directories.
* `env.clone_path` The clone source directory to use when deploying to `clone`.
* `env.host_path` The directory to deploy your project to on remote systems.
* `env.host_user` The user to `sudo` to when deploying to remote systems.


### Prerequisites

This software requires:

* Python 3
* Invoke
* rsync
* git

It also requires standard system utilities in your path like `ssh` and `sudo`.


### Credits and Copyright

This project is a derivation of a similar project created and used internally
by the University of Washington Information Technology IT Infrastructure
division. The code seen here was created by Paul Lockaby.
