import re
from typing import Optional
from urllib.parse import urlparse, urljoin

import mwclient
import requests

from wikiteam3.dumpgenerator.api.get_json import get_JSON
from wikiteam3.utils import get_random_UserAgent


def check_API(api: str, session: requests.Session):
    """Checking API availability"""
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
    assert r is not None
    if "MediaWiki API is not enabled for this site." in r.text:
        return None
    try:
        result = get_JSON(r)
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


def mediawiki_get_API_and_Index(url: str, session: requests.Session):
    """Returns the MediaWiki API and Index.php"""

    api = ""
    index = ""
    if not session:
        session = requests.Session()  # Create a new session
        session.headers.update({"User-Agent": get_random_UserAgent()})
    r = session.post(url=url, timeout=120)
    result = r.text

    # API
    m = re.findall(
        r'(?im)<\s*link\s*rel="EditURI"\s*type="application/rsd\+xml"\s*href="([^>]+?)\?action=rsd"[^>]*?>',
        result,
    )
    if m:
        api = m[0]
        if api.startswith("//"):  # relative-protocol URL: https://wiki.gentoo.org/, https://www.mediawiki.org/
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
            if api:
                index = urljoin(api, index.split("/")[-1])
            else:
                index = urljoin(url, index.split("/")[-1])
            #     api = index.split("/index.php")[0] + "/api.php"
            if index.endswith("/Main_Page"):
                index = urljoin(index, "index.php")
    else:
        if api:
            if len(re.findall(r"/index\.php5\?", result)) > len(
                re.findall(r"/index\.php\?", result)
            ):
                index = "/".join(api.split("/")[:-1]) + "/index.php5"
            else:
                index = "/".join(api.split("/")[:-1]) + "/index.php"

    if not api and index:
        api = urljoin(index, "api.php")

    # remove multiple slashes
    # https://romancewiki.bham.ac.uk//api.php -> https://romancewiki.bham.ac.uk/api.php
    # log: https://cdn.digitaldragon.dev/wikibot/jobs/a1847c8b-f01c-4533-8692-579f11da9c94/log.txt
    # log: https://cdn.digitaldragon.dev/wikibot/jobs/4f18485c-e40c-4dcf-9a6d-6d20bf8a82f5/log.txt
    if api:
        api = re.sub(r"([^:])//+", r"\1/", api)
    if index:
        index = re.sub(r"([^:])//+", r"\1/", index)

    return api, index


def check_retry_API(api: str, apiclient=False, *, session: requests.Session):
    """Call check_API and mwclient if necessary"""
    check = None
    try:
        check = check_API(api, session=session)
    except requests.exceptions.ConnectionError as e:
        print("Connection error: %s" % (str(e)))

    if check and apiclient:
        apiurl = urlparse(api)
        try:
            mwclient.Site(
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
                mwclient.Site(
                    apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=newscheme, pool=session
                )
            except KeyError:
                check = False

    return check, api
