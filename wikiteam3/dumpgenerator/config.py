import json
import sys


def loadConfig(config={}, configfilename=""):
    """Load config file"""

    try:
        with open(
            "{}/{}".format(config["path"], configfilename), encoding="utf-8"
        ) as infile:
            config = json.load(infile)
    except:
        print("There is no config file. we can't resume. Start a new dump.")
        sys.exit()

    return config


def saveConfig(config={}, configfilename=""):
    """Save config file"""

    with open(
        "{}/{}".format(config["path"], configfilename), "w", encoding="utf-8"
    ) as outfile:
        json.dump(config, outfile)
