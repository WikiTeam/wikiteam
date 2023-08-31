import re
import time
import traceback
from typing import Dict

import requests

from wikiteam3.dumpgenerator.api import handleStatusCode
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.dumpgenerator.exceptions import ExportAbortedError, PageMissingError
from wikiteam3.dumpgenerator.log import logerror

try:
    import xml.etree.ElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

import xml.dom.minidom as MD


def reconstructRevisions(root: ElementTree.Element):
    # print ElementTree.tostring(rev)
    page = ElementTree.Element("stub")
    edits = 0

    query: (ElementTree.Element | None) = root.find("query")
    if query is None:
        raise ValueError("query was none")
    pages: (ElementTree.Element | None) = query.find("pages")
    if pages is None:
        raise ValueError("pages was none")
    page_element: (ElementTree.Element | None) = query.find("page")
    if page_element is None:
        raise ValueError("page was none")
    revisions: (ElementTree.Element | None) = page_element.find("revisions")
    if revisions is None:
        raise ValueError("revisions was none")
    for rev in revisions.findall("rev"):
        try:
            rev_ = ElementTree.SubElement(page, "revision")
            # id
            ElementTree.SubElement(rev_, "id").text = rev.attrib["revid"]
            # parentid (optional, export-0.7+)
            if "parentid" in rev.attrib:
                ElementTree.SubElement(rev_, "parentid").text = rev.attrib["parentid"]
            # timestamp
            ElementTree.SubElement(rev_, "timestamp").text = rev.attrib["timestamp"]
            # contributor
            contributor = ElementTree.SubElement(rev_, "contributor")
            if "userhidden" not in rev.attrib:
                ElementTree.SubElement(contributor, "username").text = rev.attrib[
                    "user"
                ]
                ElementTree.SubElement(contributor, "id").text = rev.attrib["userid"]
            else:
                contributor.set("deleted", "deleted")
            # comment (optional)
            if "commenthidden" in rev.attrib:
                print("commenthidden")
                comment = ElementTree.SubElement(rev_, "comment")
                comment.set("deleted", "deleted")
            elif "comment" in rev.attrib and rev.attrib["comment"]:  # '' is empty
                comment = ElementTree.SubElement(rev_, "comment")
                comment.text = rev.attrib["comment"]
            # minor edit (optional)
            if "minor" in rev.attrib:
                ElementTree.SubElement(rev_, "minor")
            # model and format (optional, export-0.8+)
            if "contentmodel" in rev.attrib:
                ElementTree.SubElement(rev_, "model").text = rev.attrib[
                    "contentmodel"
                ]  # default: 'wikitext'
            if "contentformat" in rev.attrib:
                ElementTree.SubElement(rev_, "format").text = rev.attrib[
                    "contentformat"
                ]  # default: 'text/x-wiki'
            # text
            text = ElementTree.SubElement(rev_, "text")
            if "texthidden" not in rev.attrib:
                text.attrib["xml:space"] = "preserve"
                text.attrib["bytes"] = rev.attrib["size"]
                text.text = rev.text
            else:
                # NOTE: this is not the same as the text being empty
                text.set("deleted", "deleted")
            # sha1
            if "sha1" in rev.attrib:
                sha1 = ElementTree.SubElement(rev_, "sha1")
                sha1.text = rev.attrib["sha1"]

            elif "sha1hidden" in rev.attrib:
                ElementTree.SubElement(rev_, "sha1")  # stub
            edits += 1
        except Exception as e:
            # logerror(config=config, text='Error reconstructing revision, xml:%s' % (ElementTree.tostring(rev)))
            print(ElementTree.tostring(rev))
            traceback.print_exc()
            page = None  # type: ignore
            edits = 0
            raise e
    return page, edits


# headers: Dict = None, params: Dict = None
def getXMLPageCoreWithApi(
    headers: Dict,
    params: Dict[str, (str | int)],
    config: Config,
    session: requests.Session,
):
    """ """
    # just send the API request
    # if it fails, it will reduce params['rvlimit']
    xml = ""
    c = 0
    maxseconds = 100  # max seconds to wait in a single sleeping
    maxretries = config.retries  # x retries and skip
    increment = 20  # increment every retry

    while not re.search(
        r"</mediawiki>" if config.curonly else r"</api>", xml
    ) or re.search(r"</error>", xml):
        if c > 0 and c < maxretries:
            wait = (
                increment * c < maxseconds and increment * c or maxseconds
            )  # incremental until maxseconds
            print(
                '    In attempt %d, XML for "%s" is wrong. Waiting %d seconds and reloading...'
                % (c, params["titles" if config.xmlapiexport else "pages"], wait)
            )
            time.sleep(wait)
            # reducing server load requesting smallest chunks (if curonly then
            # rvlimit = 1 from mother function)
            if int(params["rvlimit"]) > 1:
                params["rvlimit"] = int(params["rvlimit"]) // 2  # half
        if c >= maxretries:
            print("    We have retried %d times" % (c))
            print(
                f'    MediaWiki error for "{params["titles" if config.xmlapiexport else "pages"]}", network error or whatever...'
            )
            # If it's not already what we tried: our last chance, preserve only the last revision...
            # config.curonly means that the whole dump is configured to save only the last,
            # params['curonly'] should mean that we've already tried this
            # fallback, because it's set by the following if and passed to
            # getXMLPageCore
            # TODO: save only the last version when failed
            print("    Saving in the errors log, and skipping...")
            logerror(
                config=config,
                text=f'Error while retrieving the last revision of "{params["titles" if config.xmlapiexport else "pages"]}". Skipping.',  # .decode("utf-8")
            )
            raise ExportAbortedError(config.index)
        # FIXME HANDLE HTTP Errors HERE
        try:
            r = session.get(url=config.api, params=params, headers=headers)
            handleStatusCode(r)
            xml = r.text
            # print xml
        except requests.exceptions.ConnectionError as e:
            print(f"    Connection error: {str(e.args[0])}")
            xml = ""
        except requests.exceptions.ReadTimeout as e:
            print(f"    Read timeout: {str(e.args[0])}")
            xml = ""
        c += 1
    return xml


# title="", verbose=True
def getXMLPageWithApi(
    config: Config, title: str, verbose: bool, session: requests.Session
):
    """Get the full history (or current only) of a page using API:Query
    if params['curonly'] is set, then using export&exportwrap to export
    """

    title_ = title
    title_ = re.sub(" ", "_", title_)
    if not config.curonly:
        params = {
            "titles": title_,
            "action": "query",
            "format": "xml",
            "prop": "revisions",
            "rvprop": "timestamp|user|comment|content|"  # rvprop: <https://www.mediawiki.org/wiki/API:Revisions#Parameter_history>  # MW v????
            "ids|flags|size|"  # MW v1.11
            "userid|"  # MW v1.17
            "sha1|"  # MW v1.19
            "contentmodel|",  # MW v1.21
            "rvcontinue": None,
            "rvlimit": config.api_chunksize,
        }
        firstpartok: bool = False
        lastcontinue: str = ""
        numberofedits = 0
        ret = ""
        continueKey: str = ""
        while True:
            # in case the last request is not right, saving last time's progress
            if not firstpartok:
                try:
                    lastcontinue = params[continueKey]
                except Exception:
                    lastcontinue = ""

            xml = getXMLPageCoreWithApi(
                headers={}, params=params, config=config, session=session
            )
            if xml == "":
                # just return so that we can continue, and getXMLPageCoreWithApi will log the error
                return
            try:
                root = ElementTree.fromstring(xml.encode("utf-8"))
            except Exception:
                continue
            try:
                ret_query: (ElementTree.Element | None) = root.find("query")
                if ret_query is None:
                    raise Exception("query was none")
                ret_pages: (ElementTree.Element | None) = root.find("pages")
                if ret_pages is None:
                    raise Exception("pages was none")
                ret_page = ret_pages.find("page")
                if ret_page is None:
                    continue
            except Exception:
                continue
            if "missing" in ret_page.attrib or "invalid" in ret_page.attrib:
                print("Page not found")
                raise PageMissingError(params["titles"], xml)
            if not firstpartok:
                try:
                    # build the firstpart by ourselves to improve the memory usage
                    ret = "  <page>\n"
                    ret += "    <title>%s</title>\n" % (ret_page.attrib["title"])
                    ret += "    <ns>%s</ns>\n" % (ret_page.attrib["ns"])
                    ret += "    <id>%s</id>\n" % (ret_page.attrib["pageid"])
                except Exception:
                    firstpartok = False
                    continue
                else:
                    firstpartok = True
                    yield ret

            continueVal = None
            continue_element: (ElementTree.Element | None) = root.find("continue")
            query_continue_element: (ElementTree.Element | None) = root.find(
                "query-continue"
            )
            if continue_element is not None:
                # uses continue.rvcontinue
                # MW 1.26+
                continueKey = "rvcontinue"
                continueVal = continue_element.attrib["rvcontinue"]
            elif query_continue_element is not None:
                rev_continue = query_continue_element.find("revisions")
                assert rev_continue is not None, "Should only have revisions continue"
                if "rvcontinue" in rev_continue.attrib:
                    # MW 1.21 ~ 1.25
                    continueKey = "rvcontinue"
                    continueVal = rev_continue.attrib["rvcontinue"]
                elif "rvstartid" in rev_continue.attrib:
                    # TODO: MW ????
                    continueKey = "rvstartid"
                    continueVal = rev_continue.attrib["rvstartid"]
                else:
                    # blindly assume the first attribute is the continue key
                    # may never happen
                    assert (
                        len(rev_continue.attrib) > 0
                    ), "Should have at least one attribute"
                    for continueKey in rev_continue.attrib.keys():
                        continueVal = rev_continue.attrib[continueKey]
                        break
            if continueVal is not None:
                params[continueKey] = continueVal
            try:
                ret = ""
                edits = 0

                # transform the revision
                rev_, edits = reconstructRevisions(root=root)
                xmldom = MD.parseString(
                    b"<stub1>" + ElementTree.tostring(rev_) + b"</stub1>"
                )
                # convert it into text in case it throws MemoryError
                # delete the first three line and last two line,which is for setting the indent
                ret += "".join(xmldom.toprettyxml(indent="  ").splitlines(True)[3:-2])
                yield ret
                numberofedits += edits
                if config.curonly or continueVal is None:  # no continue
                    break
            except Exception:
                traceback.print_exc()
                params["rvcontinue"] = lastcontinue
                ret = ""
        yield "  </page>\n"
    else:
        params = {
            "titles": title_,
            "action": "query",
            "format": "xml",
            "export": 1,
            "exportnowrap": 1,
        }
        xml = getXMLPageCoreWithApi(
            headers={}, params=params, config=config, session=session
        )
        if xml == "":
            raise ExportAbortedError(config.index)
        if "</page>" not in xml:
            raise PageMissingError(params["titles"], xml)
        # strip these sha1s sums which keep showing up in the export and
        # which are invalid for the XML schema (they only apply to
        # revisions)
        xml = re.sub(r"\n\s*<sha1>\w+</sha1>\s*\n", r"\n", xml)
        xml = re.sub(r"\n\s*<sha1/>\s*\n", r"\n", xml)

        yield xml.split("</page>")[0]

        # just for looking good :)
        r_timestamp = r"<timestamp>([^<]+)</timestamp>"

        numberofedits = 0 + len(re.findall(r_timestamp, xml))
        yield "</page>\n"

    if verbose:
        if numberofedits == 1:
            print(f"    {title.strip()}, 1 edit")
        else:
            print("    %s, %d edits" % (title.strip(), numberofedits))
