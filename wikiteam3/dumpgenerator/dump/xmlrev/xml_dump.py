import re
import sys
from typing import *

from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.utils import domain2prefix
from wikiteam3.dumpgenerator.exceptions import PageMissingError
from wikiteam3.dumpgenerator.log import logerror
from wikiteam3.dumpgenerator.dump.page.page_titles import readTitles
from wikiteam3.dumpgenerator.dump.page.page_xml import getXMLPage
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.utils import cleanXML, undoHTMLEntities
from .xml_header import getXMLHeader
from .xml_revisions import getXMLRevisions
from .xml_truncate import truncateXMLDump

def generateXMLDump(config: Config=None, titles: Iterable[str]=None, start=None, session=None):
    """Generates a XML dump for a list of titles or from revision IDs"""
    # TODO: titles is now unused.

    header, config = getXMLHeader(config=config, session=session)
    footer = "</mediawiki>\n"  # new line at the end
    xmlfilename = "{}-{}-{}.xml".format(
        domain2prefix(config=config),
        config.date,
        "current" if config.curonly else "history",
    )
    xmlfile = ""
    lock = True

    # start != None, means we are resuming a XML dump
    if start:
        print(
            "Removing the last chunk of past XML dump: it is probably incomplete."
        )
        # truncate XML dump if it already exists
        truncateXMLDump("{}/{}".format(config.path, xmlfilename))

    if config.xmlrevisions:
        if start:
            print(f"WARNING: will try to start the download from title: {start}")
            xmlfile = open(
                "{}/{}".format(config.path, xmlfilename), "a", encoding="utf-8"
            )
        else:
            print("\nRetrieving the XML for every page from the beginning\n")
            xmlfile = open(
                "{}/{}".format(config.path, xmlfilename), "w", encoding="utf-8"
            )
            xmlfile.write(header)
        try:
            r_timestamp = "<timestamp>([^<]+)</timestamp>"
            for xml in getXMLRevisions(config=config, session=session, start=start):
                numrevs = len(re.findall(r_timestamp, xml))
                # Due to how generators work, it's expected this may be less
                xml = cleanXML(xml=xml)
                xmlfile.write(xml)

                xmltitle = re.search(r"<title>([^<]+)</title>", xml)
                title = undoHTMLEntities(text=xmltitle.group(1))
                print(f'{title}, {numrevs} edits (--xmlrevisions)')
                Delay(config=config, session=session)
        except AttributeError as e:
            print(e)
            print("This API library version is not working")
            sys.exit()
        except UnicodeEncodeError as e:
            print(e)

    else:  # --xml
        print(
            '\nRetrieving the XML for every page from "%s"\n'
            % (start if start else "start")
        )

        if not start:
            # requested complete xml dump
            lock = False
            xmlfile = open(
                "{}/{}".format(config.path, xmlfilename), "w", encoding="utf-8"
            )
            xmlfile.write(header)
            xmlfile.close()

        xmlfile = open(
            "{}/{}".format(config.path, xmlfilename), "a", encoding="utf-8"
        )
        c = 1
        for title in readTitles(config, start):
            if not title:
                continue
            if title == start:  # start downloading from start, included
                lock = False
            if lock:
                continue
            Delay(config=config, session=session)
            if c % 10 == 0:
                print(f"\n->  Downloaded {c} pages\n")
            try:
                for xml in getXMLPage(config=config, title=title, session=session):
                    xml = cleanXML(xml=xml)
                    xmlfile.write(xml)
            except PageMissingError:
                logerror(
                    config=config, to_stdout=True,
                    text='The page "%s" was missing in the wiki (probably deleted)'
                    % title,
                )
            # here, XML is a correct <page> </page> chunk or
            # an empty string due to a deleted page (logged in errors log) or
            # an empty string due to an error while retrieving the page from server
            # (logged in errors log)
            c += 1

    xmlfile.write(footer)
    xmlfile.close()
    print("XML dump saved at...", xmlfilename)
