import re
import sys

from .delay import delay
from .domain import domain2prefix
from .exceptions import PageMissingError
from .log_error import logerror
from .page_titles import readTitles
from .page_xml import getXMLPage
from .util import cleanXML
from .xml_header import getXMLHeader
from .xml_revisions import getXMLRevisions
from .xml_truncate import truncateXMLDump


def generateXMLDump(config={}, titles=[], start=None, session=None):
    """Generates a XML dump for a list of titles or from revision IDs"""
    # TODO: titles is now unused.

    header, config = getXMLHeader(config=config, session=session)
    footer = "</mediawiki>\n"  # new line at the end
    xmlfilename = "{}-{}-{}.xml".format(
        domain2prefix(config=config),
        config["date"],
        config["curonly"] and "current" or "history",
    )
    xmlfile = ""
    lock = True

    if config["xmlrevisions"]:
        if start:
            print(f"WARNING: will try to start the download from title: {start}")
            xmlfile = open(
                "{}/{}".format(config["path"], xmlfilename), "a", encoding="utf-8"
            )
        else:
            print("Retrieving the XML for every page from the beginning")
            xmlfile = open(
                "{}/{}".format(config["path"], xmlfilename), "w", encoding="utf-8"
            )
            xmlfile.write(str(header))
        try:
            r_timestamp = "<timestamp>([^<]+)</timestamp>"
            for xml in getXMLRevisions(config=config, session=session, start=start):
                numrevs = len(re.findall(r_timestamp, xml))
                # Due to how generators work, it's expected this may be less
                # TODO: get the page title and reuse the usual format "X title, y edits"
                print("        %d more revisions exported" % numrevs)
                xml = cleanXML(xml=xml)
                xmlfile.write(str(xml))
        except AttributeError as e:
            print(e)
            print("This API library version is not working")
            sys.exit()
        except UnicodeEncodeError as e:
            print(e)

    else:
        print(
            'Retrieving the XML for every page from "%s"' % (start and start or "start")
        )
        if start:
            print(
                "Removing the last chunk of past XML dump: it is probably incomplete."
            )
            truncateXMLDump("{}/{}".format(config["path"], xmlfilename))
        else:
            # requested complete xml dump
            lock = False
            xmlfile = open(
                "{}/{}".format(config["path"], xmlfilename), "w", encoding="utf-8"
            )
            xmlfile.write(str(header))
            xmlfile.close()

        xmlfile = open(
            "{}/{}".format(config["path"], xmlfilename), "a", encoding="utf-8"
        )
        c = 1
        for title in readTitles(config, start):
            if not title:
                continue
            if title == start:  # start downloading from start, included
                lock = False
            if lock:
                continue
            delay(config=config, session=session)
            if c % 10 == 0:
                print("Downloaded %d pages" % (c))
            try:
                for xml in getXMLPage(config=config, title=title, session=session):
                    xml = cleanXML(xml=xml)
                    xmlfile.write(str(xml))
            except PageMissingError:
                logerror(
                    config=config,
                    text='The page "%s" was missing in the wiki (probably deleted)'
                    % title,
                )
            # here, XML is a correct <page> </page> chunk or
            # an empty string due to a deleted page (logged in errors log) or
            # an empty string due to an error while retrieving the page from server
            # (logged in errors log)
            c += 1

    xmlfile.write(str(footer))
    xmlfile.close()
    print("XML dump saved at...", xmlfilename)
