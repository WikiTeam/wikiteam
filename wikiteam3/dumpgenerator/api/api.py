import re
from typing import Any, Literal, Optional
from urllib.parse import urljoin, urlparse

import mwclient
import requests

from wikiteam3.utils import getUserAgent

from .get_json import getJSON


# api="", session: requests.Session = None
def checkAPI(api: str, session: requests.Session):
    """Checking API availability"""
    global cj
    # handle redirects
    r: Optional[requests.Response] = None
    for i in range(4):
        print("Checking API...", api)
        r = session.get(
            url=api,
            params={"action": "query", "meta": "siteinfo", "format": "json"},
            timeout=30,
        )
        if i >= 4:
            break
        if r.status_code == 200:
            break
        elif r.status_code < 400:
            api = r.url
        elif r.status_code > 400:
            print(
                "MediaWiki API URL not found or giving error: HTTP %d" % r.status_code
            )
            return None
    if r is not None:
        if "MediaWiki API is not enabled for this site." in r.text:
            return None
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
            return None
    return None


# url=""
def mwGetAPIAndIndex(url: str, session: requests.Session):
    """Returns the MediaWiki API and Index.php"""

    api = ""
    index = ""
    if not session:
        session = requests.Session()  # Create a new session
        session.headers.update({"User-Agent": getUserAgent()})
    r = session.post(url=url, timeout=120)
    result = r.text

    if m := re.findall(
        r'(?im)<\s*link\s*rel="EditURI"\s*type="application/rsd\+xml"\s*href="([^>]+?)\?action=rsd"\s*/\s*>',
        result,
    ):
        api = m[0]
        if api.startswith("//"):  # gentoo wiki
            api = url.split("//")[0] + api
    if m := re.findall(
        r'<li id="ca-viewsource"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?',
        result,
    ):
        index = m[0]
    elif m := re.findall(
        r'<li id="ca-history"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?',
        result,
    ):
        index = m[0]
    if index:
        if index.startswith("/"):
            index = (
                urljoin(api, index.split("/")[-1])
                if api
                else urljoin(url, index.split("/")[-1])
            )
            #     api = index.split("/index.php")[0] + "/api.php"
            if index.endswith("/Main_Page"):
                index = urljoin(index, "index.php")
    elif api:
        if len(re.findall(r"/index\.php5\?", result)) > len(
            re.findall(r"/index\.php\?", result)
        ):
            index = "/".join(api.split("/")[:-1]) + "/index.php5"
        else:
            index = "/".join(api.split("/")[:-1]) + "/index.php"

    if not api and index:
        api = urljoin(index, "api.php")

    return api, index


# api="", apiclient=False
def checkRetryAPI(api: str, apiclient: bool, session: requests.Session):
    """Call checkAPI and mwclient if necessary"""
    check: (tuple[Literal[True], Any, str] | tuple[Literal[True], None, str] | None)
    try:
        check = checkAPI(api, session=session)
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {str(e)}")
        check = None

    if check and apiclient:
        apiurl = urlparse(api)
        try:
            # Returns a value, but we're just checking for an error here
            mwclient.Site(
                apiurl.netloc,
                apiurl.path.replace("api.php", ""),
                scheme=apiurl.scheme,
                pool=session,
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
                f"WARNING: The provided API URL did not work with mwclient. Switched protocol to: {newscheme}"
            )

            try:
                # Returns a value, but we're just checking for an error here
                mwclient.Site(
                    apiurl.netloc,
                    apiurl.path.replace("api.php", ""),
                    scheme=newscheme,
                    pool=session,
                )
            except KeyError:
                check = False  # type: ignore

    return check, api  # type: ignore
