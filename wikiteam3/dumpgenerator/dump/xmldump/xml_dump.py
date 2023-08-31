import re
import sys
from io import TextIOWrapper

import lxml.etree
import requests

# from typing import *
from lxml.etree import _ElementTree as ElementTree

from wikiteam3.dumpgenerator.api.page_titles import readTitles
from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.dumpgenerator.dump.page.xmlexport.page_xml import getXMLPage
from wikiteam3.dumpgenerator.dump.page.xmlrev.xml_revisions import getXMLRevisions
from wikiteam3.dumpgenerator.dump.xmldump.xml_header import getXMLHeader
from wikiteam3.dumpgenerator.dump.xmldump.xml_truncate import (
    parseLastPageChunk,
    truncateXMLDump,
)
from wikiteam3.dumpgenerator.exceptions import PageMissingError
from wikiteam3.dumpgenerator.log import logerror
from wikiteam3.utils import cleanXML, domain2prefix, undoHTMLEntities


# lastPage=None,
# useAllrevisions=False,
def doXMLRevisionDump(
    config: Config,
    session: requests.Session,
    xmlfile: TextIOWrapper,
    lastPage: (ElementTree | None),
    useAllrevisions: bool,
):
    try:
        r_timestamp = "<timestamp>([^<]+)</timestamp>"
        r_arvcontinue = '<page arvcontinue="(.*?)">'

        lastArvcontinue = None
        for xml in getXMLRevisions(
            config=config,
            session=session,
            lastPage=lastPage,
            useAllrevision=useAllrevisions,
        ):
            numrevs = len(re.findall(r_timestamp, xml))
            if arvcontinueRe := re.findall(r_arvcontinue, xml):
                curArvcontinue = arvcontinueRe[0]
                if lastArvcontinue != curArvcontinue:
                    Delay(config=config)
                    lastArvcontinue = curArvcontinue
            # Due to how generators work, it's expected this may be less
            xml = cleanXML(xml=xml)
            xmlfile.write(xml)

            xmltitle = re.search(r"<title>([^<]+)</title>", xml)
            if xmltitle is not None:
                title = undoHTMLEntities(text=xmltitle[1])
                print(f"{title}, {numrevs} edits (--xmlrevisions)")
                # Delay(config=config)
    except AttributeError as e:
        print(e)
        print("This API library version is not working")
        sys.exit()
    except UnicodeEncodeError as e:
        print(e)


def doXMLExportDump(
    config: Config, session: requests.Session, xmlfile: TextIOWrapper, lastPage=None
):
    print("\nRetrieving the XML for every page\n")

    lock = True
    start: str = ""
    if lastPage is not None:
        try:
            start = lastPage.find("title").text
        except Exception:
            print(
                f"Failed to find title in last trunk XML: {lxml.etree.tostring(lastPage)}"
            )
            raise
    else:
        # requested complete xml dump
        lock = False

    c = 1
    for title in readTitles(config, session=session, start=start, batch=False):
        if title is not str or title == "":
            continue
        if title == start:  # start downloading from start, included
            lock = False
        if lock:
            continue
        Delay(config=config)
        if c % 10 == 0:
            print(f"\n->  Downloaded {c} pages\n")
        try:
            for xml in getXMLPage(
                config=config, verbose=True, title=title, session=session
            ):
                xml = cleanXML(xml=xml)
                xmlfile.write(xml)
        except PageMissingError:
            logerror(
                config=config,
                to_stdout=True,
                text=f'The page "{title}" was missing in the wiki (probably deleted)',
            )
        # here, XML is a correct <page> </page> chunk or
        # an empty string due to a deleted page (logged in errors log) or
        # an empty string due to an error while retrieving the page from server
        # (logged in errors log)
        c += 1


# resume=False
def generateXMLDump(config: Config, resume: bool, session: requests.Session):
    """Generates a XML dump for a list of titles or from revision IDs"""

    header, config = getXMLHeader(config=config, session=session)
    footer = "</mediawiki>\n"  # new line at the end
    xmlfilename = "{}-{}-{}.xml".format(
        domain2prefix(config=config),
        config.date,
        "current" if config.curonly else "history",
    )
    xmlfile: TextIOWrapper

    lastPage: (ElementTree | None) = None
    lastPageChunk = None
    # start != None, means we are resuming a XML dump
    if resume:
        print("Removing the last chunk of past XML dump: it is probably incomplete.")
        # truncate XML dump if it already exists
        lastPageChunk = truncateXMLDump(f"{config.path}/{xmlfilename}")
        if not lastPageChunk.strip():
            print("Last page chunk is NULL, we'll directly start a new dump!")
            resume = False
            lastPage = None
        else:
            try:
                lastPage = parseLastPageChunk(lastPageChunk)
            except lxml.etree.LxmlError:
                print("Failed to parse last page chunk: \n%s" % lastPageChunk)
                print("Cannot resume, exiting now!")
                sys.exit(1)

        print("WARNING: will try to start the download...")
        xmlfile = open(f"{config.path}/{xmlfilename}", "a", encoding="utf-8")
    else:
        print("\nRetrieving the XML for every page from the beginning\n")
        xmlfile = open(f"{config.path}/{xmlfilename}", "w", encoding="utf-8")
        xmlfile.write(header)

    if config.xmlrevisions and not config.xmlrevisions_page:
        doXMLRevisionDump(config, session, xmlfile, lastPage, useAllrevisions=True)
    elif config.xmlrevisions:
        doXMLRevisionDump(config, session, xmlfile, lastPage, useAllrevisions=False)
    else:  # --xml
        doXMLExportDump(config, session, xmlfile, lastPage)
    xmlfile.write(footer)
    xmlfile.close()
    print("XML dump saved at...", xmlfilename)
