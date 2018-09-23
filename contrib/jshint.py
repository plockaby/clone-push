from invoke import run
from .. import colors
from .. import env
import os


class JSHintTask(object):
    def __init__(self):
        jshint = "{}/shared/jshint/jshint --verbose --extract=auto --config={}/shared/jshint/jshint.conf".format(env.push_dir, env.push_dir)

        # want to ignore files that haven't changed since the last time that
        # jshint ran. though, this is useless when a "clean" has happened.
        jshinted = "{}/.jshinted".format(env.test_dir)
        if (not os.path.exists(jshinted)):
            run("touch -m -t 200001010000 {}".format(jshinted))

        # build a list of files to check
        files = set()

        # add non-minified, non-third-party JavaScript
        js_files = run("find {} -newer {} -type f -name \"*.js\" -not -name \"*.min.js\" -not -path \"*/third-party/*\" -not -path \"*/.eggs/*\"".format(env.build_dir, jshinted), hide=True).stdout.strip()
        if (js_files):
            for file in js_files.split("\n"):
                files.add(file)

        # add html files plus any other extensions
        # NOTE: jshint doesn't work very well with Kolon (Perl) and Jinja
        # (Python) templates so we are temporarily disabling thins.
        # for extension in ["*.html"]:
        #     other_files = run("find {} -newer {} -type f -name \"{}\" -not -path \"*/third-party/*\" -not -path \"*/.eggs/*\"".format(env.build_dir, jshinted, extension), hide=True).stdout.strip()
        #     if (other_files):
        #         for file in other_files.split("\n"):
        #             files.add(file)

        # now process the unique set of files
        for f in files:
            dot_nojshint = "{}/.nojshint".format(os.path.dirname(f))
            if (os.path.exists(dot_nojshint)):
                print(colors.yellow("Found .nojshint -- ignoring {}.".format(f)))
            else:
                run("{} {}".format(jshint, f))

        run("touch {}".format(jshinted))
