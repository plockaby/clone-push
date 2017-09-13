#!/usr/bin/env python2.7

import os
import pushlib
from fabric.tasks import Task
from fabric.api import env, local
from fabric.colors import yellow


class JSHintTask(Task):
    """
        run jshint against all non-minified, non-third-party JavaScript files
    """

    def run(self):
        # run python tests
        if (str(env.get("skip_tests", os.environ.get("SKIP_TESTS", False))) not in ["True", "1"]):
            jshint = "{}/third-party/jshint/jshint --verbose --extract=auto --config={}/third-party/jshint/jshint.conf".format(env.push_dir, env.push_dir)

            # want it such that we don't run jshint if we've already jshinted
            jshinted = "{}/.jshinted".format(env.test_dir)
            if (not os.path.exists(jshinted)):
                local("{} -m -t 200001010000 {}".format(env.tools['touch'], jshinted))

            # build a unique set of all files to jshint
            files = set()

            # find javascript files
            js_files = local("{} {} -newer {} -type f -name \"*.js\" -not -name \"*.min.js\" -not -path \"*/third-party/*\" -not -path \"*/.eggs/*\"".format(env.tools['find'], env.build_dir, jshinted), capture=True)
            if (js_files):
                for file in js_files.split("\n"):
                    files.add(file)

            # find other files that might have javascript in them
            # NOTE: jshint doesn't do very well with Kolon (Perl) and Jinja
            # (Python) templates right now. disabling until that gets better.
            #for extension in ["*.html"]:
            #    other_files = local("{} {} -newer {} -type f -name \"{}\" -not -path \"*/third-party/*\" -not -path \"*/.eggs/*\"".format(env.tools['find'], env.build_dir, jshinted, extension), capture=True)
            #    if (other_files):
            #        for file in other_files.split("\n"):
            #            files.add(file)

            for file in files:
                dot_nojshint = "{}/.nojshint".format(os.path.dirname(file))
                if (os.path.exists(dot_nojshint)):
                    print(yellow("Found .nojshint -- ignoring {}.".format(file)))
                else:
                    local("{} {}".format(jshint, file))

            local("{} {}".format(env.tools['touch'], jshinted))
        else:
            print(yellow("Not running tests because 'skip_tests' is set."))
