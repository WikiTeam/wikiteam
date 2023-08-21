import re
import sys
import time
from typing import *

import requests

from wikiteam3.dumpgenerator.api import handleStatusCode
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.dumpgenerator.exceptions import ExportAbortedError, PageMissingError
from wikiteam3.dumpgenerator.log import logerror
from wikiteam3.utils import uprint


def getXMLPageCore(
    headers: Dict = None, params: Dict = None, config: Config = None, session=None
) -> str:
    """"""
    # returns a XML containing params['limit'] revisions (or current only), ending in </mediawiki>
    # if retrieving params['limit'] revisions fails, returns a current only version
    # if all fail, returns the empty string
    xml = ""
    c = 0
    maxseconds = 100  # max seconds to wait in a single sleeping
    maxretries = config.retries  # x retries and skip
    increment = 20  # increment every retry

    while not re.search(r"</mediawiki>", xml):
        if c > 0 and c < maxretries:
            wait = (
                increment if increment * c < maxseconds else maxseconds
            )  # incremental until maxseconds
            print(
                '    In attempt %d, XML for "%s" is wrong. Waiting %d seconds and reloading...'
                % (c, params["pages"], wait)
            )
            time.sleep(wait)
            # reducing server load requesting smallest chunks (if curonly then
            # limit = 1 from mother function)
            if params["limit"] > 1:
                params["limit"] = params["limit"] / 2  # half
        if c >= maxretries:
            print("    We have retried %d times" % (c))
            print(
                '    MediaWiki error for "%s", network error or whatever...'
                % (params["pages"])
            )
            if config.failfast:
                print("Exit, it will be for another time")
                sys.exit()
            # If it's not already what we tried: our last chance, preserve only the last revision...
            # config.curonly means that the whole dump is configured to save only the last,
            # params['curonly'] should mean that we've already tried this
            # fallback, because it's set by the following if and passed to
            # getXMLPageCore
            if not config.curonly and "curonly" not in params:
                print("    Trying to save only the last revision for this page...")
                params["curonly"] = 1
                logerror(
                    config=config,
                    to_stdout=True,
                    text='Error while retrieving the full history of "%s". Trying to save only the last revision for this page'
                    % (params["pages"]),
                )
                return getXMLPageCore(
                    headers=headers, params=params, config=config, session=session
                )
            else:
                print("    Saving in the errors log, and skipping...")
                logerror(
                    config=config,
                    to_stdout=True,
                    text='Error while retrieving the last revision of "%s". Skipping.'
                    % (params["pages"]),
                )
                raise ExportAbortedError(config.index)
                return ""  # empty xml
        # FIXME HANDLE HTTP Errors HERE
        try:
            r = session.post(
                url=config.index, params=params, headers=headers, timeout=10
            )
            handleStatusCode(r)
            xml = r.text
        except requests.exceptions.ConnectionError as e:
            print("    Connection error: %s" % (str(e.args[0])))
            xml = ""
        except requests.exceptions.ReadTimeout as e:
            print("    Read timeout: %s" % (str(e.args[0])))
            xml = ""
        c += 1

    return xml


def getXMLPageWithExport(config: Config = None, title="", verbose=True, session=None):
    """Get the full history (or current only) of a page"""

    # if server errors occurs while retrieving the full page history, it may return [oldest OK versions] + last version, excluding middle revisions, so it would be partialy truncated
    # http://www.mediawiki.org/wiki/Manual_talk:Parameters_to_Special:Export#Parameters_no_longer_in_use.3F

    limit = 1000
    truncated = False
    title_ = title
    title_ = re.sub(" ", "_", title_)
    # do not convert & into %26, title_ = re.sub('&', '%26', title_)
    if config.export:
        params = {"title": config.export, "pages": title_, "action": "submit"}
    else:
        params = {"title": "Special:Export", "pages": title_, "action": "submit"}
    if config.curonly:
        params["curonly"] = 1
        params["limit"] = 1
    else:
        params["offset"] = "1"  # 1 always < 2000s
        params["limit"] = limit
    # in other case, do not set params['templates']
    if config.templates:
        params["templates"] = 1

    xml = getXMLPageCore(params=params, config=config, session=session)
    if xml == "":
        raise ExportAbortedError(config.index)
    if "</page>" not in xml:
        raise PageMissingError(params["title"], xml)
    else:
        # strip these sha1s sums which keep showing up in the export and
        # which are invalid for the XML schema (they only apply to
        # revisions)
        xml = re.sub(r"\n\s*<sha1>\w+</sha1>\s*\n", "\n", xml)
        xml = re.sub(r"\n\s*<sha1/>\s*\n", "\n", xml)

    yield xml.split("</page>")[0]

    # if complete history, check if this page history has > limit edits, if so, retrieve all using offset if available
    # else, warning about Special:Export truncating large page histories
    r_timestamp = "<timestamp>([^<]+)</timestamp>"

    edit_count = 0
    edit_count += len(re.findall(r_timestamp, xml))

    # search for timestamps in xml to avoid analysing empty pages like
    # Special:Allpages and the random one
    if not config.curonly and re.search(r_timestamp, xml):
        while not truncated and params["offset"]:  # next chunk
            # get the last timestamp from the acum XML
            params["offset"] = re.findall(r_timestamp, xml)[-1]
            try:
                xml2 = getXMLPageCore(params=params, config=config, session=session)
            except MemoryError:
                print("The page's history exceeds our memory, halving limit.")
                params["limit"] = params["limit"] / 2
                continue

            # are there more edits in this next XML chunk or no <page></page>?
            if re.findall(r_timestamp, xml2):
                if re.findall(r_timestamp, xml2)[-1] == params["offset"]:
                    # again the same XML, this wiki does not support params in
                    # Special:Export, offer complete XML up to X edits (usually
                    # 1000)
                    print(
                        "ATTENTION: This wiki does not allow some parameters in Special:Export, therefore pages with large histories may be truncated"
                    )
                    truncated = True
                    break
                else:
                    """</namespaces>
                    </siteinfo>
                    <page>
                    <title>Main Page</title>
                    <id>15580374</id>
                    <restrictions>edit=sysop:move=sysop</restrictions> (?)
                    <revision>
                        <id>418009832</id>
                        <timestamp>2011-03-09T19:57:06Z</timestamp>
                        <contributor>
                    """
                    # offset is OK in this wiki, merge with the previous chunk
                    # of this page history and continue
                    try:
                        xml2 = xml2.split("</page>")[0]
                        yield "  <revision>" + (
                            "<revision>".join(xml2.split("<revision>")[1:])
                        )
                    except MemoryError:
                        "The page's history exceeds our memory, halving limit."
                        params["limit"] = params["limit"] / 2
                        continue
                    xml = xml2
                    edit_count += len(re.findall(r_timestamp, xml))
            else:
                params["offset"] = ""  # no more edits in this page history
    yield "</page>\n"

    if verbose:
        if edit_count == 1:
            uprint("    %s, 1 edit" % (title.strip()))
        else:
            uprint("    %s, %d edits" % (title.strip(), edit_count))
