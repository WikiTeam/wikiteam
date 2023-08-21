import sys
import time
from datetime import datetime
from typing import *
from urllib.parse import urlparse

import lxml.etree
import mwclient
import requests

from wikiteam3.dumpgenerator.api.namespaces import getNamespacesAPI
from wikiteam3.dumpgenerator.api.page_titles import readTitles
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.dumpgenerator.dump.page.xmlrev.xml_revisions_page import (
    makeXmlFromPage,
    makeXmlPageFromRaw,
)
from wikiteam3.dumpgenerator.exceptions import PageMissingError
from wikiteam3.dumpgenerator.log import logerror

ALL_NAMESPACE = -1


def getXMLRevisionsByAllRevisions(
    config: Config = None,
    session=None,
    site: mwclient.Site = None,
    nscontinue=None,
    arvcontinue=None,
):
    if "all" not in config.namespaces:
        namespaces = config.namespaces
    else:
        # namespaces, namespacenames = getNamespacesAPI(config=config, session=session)
        namespaces = [ALL_NAMESPACE]  # magic number refers to "all"
    _nscontinue = nscontinue
    _arvcontinue = arvcontinue

    for namespace in namespaces:
        # Skip retrived namespace
        if namespace == ALL_NAMESPACE:
            assert (
                len(namespaces) == 1
            ), "Only one item shoule be there when 'all' namespace are specified"
            _nscontinue = None
        else:
            if _nscontinue is not None:
                if namespace != _nscontinue:
                    print("Skipping already exported namespace: %d" % namespace)
                    continue
                _nscontinue = None

        print("Trying to export all revisions from namespace %s" % namespace)
        # arvgeneratexml exists but was deprecated in 1.26 (while arv is from 1.27?!)
        arvparams = {
            "action": "query",
            "list": "allrevisions",
            "arvlimit": config.api_chunksize,
            "arvdir": "newer",
        }
        if namespace != ALL_NAMESPACE:
            arvparams["arvnamespace"] = namespace
        if _arvcontinue is not None:
            arvparams["arvcontinue"] = _arvcontinue

        if not config.curonly:
            # We have to build the XML manually...
            # Skip flags, presumably needed to add <minor/> which is in the schema.
            # Also missing: parentid and contentformat.
            arvparams[
                "arvprop"
            ] = "ids|timestamp|user|userid|size|sha1|contentmodel|comment|content|flags"
            print(
                "Trying to get wikitext from the allrevisions API and to build the XML"
            )
            while True:
                try:
                    arvrequest = site.api(http_method=config.http_method, **arvparams)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 405 and config.http_method == "POST":
                        print("POST request to the API failed, retrying with GET")
                        config.http_method = "GET"
                        continue
                    else:
                        raise
                except requests.exceptions.ReadTimeout as err:
                    # Hopefully temporary, just wait a bit and continue with the same request.
                    # No point putting a limit to retries, we'd need to abort everything.
                    # TODO: reuse the retry logic of the checkAPI phase? Or force mwclient
                    # to use the retry adapter we use for our own requests session?
                    print(f"ERROR: {str(err)}")
                    print("Sleeping for 20 seconds")
                    time.sleep(20)
                    continue
                except mwclient.errors.InvalidResponse as e:
                    if (
                        e.response_text.startswith("<!DOCTYPE html>")
                        and config.http_method == "POST"
                    ):
                        print(
                            "POST request to the API failed (got HTML), retrying with GET"
                        )
                        config.http_method = "GET"
                        continue
                    else:
                        raise

                for page in arvrequest["query"]["allrevisions"]:
                    yield makeXmlFromPage(page, arvparams.get("arvcontinue", ""))
                if "continue" in arvrequest:
                    arvparams["arvcontinue"] = arvrequest["continue"]["arvcontinue"]
                else:
                    # End of continuation. We are done with this namespace.
                    break

        else:
            # FIXME: this is not curonly, just different strategy to do all revisions
            # Just cycle through revision IDs and use the XML as is
            print("Trying to list the revisions and to export them one by one")
            # We only need the revision ID, all the rest will come from the raw export
            arvparams["arvprop"] = "ids"
            try:
                arvrequest = site.api(http_method=config.http_method, **arvparams)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 405 and config.http_method == "POST":
                    print("POST request to the API failed, retrying with GET")
                    config.http_method = "GET"
                    continue
                else:
                    raise
            exportparams = {
                "action": "query",
                "export": "1",
            }
            # Skip the namespace if it's empty
            if len(arvrequest["query"]["allrevisions"]) < 1:
                continue
            # Repeat the arvrequest with new arvparams until done
            while True:
                # Reset revision IDs from the previous batch from arv
                revids = []
                for page in arvrequest["query"]["allrevisions"]:
                    for revision in page["revisions"]:
                        revids.append(str(revision["revid"]))
                print(
                    "        %d more revisions listed, until %s"
                    % (len(revids), revids[-1])
                )

                # We can now get the XML for one revision at a time
                # FIXME: we can actually get them in batches as we used to
                # but need to figure out the continuation and avoid that the API
                # chooses to give us only the latest for each page
                for revid in revids:
                    exportparams["revids"] = revid
                    try:
                        exportrequest = site.api(
                            http_method=config.http_method, **exportparams
                        )
                    except requests.exceptions.HTTPError as e:
                        if (
                            e.response.status_code == 405
                            and config.http_method == "POST"
                        ):
                            print("POST request to the API failed, retrying with GET")
                            config.http_method = "GET"
                            exportrequest = site.api(
                                http_method=config.http_method, **exportparams
                            )
                        else:
                            raise

                    # This gives us a self-standing <mediawiki> element
                    # but we only need the inner <page>: we can live with
                    # duplication and non-ordering of page titles, but the
                    # repeated header is confusing and would not even be valid
                    xml = exportrequest["query"]["export"]["*"]  # type(xml) == str
                    yield makeXmlPageFromRaw(xml, arvparams.get("arvcontinue", ""))

                if "continue" in arvrequest:
                    # Get the new ones
                    arvparams["arvcontinue"] = arvrequest["continue"]["arvcontinue"]
                    try:
                        arvrequest = site.api(
                            http_method=config.http_method, **arvparams
                        )
                    except requests.exceptions.HTTPError as e:
                        if (
                            e.response.status_code == 405
                            and config.http_method == "POST"
                        ):
                            print("POST request to the API failed, retrying with GET")
                            config.http_method = "GET"
                            arvrequest = site.api(
                                http_method=config.http_method, **arvparams
                            )
                    except requests.exceptions.ReadTimeout as err:
                        # As above
                        print(f"ERROR: {str(err)}")
                        print("Sleeping for 20 seconds")
                        time.sleep(20)
                        # But avoid rewriting the same revisions
                        arvrequest["query"]["allrevisions"] = []
                        continue
                else:
                    # End of continuation. We are done with this namespace.
                    break


def getXMLRevisionsByTitles(
    config: Config = None, session=None, site: mwclient.Site = None, start=None
):
    if config.curonly:
        # The raw XML export in the API gets a title and gives the latest revision.
        # We could also use the allpages API as generator but let's be consistent.
        print("Getting titles to export the latest revision for each")
        c = 0
        for title in readTitles(config, session=session, start=start):
            # TODO: respect verbose flag, reuse output from getXMLPage
            print(f"    {title}")
            # TODO: as we're doing one page and revision at a time, we might
            # as well use xml format and exportnowrap=1 to use the string of,
            # XML as is, but need to check how well the library handles it.
            exportparams = {
                "action": "query",
                "titles": title,
                "export": "1",
            }
            try:
                exportrequest = site.api(http_method=config.http_method, **exportparams)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 405 and config.http_method == "POST":
                    print("POST request to the API failed, retrying with GET")
                    config.http_method = "GET"
                    exportrequest = site.api(
                        http_method=config.http_method, **exportparams
                    )
                else:
                    raise

            xml = str(exportrequest["query"]["export"]["*"])
            c += 1
            if c % 10 == 0:
                print(f"\n->  Downloaded {c} pages\n")
            # Because we got the fancy XML from the JSON format, clean it:
            yield makeXmlPageFromRaw(xml, None)
    else:
        # This is the closest to what we usually do with Special:Export:
        # take one title at a time and try to get all revisions exported.
        # It differs from the allrevisions method because it actually needs
        # to be input the page titles; otherwise, the requests are similar.
        # The XML needs to be made manually because the export=1 option
        # refuses to return an arbitrary number of revisions (see above).
        print("Getting titles to export all the revisions of each")
        c = 0
        titlelist = []
        # TODO: Decide a suitable number of a batched request. Careful:
        # batched responses may not return all revisions.
        for titlelist in readTitles(config, session=session, start=start, batch=False):
            if type(titlelist) is not list:
                titlelist = [titlelist]
            for title in titlelist:
                print(f"    {title}")
            # Try and ask everything. At least on MediaWiki 1.16, uknown props are discarded:
            # "warnings":{"revisions":{"*":"Unrecognized values for parameter 'rvprop': userid, sha1, contentmodel"}}}
            pparams = {
                "action": "query",
                "titles": "|".join(titlelist),
                "prop": "revisions",
                "rvlimit": config.api_chunksize,
                "rvprop": "ids|timestamp|user|userid|size|sha1|contentmodel|comment|content|flags",
            }
            try:
                prequest = site.api(http_method=config.http_method, **pparams)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 405 and config.http_method == "POST":
                    print("POST request to the API failed, retrying with GET")
                    config.http_method = "GET"
                    prequest = site.api(http_method=config.http_method, **pparams)
                else:
                    raise
            except mwclient.errors.InvalidResponse:
                logerror(
                    config=config,
                    to_stdout=True,
                    text="Error: page inaccessible? Could not export page: %s"
                    % ("; ".join(titlelist)),
                )
                continue

            # Be ready to iterate if there is continuation.
            while True:
                # Get the revision data returned by the API: prequest is the initial request
                # or the new one after continuation at the bottom of this while loop.
                # The array is called "pages" even if there's only one.
                try:
                    pages = prequest["query"]["pages"]
                except KeyError:
                    logerror(
                        config=config,
                        to_stdout=True,
                        text="Error: page inaccessible? Could not export page: %s"
                        % ("; ".join(titlelist)),
                    )
                    break
                # Go through the data we got to build the XML.
                for pageid in pages:
                    try:
                        xml = makeXmlFromPage(pages[pageid], None)
                        yield xml
                    except PageMissingError:
                        logerror(
                            config=config,
                            to_stdout=True,
                            text="Error: empty revision from API. Could not export page: %s"
                            % ("; ".join(titlelist)),
                        )
                        continue

                # Get next batch of revisions if there's more.
                if "continue" in prequest.keys():
                    print("Getting more revisions for the page")
                    for key, value in prequest["continue"].items():
                        pparams[key] = value
                elif "query-continue" in prequest.keys():
                    rvstartid = prequest["query-continue"]["revisions"]["rvstartid"]
                    pparams["rvstartid"] = rvstartid
                else:
                    break

                try:
                    prequest = site.api(http_method=config.http_method, **pparams)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 405 and config.http_method == "POST":
                        print("POST request to the API failed, retrying with GET")
                        config.http_method = "GET"
                        prequest = site.api(http_method=config.http_method, **pparams)

            # We're done iterating for this title or titles.
            c += len(titlelist)
            # Reset for the next batch.
            titlelist = []
            if c % 10 == 0:
                print(f"\n->  Downloaded {c} pages\n")


def getXMLRevisions(
    config: Config = None, session=None, useAllrevision=True, lastPage=None
):
    # FIXME: actually figure out the various strategies for each MediaWiki version
    apiurl = urlparse(config.api)
    # FIXME: force the protocol we asked for! Or don't verify SSL if we asked HTTP?
    # https://github.com/WikiTeam/wikiteam/issues/358
    site = mwclient.Site(
        apiurl.netloc,
        apiurl.path.replace("api.php", ""),
        scheme=apiurl.scheme,
        pool=session,
    )

    if useAllrevision:
        # Find last title
        if lastPage is not None:
            try:
                lastNs = int(lastPage.find("ns").text)
                if False:
                    lastRevision = lastPage.find("revision")
                    lastTimestamp = lastRevision.find("timestamp").text
                    lastRevid = int(lastRevision.find("id").text)
                    lastDatetime = datetime.fromisoformat(lastTimestamp.rstrip("Z"))
                    lastArvcontinue = (
                        lastDatetime.strftime("%Y%m%d%H%M%S") + "|" + str(lastRevid)
                    )
                else:
                    lastArvcontinue = lastPage.attrib["arvcontinue"]
            except Exception:
                print(
                    "Failed to find title in last trunk XML: %s"
                    % (lxml.etree.tostring(lastPage))
                )
                raise
            nscontinue = lastNs
            arvcontinue = lastArvcontinue
            if not arvcontinue:
                arvcontinue = None
        else:
            nscontinue = None
            arvcontinue = None

        try:
            return getXMLRevisionsByAllRevisions(
                config, session, site, nscontinue, arvcontinue
            )
        except (KeyError, mwclient.errors.InvalidResponse) as e:
            print(e)
            # TODO: check whether the KeyError was really for a missing arv API
            print(
                "Warning. Could not use allrevisions. Wiki too old? Try to use --xmlrevisions_page"
            )
            sys.exit()
    else:
        # Find last title
        if lastPage is not None:
            try:
                start = lastPage.find("title")
            except Exception:
                print(
                    "Failed to find title in last trunk XML: %s"
                    % (lxml.etree.tostring(lastPage))
                )
                raise
        else:
            start = None

        try:
            # # Uncomment these lines to raise an KeyError for testing
            # raise KeyError(999999)
            # # DO NOT UNCOMMMENT IN RELEASE
            return getXMLRevisionsByTitles(config, session, site, start)
        except mwclient.errors.MwClientError as e:
            print(e)
            print("This mwclient version seems not to work for us. Exiting.")
            sys.exit()
