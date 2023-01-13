import datetime

from wikiteam3.dumpgenerator.config import Config

def logerror(config: Config=None,to_stdout=False , text="") -> None:
    """Log error in errors.log"""
    if text:
        with open("%s/errors.log" % (config.path), "a", encoding="utf-8") as outfile:
            output = "{}: {}\n".format(
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                text,
            )
            outfile.write(output)
    if to_stdout:
        print(text)
