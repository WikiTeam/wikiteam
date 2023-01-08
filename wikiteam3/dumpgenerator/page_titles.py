import re
import sys
from urllib.parse import urlparse

import mwclient

from .delay import Delay
from .domain import domain2prefix
from .namespaces import getNamespacesAPI, getNamespacesScraper
from .util import cleanHTML, undoHTMLEntities


def getPageTitlesAPI(config={}, session=None):
    """Uses the API to get the list of page titles"""
    titles = []
    namespaces, namespacenames = getNamespacesAPI(config=config, session=session)
    for namespace in namespaces:
        if namespace in config["exnamespaces"]:
            print("    Skipping namespace = %d" % (namespace))
            continue

        c = 0
        sys.stdout.write("    Retrieving titles in the namespace %d" % (namespace))
        apiurl = urlparse(config["api"])
        site = mwclient.Site(
            apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=apiurl.scheme, pool=session
        )
        for page in site.allpages(namespace=namespace):
            title = page.name
            titles.append(title)
            c += 1
            yield title

        if len(titles) != len(set(titles)):
            print("Probably a loop, switching to next namespace")
            titles = list(set(titles))

        sys.stdout.write(
            "\r    %d titles retrieved in the namespace %d\n" % (c, namespace)
        )
        sys.stdout.flush()
        Delay(config=config, session=session)


def getPageTitlesScraper(config={}, session=None):
    """Scrape the list of page titles from Special:Allpages"""
    titles = []
    namespaces, namespacenames = getNamespacesScraper(config=config, session=session)
    for namespace in namespaces:
        print("    Retrieving titles in the namespace", namespace)
        url = "{}?title=Special:Allpages&namespace={}".format(
            config["index"], namespace
        )
        r = session.get(url=url, timeout=30)
        raw = str(r.text)
        raw = str(cleanHTML(raw))

        r_title = 'title="(?P<title>[^>]+)">'
        r_suballpages = ""
        r_suballpages1 = '&amp;from=(?P<from>[^>]+)&amp;to=(?P<to>[^>]+)">'
        r_suballpages2 = 'Special:Allpages/(?P<from>[^>]+)">'
        r_suballpages3 = '&amp;from=(?P<from>[^>]+)" title="[^>]+">'
        if re.search(r_suballpages1, raw):
            r_suballpages = r_suballpages1
        elif re.search(r_suballpages2, raw):
            r_suballpages = r_suballpages2
        elif re.search(r_suballpages3, raw):
            r_suballpages = r_suballpages3
        else:
            pass  # perhaps no subpages

        # Should be enought subpages on Special:Allpages
        deep = 50
        c = 0
        oldfr = ""
        checked_suballpages = []
        rawacum = raw
        while r_suballpages and re.search(r_suballpages, raw) and c < deep:
            # load sub-Allpages
            m = re.compile(r_suballpages).finditer(raw)
            for i in m:
                fr = i.group("from")
                currfr = fr

                if oldfr == currfr:
                    # We are looping, exit the loop
                    pass

                if r_suballpages == r_suballpages1:
                    to = i.group("to")
                    name = f"{fr}-{to}"
                    url = "{}?title=Special:Allpages&namespace={}&from={}&to={}".format(
                        config["index"],
                        namespace,
                        fr,
                        to,
                    )  # do not put urllib.parse.quote in fr or to
                # fix, esta regexp no carga bien todas? o falla el r_title en
                # este tipo de subpag? (wikiindex)
                elif r_suballpages == r_suballpages2:
                    # clean &amp;namespace=\d, sometimes happens
                    fr = fr.split("&amp;namespace=")[0]
                    name = fr
                    url = "{}?title=Special:Allpages/{}&namespace={}".format(
                        config["index"],
                        name,
                        namespace,
                    )
                elif r_suballpages == r_suballpages3:
                    fr = fr.split("&amp;namespace=")[0]
                    name = fr
                    url = "{}?title=Special:Allpages&from={}&namespace={}".format(
                        config["index"],
                        name,
                        namespace,
                    )

                if name not in checked_suballpages:
                    # to avoid reload dupe subpages links
                    checked_suballpages.append(name)
                    Delay(config=config, session=session)
                    r = session.get(url=url, timeout=10)
                    # print ('Fetching URL: ', url)
                    raw = str(r.text)
                    raw = cleanHTML(raw)
                    rawacum += raw  # merge it after removed junk
                    print(
                        "    Reading",
                        name,
                        len(raw),
                        "bytes",
                        len(re.findall(r_suballpages, raw)),
                        "subpages",
                        len(re.findall(r_title, raw)),
                        "pages",
                    )

                Delay(config=config, session=session)
            oldfr = currfr
            c += 1

        c = 0
        m = re.compile(r_title).finditer(rawacum)
        for i in m:
            t = undoHTMLEntities(text=i.group("title"))
            if not t.startswith("Special:"):
                if t not in titles:
                    titles.append(t)
                    c += 1
        print("    %d titles retrieved in the namespace %d" % (c, namespace))
    return titles


def getPageTitles(config={}, session=None):
    """Get list of page titles"""
    # http://en.wikipedia.org/wiki/Special:AllPages
    # http://wiki.archiveteam.org/index.php?title=Special:AllPages
    # http://www.wikanda.es/wiki/Especial:Todas
    print(
        "Loading page titles from namespaces = %s"
        % (
            config["namespaces"]
            and ",".join([str(i) for i in config["namespaces"]])
            or "None"
        )
    )
    print(
        "Excluding titles from namespaces = %s"
        % (
            config["exnamespaces"]
            and ",".join([str(i) for i in config["exnamespaces"]])
            or "None"
        )
    )

    titles = []
    if "api" in config and config["api"]:
        try:
            titles = getPageTitlesAPI(config=config, session=session)
        except:
            print("Error: could not get page titles from the API")
            titles = getPageTitlesScraper(config=config, session=session)
    elif "index" in config and config["index"]:
        titles = getPageTitlesScraper(config=config, session=session)

    titlesfilename = "{}-{}-titles.txt".format(
        domain2prefix(config=config), config["date"]
    )
    titlesfile = open(
        "{}/{}".format(config["path"], titlesfilename), "wt", encoding="utf-8"
    )
    c = 0
    for title in titles:
        titlesfile.write(str(title) + "\n")
        c += 1
    # TODO: Sort to remove dupes? In CZ, Widget:AddThis appears two times:
    # main namespace and widget namespace.
    # We can use sort -u in UNIX, but is it worth it?
    titlesfile.write("--END--\n")
    titlesfile.close()
    print("Titles saved at...", titlesfilename)

    print("%d page titles loaded" % (c))
    return titlesfilename


def readTitles(config={}, start=None, batch=False):
    """Read title list from a file, from the title "start" """

    titlesfilename = "{}-{}-titles.txt".format(
        domain2prefix(config=config), config["date"]
    )
    titlesfile = open("{}/{}".format(config["path"], titlesfilename), encoding="utf-8")

    titlelist = []
    seeking = False
    if start:
        seeking = True

    with titlesfile as f:
        for line in f:
            title = str(line).strip()
            if title == "--END--":
                break
            elif seeking and title != start:
                continue
            elif seeking and title == start:
                seeking = False

            if not batch:
                yield title
            else:
                titlelist.append(title)
                if len(titlelist) < batch:
                    continue
                else:
                    yield titlelist
                    titlelist = []
