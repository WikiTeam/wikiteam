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

from typing import *

from wikiteam3.dumpgenerator.cli import bye, getParameters, welcome
from wikiteam3.dumpgenerator.config import Config, loadConfig, saveConfig
from wikiteam3.dumpgenerator.dump.image.image import Image
from wikiteam3.dumpgenerator.dump.misc.index_php import saveIndexPHP
from wikiteam3.dumpgenerator.dump.misc.site_info import saveSiteInfo
from wikiteam3.dumpgenerator.dump.misc.special_logs import saveLogs
from wikiteam3.dumpgenerator.dump.misc.special_version import saveSpecialVersion
from wikiteam3.dumpgenerator.dump.xmldump.xml_dump import generateXMLDump
from wikiteam3.dumpgenerator.dump.xmldump.xml_integrity import checkXMLIntegrity
from wikiteam3.dumpgenerator.log import logerror
from wikiteam3.utils import avoidWikimediaProjects, domain2prefix, undoHTMLEntities


# From https://stackoverflow.com/a/57008707
class Tee:
    def __init__(self, filename):
        self.file = open(filename, "w", encoding="utf-8")
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
    configfilename = "config.json"

    @staticmethod
    def __init__(params=None):
        """Main function"""
        configfilename = DumpGenerator.configfilename
        config, other = getParameters(params=params)
        avoidWikimediaProjects(config=config, other=other)

        with (
            Tee(other["stdout_log_path"])
            if other["stdout_log_path"] is not None
            else contextlib.nullcontext()
        ):
            print(welcome())
            print(f"Analysing {config.api if config.api else config.index}")

            # creating path or resuming if desired
            c = 2
            # to avoid concat blabla-2, blabla-2-3, and so on...
            originalpath = config.path
            # do not enter if resume is requested from begining
            while not other["resume"] and os.path.isdir(config.path):
                print('\nWarning!: "%s" path exists' % (config.path))
                reply = ""
                if config.failfast:
                    reply = "yes"
                while reply.lower() not in ["yes", "y", "no", "n"]:
                    reply = input(
                        'There is a dump in "%s", probably incomplete.\nIf you choose resume, to avoid conflicts, the parameters you have chosen in the current session will be ignored\nand the parameters available in "%s/%s" will be loaded.\nDo you want to resume ([yes, y], [no, n])? '
                        % (config.path, config.path, configfilename)
                    )
                if reply.lower() in ["yes", "y"]:
                    if not os.path.isfile(f"{config.path}/{configfilename}"):
                        print("No config file found. I can't resume. Aborting.")
                        sys.exit()
                    print("You have selected: YES")
                    other["resume"] = True
                    break
                elif reply.lower() in ["no", "n"]:
                    print("You have selected: NO")
                    other["resume"] = False
                config.path = "%s-%d" % (originalpath, c)
                print(f'Trying to use path "{config.path}"...')
                c += 1

            if other["resume"]:
                print("Loading config file...")
                config = loadConfig(config=config, configfilename=configfilename)
            else:
                os.mkdir(config.path)
                saveConfig(config=config, configfilename=configfilename)

            if other["resume"]:
                DumpGenerator.resumePreviousDump(config=config, other=other)
            else:
                DumpGenerator.createNewDump(config=config, other=other)

            saveIndexPHP(config=config, session=other["session"])
            saveSpecialVersion(config=config, session=other["session"])
            saveSiteInfo(config=config, session=other["session"])
            bye()

    @staticmethod
    def createNewDump(config: Config = None, other: Dict = None):
        # we do lazy title dumping here :)
        images = []
        print("Trying generating a new dump into a new directory...")
        if config.xml:
            generateXMLDump(config=config, session=other["session"])
            checkXMLIntegrity(config=config, session=other["session"])
        if config.images:
            images += Image.getImageNames(config=config, session=other["session"])
            Image.saveImageNames(config=config, images=images, session=other["session"])
            Image.generateImageDump(
                config=config, other=other, images=images, session=other["session"]
            )
        if config.logs:
            saveLogs(config=config, session=other["session"])

    @staticmethod
    def resumePreviousDump(config: Config = None, other: Dict = None):
        images = []
        print("Resuming previous dump process...")
        if config.xml:
            # checking xml dump
            xmliscomplete = False
            lastxmltitle = None
            lastxmlrevid = None
            try:
                with FileReadBackwards(
                    "%s/%s-%s-%s.xml"
                    % (
                        config.path,
                        domain2prefix(config=config, session=other["session"]),
                        config.date,
                        "current" if config.curonly else "history",
                    ),
                    encoding="utf-8",
                ) as frb:
                    for l in frb:
                        if l.strip() == "</mediawiki>":
                            # xml dump is complete
                            xmliscomplete = True
                            break

                        if xmlrevid := re.search(r"    <id>([^<]+)</id>", l):
                            lastxmlrevid = int(xmlrevid.group(1))
                        if xmltitle := re.search(r"<title>([^<]+)</title>", l):
                            lastxmltitle = undoHTMLEntities(text=xmltitle.group(1))
                            break

            except:
                pass  # probably file does not exists

            if xmliscomplete:
                print("XML dump was completed in the previous session")
            elif lastxmltitle:
                # resuming...
                print(
                    f'Resuming XML dump from "{lastxmltitle}" (revision id {lastxmlrevid})'
                )
                generateXMLDump(
                    config=config,
                    session=other["session"],
                    resume=True,
                )
            else:
                # corrupt? only has XML header?
                print("XML is corrupt? Regenerating...")
                generateXMLDump(config=config, session=other["session"])

        if config.images:
            # load images list
            lastimage = ""
            imagesFilePath = "{}/{}-{}-images.txt".format(
                config.path,
                domain2prefix(config=config),
                config.date,
            )
            if os.path.exists(imagesFilePath):
                with open(imagesFilePath) as f:
                    lines = f.read().splitlines()
                    images.extend(l.split("\t") for l in lines if re.search(r"\t", l))
                    if len(lines) == 0:  # empty file
                        lastimage = "--EMPTY--"
                    if not lastimage:
                        lastimage = lines[-1].strip()
                    if lastimage == "":
                        lastimage = lines[-2].strip()
            if images and len(images[0]) < 5:
                print(
                    "Warning: Detected old images list (images.txt) format.\n"
                    + "You can delete 'images.txt' manually and restart the script."
                )
                sys.exit(1)
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
                listdir = os.listdir(f"{config.path}/images")
            except OSError:
                pass  # probably directory does not exist
            listdir = set(listdir)
            c_desc = 0
            c_images = 0
            c_checked = 0
            for filename, url, uploader, size, sha1 in images:
                lastfilename = filename
                if other["filenamelimit"] < len(filename.encode("utf-8")):
                    logerror(
                        config=config,
                        to_stdout=True,
                        text=f"Filename too long(>240 bytes), skipping: {filename}",
                    )
                    continue
                if filename in listdir:
                    c_images += 1
                if f"{filename}.desc" in listdir:
                    c_desc += 1
                c_checked += 1
                if c_checked % 100000 == 0:
                    print(f"checked {c_checked}/{len(images)} records", end="\r")
            print(
                f"{len(images)} records in images.txt, {c_images} images and {c_desc} .desc were saved in the previous session"
            )
            if c_desc < len(images):
                complete = False
            elif c_images < len(images):
                complete = False
                print(
                    "WARNING: Some images were not saved. You may want to delete their \n"
                    + ".desc files and re-run the script to redownload the missing images.\n"
                    + "(If images URL are unavailable, you can ignore this warning.)\n"
                    + "(In most cases, if the number of .desc files equals the number of \n"
                    + "images.txt records, you can ignore this warning, images dump was completed.)"
                )
                sys.exit()
            else:  # c_desc == c_images == len(images)
                complete = True
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
                    session=other["session"],
                )
