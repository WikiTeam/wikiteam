import re
import sys
from urllib.parse import urlparse

import mwclient
from file_read_backwards import FileReadBackwards

from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.dumpgenerator.api.namespaces import getNamespacesAPI, getNamespacesScraper
from wikiteam3.utils import domain2prefix, cleanHTML, undoHTMLEntities
from wikiteam3.dumpgenerator.config import Config


def getPageTitlesAPI(config: Config=None, session=None):
    """Uses the API to get the list of page titles"""
    titles = []
    namespaces, namespacenames = getNamespacesAPI(config=config, session=session)
    for namespace in namespaces:
        if namespace in config.exnamespaces:
            print("    Skipping namespace = %d" % (namespace))
            continue

        c = 0
        sys.stdout.write("    Retrieving titles in the namespace %d" % (namespace))
        apiurl = urlparse(config.api)
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


def getPageTitlesScraper(config: Config=None, session=None):
    """Scrape the list of page titles from Special:Allpages"""
    titles = []
    namespaces, namespacenames = getNamespacesScraper(config=config, session=session)
    for namespace in namespaces:
        print("    Retrieving titles in the namespace", namespace)
        url = "{}?title=Special:Allpages&namespace: Dict=None".format(
            config.index, namespace
        )
        r = session.get(url=url, timeout=30)
        raw = r.text
        raw = cleanHTML(raw)

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
            currfr = None
            for i in m:
                fr = i.group("from")
                currfr = fr

                if oldfr == currfr:
                    # We are looping, exit the loop
                    pass

                if r_suballpages == r_suballpages1:
                    to = i.group("to")
                    name = f"{fr}-{to}"
                    url = "{}?title=Special:Allpages&namespace: Dict=None&from: Dict=None&to: Dict=None".format(
                        config.index,
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
                    url = "{}?title=Special:Allpages/{}&namespace: Dict=None".format(
                        config.index,
                        name,
                        namespace,
                    )
                elif r_suballpages == r_suballpages3:
                    fr = fr.split("&amp;namespace=")[0]
                    name = fr
                    url = "{}?title=Special:Allpages&from: Dict=None&namespace: Dict=None".format(
                        config.index,
                        name,
                        namespace,
                    )
                else:
                    assert False, "Unreachable"

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
            
            assert currfr is not None, "re.search found the pattern, but re.finditer fails, why?"
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


def getPageTitles(config: Config=None, session=None):
    """Get list of page titles"""
    # http://en.wikipedia.org/wiki/Special:AllPages
    # http://wiki.archiveteam.org/index.php?title=Special:AllPages
    # http://www.wikanda.es/wiki/Especial:Todas
    print(
        "Loading page titles from namespaces = %s"
        % (
            ",".join([str(i) for i in config.namespaces])
            if config.namespaces
            else "None"
        )
    )
    print(
        "Excluding titles from namespaces = %s"
        % (
            ",".join([str(i) for i in config.exnamespaces])
            if config.exnamespaces
            else "None"
        )
    )

    titles = []
    if config.api:
        try:
            titles = getPageTitlesAPI(config=config, session=session)
        except:
            print("Error: could not get page titles from the API")
            titles = getPageTitlesScraper(config=config, session=session)
    elif config.index:
        titles = getPageTitlesScraper(config=config, session=session)

    titlesfilename = "{}-{}-titles.txt".format(
        domain2prefix(config=config), config.date
    )
    titlesfile = open(
        "{}/{}".format(config.path, titlesfilename), "wt", encoding="utf-8"
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

def checkTitleOk(config: Config=None, ):
    try:
        with FileReadBackwards(
                "%s/%s-%s-titles.txt"
                % (
                        config.path,
                        domain2prefix(config=config),
                        config.date,
                ),
                encoding="utf-8",
        ) as frb:
            lasttitle = frb.readline().strip()
            if lasttitle == "":
                lasttitle = frb.readline().strip()
    except:
        lasttitle = ""  # probably file does not exists

    if lasttitle != "--END--":
        return False
    return True


def readTitles(config: Config=None, session=None, start=None, batch=False):
    """Read title list from a file, from the title "start" """
    if not checkTitleOk(config):
        getPageTitles(config=config, session=session)

    titlesfilename = "{}-{}-titles.txt".format(
        domain2prefix(config=config), config.date
    )
    titlesfile = open("{}/{}".format(config.path, titlesfilename), encoding="utf-8")

    titlelist = []
    seeking = False
    if start:
        seeking = True

    with titlesfile as f:
        for line in f:
            title = line.strip()
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
