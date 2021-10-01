import re
import requests
from user_agent import getUserAgent


def mwGetAPIAndIndex(url=""):
    """Returns the MediaWiki API and Index.php"""

    api = ""
    index = ""
    session = requests.Session()
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
