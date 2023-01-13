from typing import *
from wikiteam3.dumpgenerator.config import Config

def checkXMLIntegrity(config: Config=None, titles: Iterable[str]=None, session=None):
    """Check XML dump integrity, to detect broken XML chunks"""
    return

    print("Verifying dump...")
    checktitles = 0
    checkpageopen = 0
    checkpageclose = 0
    checkrevisionopen = 0
    checkrevisionclose = 0
    for line in (
        file(
            "%s/%s-%s-%s.xml"
            % (
                config.path,
                domain2prefix(config=config, session=session),
                config.date,
                config.curonly and "current" or "history",
            ),
            "r",
        )
        .read()
        .splitlines()
    ):
        if "<revision>" in line:
            checkrevisionopen += 1
        elif "</revision>" in line:
            checkrevisionclose += 1
        elif "<page>" in line:
            checkpageopen += 1
        elif "</page>" in line:
            checkpageclose += 1
        elif "<title>" in line:
            checktitles += 1
        else:
            continue
    if (
        checktitles == checkpageopen
        and checktitles == checkpageclose
        and checkrevisionopen == checkrevisionclose
    ):
        pass
    else:
        print("XML dump seems to be corrupted.")
        reply = ""
        if config.failfast:
            reply = "yes"
        while reply.lower() not in ["yes", "y", "no", "n"]:
            reply = raw_input("Regenerate a new dump ([yes, y], [no, n])? ")
        if reply.lower() in ["yes", "y"]:
            generateXMLDump(config=config, titles=titles, session=session)
        elif reply.lower() in ["no", "n"]:
            print("Not generating a new dump.")
