import datetime


def logerror(config={}, text=""):
    """Log error in file"""
    if text:
        with open("%s/errors.log" % (config["path"]), "a") as outfile:
            output = u"%s: %s\n" % (
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                text,
            )
            outfile.write(str(output))
