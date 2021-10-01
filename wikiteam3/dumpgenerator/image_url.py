import re
import sys

from clean_html import undoHTMLEntities


def curateImageURL(config={}, url=""):
    """Returns an absolute URL for an image, adding the domain if missing"""

    if "index" in config and config["index"]:
        # remove from :// (http or https) until the first / after domain
        domainalone = (
            config["index"].split("://")[0]
            + "://"
            + config["index"].split("://")[1].split("/")[0]
        )
    elif "api" in config and config["api"]:
        domainalone = (
            config["api"].split("://")[0]
            + "://"
            + config["api"].split("://")[1].split("/")[0]
        )
    else:
        print("ERROR: no index nor API")
        sys.exit()

    if url.startswith("//"):  # Orain wikifarm returns URLs starting with //
        url = u"%s:%s" % (domainalone.split("://")[0], url)
    # is it a relative URL?
    elif url[0] == "/" or (
        not url.startswith("http://") and not url.startswith("https://")
    ):
        if url[0] == "/":  # slash is added later
            url = url[1:]
        # concat http(s) + domain + relative url
        url = u"%s/%s" % (domainalone, url)
    url = undoHTMLEntities(text=url)
    # url = urllib.parse.unquote(url) #do not use unquote with url, it break some
    # urls with odd chars
    url = re.sub(" ", "_", url)

    return url
