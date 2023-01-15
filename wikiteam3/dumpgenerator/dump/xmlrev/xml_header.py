import json
import re
import sys
from typing import *

import requests

from wikiteam3.dumpgenerator.exceptions import ExportAbortedError, PageMissingError
from wikiteam3.dumpgenerator.log import logerror
from wikiteam3.dumpgenerator.dump.page.page_xml import getXMLPage
from wikiteam3.dumpgenerator.config import Config

def getXMLHeader(config: Config=None, session=None) -> Tuple[str, Config]:
    """Retrieve a random page to extract XML headers (namespace info, etc)"""
    # get the header of a random page, to attach it in the complete XML backup
    # similar to: <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/"
    # xmlns:x....
    randomtitle = "Main_Page"  # previously AMF5LKE43MNFGHKSDMRTJ
    print(config.api)
    xml = ""
    if config.xmlrevisions and config.api and config.api.endswith("api.php"):
        try:
            print("Getting the XML header from the API")
            # Export and exportnowrap exist from MediaWiki 1.15, allpages from 1.18
            r = session.get(
                config.api
                + "?action=query&export=1&exportnowrap=1&list=allpages&aplimit=1",
                timeout=10,
            )
            xml: str = r.text
            # Otherwise try without exportnowrap, e.g. Wikia returns a blank page on 1.19
            if not re.match(r"\s*<mediawiki", xml):
                r = session.get(
                    config.api
                    + "?action=query&export=1&list=allpages&aplimit=1&format=json",
                    timeout=10,
                )
                try:
                    xml = r.json()["query"]["export"]["*"]
                except KeyError:
                    pass
            if not re.match(r"\s*<mediawiki", xml):
                # Do without a generator, use our usual trick of a random page title
                r = session.get(
                    config.api
                    + "?action=query&export=1&exportnowrap=1&titles="
                    + randomtitle,
                    timeout=10,
                )
                xml = str(r.text)
            # Again try without exportnowrap
            if not re.match(r"\s*<mediawiki", xml):
                r = session.get(
                    config.api
                    + "?action=query&export=1&format=json&titles="
                    + randomtitle,
                    timeout=10,
                )
                try:
                    xml = r.json()["query"]["export"]["*"]
                except KeyError:
                    pass
        except requests.exceptions.RetryError:
            pass

    else:
        try:
            xml = "".join(
                [
                    x
                    for x in getXMLPage(
                        config=config, title=randomtitle, verbose=False, session=session
                    )
                ]
            )
        except PageMissingError as pme:
            # The <page> does not exist. Not a problem, if we get the <siteinfo>.
            xml = pme.xml
        # Issue 26: Account for missing "Special" namespace.
        # Hope the canonical special name has not been removed.
        # http://albens73.fr/wiki/api.php?action=query&meta=siteinfo&siprop=namespacealiases
        except ExportAbortedError:
            try:
                if config.api:
                    print("Trying the local name for the Special namespace instead")
                    r = session.get(
                        url=config.api,
                        params={
                            "action": "query",
                            "meta": "siteinfo",
                            "siprop": "namespaces",
                            "format": "json",
                        },
                        timeout=120,
                    )
                    config.export = (
                        json.loads(r.text)["query"]["namespaces"]["-1"]["*"] + ":Export"
                    )
                    xml = "".join(
                        [
                            x
                            for x in getXMLPage(
                                config=config,
                                title=randomtitle,
                                verbose=False,
                                session=session,
                            )
                        ]
                    )
            except PageMissingError as pme:
                xml = pme.xml
            except ExportAbortedError:
                pass

    header = xml.split("</mediawiki>")[0]
    if not re.match(r"\s*<mediawiki", xml):
        if config.xmlrevisions:
            # Try again the old way
            print(
                "Export test via the API failed. Wiki too old? Trying without xmlrevisions."
            )
            config.xmlrevisions = False
            header, config = getXMLHeader(config=config, session=session)
        else:
            print(xml)
            print("XML export on this wiki is broken, quitting.")
            logerror(to_stdout=True, text="XML export on this wiki is broken, quitting.")
            sys.exit()
    return header, config
