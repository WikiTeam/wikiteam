import delay
import re
import sys

from clean_xml import cleanXML
from domain import domain2prefix
from exceptions import PageMissingError
from log_error import logerror
from page_titles import readTitles
from page_xml import getXMLPage
from readline import reverse_readline
from xml_header import getXMLHeader
from xml_revisions import getXMLRevisions


def generateXMLDump(config={}, titles=[], start=None, session=None):
    """Generates a XML dump for a list of titles or from revision IDs"""
    # TODO: titles is now unused.

    header, config = getXMLHeader(config=config, session=session)
    footer = "</mediawiki>\n"  # new line at the end
    xmlfilename = "%s-%s-%s.xml" % (
        domain2prefix(config=config),
        config["date"],
        config["curonly"] and "current" or "history",
    )
    xmlfile = ""
    lock = True

    if config["xmlrevisions"]:
        if start:
            print(
                "WARNING: will try to start the download from title: {}".format(start)
            )
            xmlfile = open("%s/%s" % (config["path"], xmlfilename), "a")
        else:
            print("Retrieving the XML for every page from the beginning")
            xmlfile = open("%s/%s" % (config["path"], xmlfilename), "wb")
            xmlfile.write(header)
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
    else:
        print(
            'Retrieving the XML for every page from "%s"' % (start and start or "start")
        )
        if start:
            print(
                "Removing the last chunk of past XML dump: it is probably incomplete."
            )
            for i in reverse_readline(
                "%s/%s" % (config["path"], xmlfilename), truncate=True
            ):
                pass
        else:
            # requested complete xml dump
            lock = False
            xmlfile = open("%s/%s" % (config["path"], xmlfilename), "w")
            xmlfile.write(header)
            xmlfile.close()

        xmlfile = open("%s/%s" % (config["path"], xmlfilename), "a")
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
                    text=u'The page "%s" was missing in the wiki (probably deleted)'
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
