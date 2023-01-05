try:
    import contextlib
    import http.cookiejar
    import os
    import re
    import sys
    import traceback

    from file_read_backwards import FileReadBackwards


except ImportError:
    print(
        """
        Please install poetry with:
            $ pip install poetry.
        Then rerun py with:
            $ poetry run python py
    """
    )
    sys.exit(1)

from .cli import getParameters
from .config import loadConfig, saveConfig
from .domain import domain2prefix
from .greeter import bye, welcome
from .image import Image
from .index_php import saveIndexPHP
from .logs import saveLogs
from .page_special_version import saveSpecialVersion
from .page_titles import getPageTitles, readTitles
from .site_info import saveSiteInfo
from .truncate import truncateFilename
from .util import undoHTMLEntities
from .wiki_avoid import avoidWikimediaProjects
from .xml_dump import generateXMLDump
from .xml_integrity import checkXMLIntegrity

# From https://stackoverflow.com/a/57008707
class Tee(object):
    def __init__(self, filename):
        self.file = open(filename, 'w')
        self.stdout = sys.stdout

    def __enter__(self):
        sys.stdout = self

    def __exit__(self, exc_type, exc_value, tb):
        sys.stdout = self.stdout
        if exc_type is not None:
            self.file.write(traceback.format_exc())
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()
        self.stdout.flush()

class DumpGenerator:
    def __init__(params=[]):
        """Main function"""
        configfilename = "config.json"
        config, other = getParameters(params=params)
        avoidWikimediaProjects(config=config, other=other)

        with (Tee(other["log_path"]) if other["log_path"] is not None else contextlib.nullcontext()):
            print(welcome())
            print("Analysing %s" % (config["api"] and config["api"] or config["index"]))

            # creating path or resuming if desired
            c = 2
            # to avoid concat blabla-2, blabla-2-3, and so on...
            originalpath = config["path"]
            # do not enter if resume is requested from begining
            while not other["resume"] and os.path.isdir(config["path"]):
                print('\nWarning!: "%s" path exists' % (config["path"]))
                reply = ""
                if config["failfast"]:
                    retry = "yes"
                while reply.lower() not in ["yes", "y", "no", "n"]:
                    reply = input(
                        'There is a dump in "%s", probably incomplete.\nIf you choose resume, to avoid conflicts, the parameters you have chosen in the current session will be ignored\nand the parameters available in "%s/%s" will be loaded.\nDo you want to resume ([yes, y], [no, n])? '
                        % (config["path"], config["path"], configfilename)
                    )
                if reply.lower() in ["yes", "y"]:
                    if not os.path.isfile("{}/{}".format(config["path"], configfilename)):
                        print("No config file found. I can't resume. Aborting.")
                        sys.exit()
                    print("You have selected: YES")
                    other["resume"] = True
                    break
                elif reply.lower() in ["no", "n"]:
                    print("You have selected: NO")
                    other["resume"] = False
                config["path"] = "%s-%d" % (originalpath, c)
                print('Trying to use path "%s"...' % (config["path"]))
                c += 1

            if other["resume"]:
                print("Loading config file...")
                config = loadConfig(config=config, configfilename=configfilename)
            else:
                os.mkdir(config["path"])
                saveConfig(config=config, configfilename=configfilename)

            if other["resume"]:
                DumpGenerator.resumePreviousDump(config=config, other=other)
            else:
                DumpGenerator.createNewDump(config=config, other=other)

            saveIndexPHP(config=config, session=other["session"])
            saveSpecialVersion(config=config, session=other["session"])
            saveSiteInfo(config=config, session=other["session"])
            bye()

    def createNewDump(config={}, other={}):
        images = []
        print("Trying generating a new dump into a new directory...")
        if config["xml"]:
            getPageTitles(config=config, session=other["session"])
            titles = readTitles(config)
            generateXMLDump(config=config, titles=titles, session=other["session"])
            checkXMLIntegrity(config=config, titles=titles, session=other["session"])
        if config["images"]:
            images += Image.getImageNames(config=config, session=other["session"])
            Image.saveImageNames(config=config, images=images, session=other["session"])
            Image.generateImageDump(
                config=config, other=other, images=images, session=other["session"]
            )
        if config["logs"]:
            saveLogs(config=config, session=other["session"])

    def resumePreviousDump(config={}, other={}):
        images = []
        print("Resuming previous dump process...")
        if config["xml"]:
            titles = readTitles(config)
            try:
                with FileReadBackwards(
                    "%s/%s-%s-titles.txt"
                    % (
                        config["path"],
                        domain2prefix(config=config, session=other["session"]),
                        config["date"],
                    ),
                    encoding="utf-8",
                ) as frb:
                    lasttitle = frb.readline().strip()
                    if lasttitle == "":
                        lasttitle = frb.readline().strip()
            except:
                lasttitle = ""  # probably file does not exists
            if lasttitle == "--END--":
                # titles list is complete
                print("Title list was completed in the previous session")
            else:
                print("Title list is incomplete. Reloading...")
                # do not resume, reload, to avoid inconsistences, deleted pages or
                # so
                getPageTitles(config=config, session=other["session"])

            # checking xml dump
            xmliscomplete = False
            lastxmltitle = None
            try:
                with FileReadBackwards(
                    "%s/%s-%s-%s.xml"
                    % (
                        config["path"],
                        domain2prefix(config=config, session=other["session"]),
                        config["date"],
                        config["curonly"] and "current" or "history",
                    ),
                    encoding="utf-8",
                ) as frb:
                    for l in frb:
                        if l.strip() == "</mediawiki>":
                            # xml dump is complete
                            xmliscomplete = True
                            break

                        xmltitle = re.search(r"<title>([^<]+)</title>", l)
                        if xmltitle:
                            lastxmltitle = undoHTMLEntities(text=xmltitle.group(1))
                            break
            except:
                pass  # probably file does not exists

            if xmliscomplete:
                print("XML dump was completed in the previous session")
            elif lastxmltitle:
                # resuming...
                print('Resuming XML dump from "%s"' % (lastxmltitle))
                titles = readTitles(config, start=lastxmltitle)
                generateXMLDump(
                    config=config,
                    titles=titles,
                    start=lastxmltitle,
                    session=other["session"],
                )
            else:
                # corrupt? only has XML header?
                print("XML is corrupt? Regenerating...")
                titles = readTitles(config)
                generateXMLDump(config=config, titles=titles, session=other["session"])

        if config["images"]:
            # load images
            lastimage = ""
            try:
                f = open(
                    "%s/%s-%s-images.txt"
                    % (config["path"], domain2prefix(config=config), config["date"]),
                    encoding="utf-8",
                )
                lines = f.readlines()
                for l in lines:
                    if re.search(r"\t", l):
                        images.append(l.split("\t"))
                lastimage = lines[-1].strip()
                if lastimage == "":
                    lastimage = lines[-2].strip()
                f.close()
            except FileNotFoundError:
                pass  # probably file does not exists
            if lastimage == "--END--":
                print("Image list was completed in the previous session")
            else:
                print("Image list is incomplete. Reloading...")
                # do not resume, reload, to avoid inconsistences, deleted images or
                # so
                images = Image.getImageNames(config=config, session=other["session"])
                Image.saveImageNames(config=config, images=images)
            # checking images directory
            listdir = []
            try:
                listdir = os.listdir("%s/images" % (config["path"]))
            except OSError:
                pass  # probably directory does not exist
            listdir.sort()
            complete = True
            lastfilename = ""
            lastfilename2 = ""
            c = 0
            for filename, url, uploader in images:
                lastfilename2 = lastfilename
                # return always the complete filename, not the truncated
                lastfilename = filename
                filename2 = filename
                if len(filename2) > other["filenamelimit"]:
                    filename2 = truncateFilename(other=other, filename=filename2)
                if filename2 not in listdir:
                    complete = False
                    break
                c += 1
            print("%d images were found in the directory from a previous session" % (c))
            if complete:
                # image dump is complete
                print("Image dump was completed in the previous session")
            else:
                # we resume from previous image, which may be corrupted (or missing
                # .desc)  by the previous session ctrl-c or abort
                Image.generateImageDump(
                    config=config,
                    other=other,
                    images=images,
                    start=lastfilename2,
                    session=other["session"],
                )

        if config["logs"]:
            # fix
            pass
