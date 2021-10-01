from get_json import getJSON
from urllib.parse import urlunparse


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
