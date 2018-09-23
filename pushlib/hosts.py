from invoke import run
from .tools import warn
import json


hosts = {
    # a dict, keyed by tag, value is an array of hostnames
    "tags": {},

    # a dict, keyed by hostname, value is an array of nocref targets
    "servers": {},
}

try:
    result = run("dart-config hosts", warn=True, hide=True)
    data = json.loads(result.stdout)
    for hostname in data:
        # add tags and hostnames
        if ("tags" in data[hostname]):
            for tag in data[hostname]["tags"]:
                if (tag not in hosts["tags"]):
                    hosts["tags"][tag] = []
                hosts["tags"][tag].append(hostname)

        # add hostname and nocref targets
        hosts["servers"][hostname] = data[hostname].get("targets")
except Exception as e:
    warn("Could not decode dart host list: {}".format(e))
