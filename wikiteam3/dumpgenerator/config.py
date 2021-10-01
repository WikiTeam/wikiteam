import json
import sys


def loadConfig(config={}, configfilename=""):
    """Load config file"""

    try:
        with open("%s/%s" % (config["path"], configfilename), "r") as infile:
            config = json.load(infile)
    except:
        print("There is no config file. we can't resume. Start a new dump.")
        sys.exit()

    return config


def saveConfig(config={}, configfilename=""):
    """Save config file"""

    with open("%s/%s" % (config["path"], configfilename), "w") as outfile:
        json.dump(config, outfile)
