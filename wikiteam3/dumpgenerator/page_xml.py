import re
import sys
import time

import requests
from lxml import etree
from lxml.builder import E

from .exceptions import ExportAbortedError, PageMissingError
from .handle_status_code import handleStatusCode
from .log_error import logerror
from .uprint import uprint


def getXMLPageCore(headers={}, params={}, config={}, session=None) -> str:
    """"""
    # returns a XML containing params['limit'] revisions (or current only), ending in </mediawiki>
    # if retrieving params['limit'] revisions fails, returns a current only version
    # if all fail, returns the empty string
    xml = ""
    c = 0
    maxseconds = 100  # max seconds to wait in a single sleeping
    maxretries = config["retries"]  # x retries and skip
    increment = 20  # increment every retry

    while not re.search(r"</mediawiki>", str(xml)):
        if c > 0 and c < maxretries:
            wait = (
                increment * c < maxseconds and increment * c or maxseconds
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
            if config["failfast"]:
                print("Exit, it will be for another time")
                sys.exit()
            # If it's not already what we tried: our last chance, preserve only the last revision...
            # config['curonly'] means that the whole dump is configured to save only the last,
            # params['curonly'] should mean that we've already tried this
            # fallback, because it's set by the following if and passed to
            # getXMLPageCore
            if not config["curonly"] and "curonly" not in params:
                print("    Trying to save only the last revision for this page...")
                params["curonly"] = 1
                logerror(
                    config=config,
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
                    text='Error while retrieving the last revision of "%s". Skipping.'
                    % (params["pages"]),
                )
                raise ExportAbortedError(config["index"])
                return ""  # empty xml
        # FIXME HANDLE HTTP Errors HERE
        try:
            r = session.post(
                url=config["index"], params=params, headers=headers, timeout=10
            )
            handleStatusCode(r)
            xml = fixBOM(r)
        except requests.exceptions.ConnectionError as e:
            print("    Connection error: %s" % (str(e.args[0])))
            xml = ""
        except requests.exceptions.ReadTimeout as e:
            print("    Read timeout: %s" % (str(e.args[0])))
            xml = ""
        c += 1

    return xml


def getXMLPage(config={}, title="", verbose=True, session=None):
    """Get the full history (or current only) of a page"""

    # if server errors occurs while retrieving the full page history, it may return [oldest OK versions] + last version, excluding middle revisions, so it would be partialy truncated
    # http://www.mediawiki.org/wiki/Manual_talk:Parameters_to_Special:Export#Parameters_no_longer_in_use.3F

    limit = 1000
    truncated = False
    title_ = title
    title_ = re.sub(" ", "_", title_)
    # do not convert & into %26, title_ = re.sub('&', '%26', title_)
    try:
        params = {"title": config["export"], "pages": title_, "action": "submit"}
    except KeyError:
        params = {"title": "Special:Export", "pages": title_, "action": "submit"}
    if config["curonly"]:
        params["curonly"] = 1
        params["limit"] = 1
    else:
        params["offset"] = "1"  # 1 always < 2000s
        params["limit"] = limit
    # in other case, do not set params['templates']
    if "templates" in config and config["templates"]:
        params["templates"] = 1

    xml = getXMLPageCore(params=params, config=config, session=session)
    if xml == "":
        raise ExportAbortedError(config["index"])
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
    if not config["curonly"] and re.search(r_timestamp, xml):
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


def makeXmlPageFromRaw(xml):
    """Discard the metadata around a <page> element in <mediawiki> string"""
    root = etree.XML(xml)
    find = etree.XPath("//*[local-name() = 'page']")
    # The tag will inherit the namespace, like:
    # <page xmlns="http://www.mediawiki.org/xml/export-0.10/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    # FIXME: pretty_print doesn't seem to work, only adds a newline
    return etree.tostring(find(root)[0], pretty_print=True, encoding="unicode")


def makeXmlFromPage(page: dict) -> str:
    """Output an XML document as a string from a page as in the API JSON"""
    try:
        p = E.page(
            E.title(str(page["title"])),
            E.ns(str(page["ns"])),
            E.id(str(page["pageid"])),
        )
        for rev in page["revisions"]:
            # Older releases like MediaWiki 1.16 do not return all fields.
            if "userid" in rev:
                userid = rev["userid"]
            else:
                userid = 0
            if "size" in rev:
                size = rev["size"]
            else:
                size = 0
            revision = E.revision(
                E.id(str(rev["revid"])),
                E.timestamp(rev["timestamp"]),
                E.text(str(rev["*"]), space="preserve", bytes=str(size)),
            )
            # The username may be deleted/suppressed
            if "user" in rev:
                revision.append(
                    E.contributor(
                        E.username(str(rev["user"])),
                        E.id(str(userid)),
                    )
                )
            else:
                revision.append(E.contributor(deleted="deleted"))
            if "comment" in rev:
                revision.append(E.comment(str(rev["comment"])))
            if "contentmodel" in rev:
                revision.append(E.model(rev["contentmodel"]))
            # Sometimes a missing parentid is not replaced with a 0 as it should.
            if "parentid" in rev:
                revision.append(E.parentid(str(rev["parentid"])))
            # The sha1 may not have been backfilled on older wikis or lack for other reasons (Wikia).
            if "sha1" in rev:
                revision.append(E.sha1(rev["sha1"]))
            p.append(revision)
    except KeyError as e:
        print(e)
        raise PageMissingError(page["title"], e)
    return etree.tostring(p, pretty_print=True, encoding="unicode")


def fixBOM(request):
    """Strip Unicode BOM"""
    if request.text.startswith("\ufeff"):
        request.encoding = "utf-8-sig"
    return request.text
