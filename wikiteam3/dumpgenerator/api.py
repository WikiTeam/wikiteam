import re
import time
from urllib.parse import urlparse, urlunparse

import mwclient
import requests

from .get_json import getJSON
from .user_agent import getUserAgent


def checkAPI(api=None, session=None):
    """Checking API availability"""
    global cj
    # handle redirects
    for i in range(4):
        print("Checking API...", api)
        r = session.get(
            url=api,
            params={"action": "query", "meta": "siteinfo", "format": "json"},
            timeout=30,
        )
        if r.status_code == 200:
            break
        elif r.status_code < 400:
            p = r.url
            api = urlunparse([p.scheme, p.netloc, p.path, "", "", ""])
        elif r.status_code > 400:
            print(
                "MediaWiki API URL not found or giving error: HTTP %d" % r.status_code
            )
            return False
    if "MediaWiki API is not enabled for this site." in r.text:
        return False
    try:
        result = getJSON(r)
        index = None
        if result:
            try:
                index = (
                    result["query"]["general"]["server"]
                    + result["query"]["general"]["script"]
                )
                return (True, index, api)
            except KeyError:
                print("MediaWiki API seems to work but returned no index URL")
                return (True, None, api)
    except ValueError:
        print(repr(r.text))
        print("MediaWiki API returned data we could not parse")
        return False
    return False


def mwGetAPIAndIndex(url="", session=None):
    """Returns the MediaWiki API and Index.php"""

    api = ""
    index = ""
    if not session:
        session = requests.Session()  # Create a new session
        session.headers.update({"User-Agent": getUserAgent()})
    r = session.post(url=url, timeout=120)
    result = r.text

    # API
    m = re.findall(
        r'(?im)<\s*link\s*rel="EditURI"\s*type="application/rsd\+xml"\s*href="([^>]+?)\?action=rsd"\s*/\s*>',
        result,
    )
    if m:
        api = m[0]
        if api.startswith("//"):  # gentoo wiki
            api = url.split("//")[0] + api
    else:
        pass  # build API using index and check it

    # Index.php
    m = re.findall(
        r'<li id="ca-viewsource"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?', result
    )
    if m:
        index = m[0]
    else:
        m = re.findall(
            r'<li id="ca-history"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?', result
        )
        if m:
            index = m[0]
    if index:
        if index.startswith("/"):
            index = "/".join(api.split("/")[:-1]) + "/" + index.split("/")[-1]
    else:
        if api:
            if len(re.findall(r"/index\.php5\?", result)) > len(
                re.findall(r"/index\.php\?", result)
            ):
                index = "/".join(api.split("/")[:-1]) + "/index.php5"
            else:
                index = "/".join(api.split("/")[:-1]) + "/index.php"

    return api, index


def checkRetryAPI(api=None, retries=5, apiclient=False, session=None):
    """Call checkAPI and mwclient if necessary"""
    retry = 0
    retrydelay = 20
    check = None
    while retry < retries:
        try:
            check = checkAPI(api, session=session)
            break
        except requests.exceptions.ConnectionError as e:
            print("Connection error: %s" % (str(e)))
            retry += 1
            print("Start retry attempt %d in %d seconds." % (retry + 1, retrydelay))
            time.sleep(retrydelay)

    if check and apiclient:
        apiurl = urlparse(api)
        try:
            site = mwclient.Site(
                apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=apiurl.scheme, pool=session
            )
        except KeyError:
            # Probably KeyError: 'query'
            if apiurl.scheme == "https":
                newscheme = "http"
                api = api.replace("https://", "http://")
            else:
                newscheme = "https"
                api = api.replace("http://", "https://")
            print(
                "WARNING: The provided API URL did not work with mwclient. Switched protocol to: {}".format(
                    newscheme
                )
            )

            try:
                site = mwclient.Site(
                    apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=newscheme, pool=session
                )
            except KeyError:
                check = False

    return check, api
