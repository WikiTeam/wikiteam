import re
from typing import List
from urllib.parse import urlparse

import mwclient
import requests
from file_read_backwards import FileReadBackwards
from mwclient.page import Page

from wikiteam3.dumpgenerator.api.namespaces import (
    getNamespacesAPI,
    getNamespacesScraper,
)
from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.utils import cleanHTML, domain2prefix, undoHTMLEntities
from wikiteam3.utils.monkey_patch import DelaySession


def getPageTitlesAPI(config: Config, session: requests.Session):
    """Uses the API to get the list of page titles"""
    titles = []
    namespaces: List[int] = getNamespacesAPI(config=config, session=session)

    # apply delay to the session for mwclient.Site.allpages()
    delay_session = DelaySession(
        session=session, msg=f"Session delay: {__name__}", config=config
    )
    delay_session.hijack()
    for namespace in namespaces:
        if namespace in config.exnamespaces:
            print("    Skipping namespace = %d" % (namespace))
            continue

        print("    Retrieving titles in the namespace %d" % (namespace))
        apiurl = urlparse(config.api)
        site = mwclient.Site(
            apiurl.netloc,
            apiurl.path.replace("api.php", ""),
            scheme=apiurl.scheme,
            pool=session,
        )
        for page in site.allpages(namespace=str(namespace)):
            if page is Page:
                title = page.name
                titles.append(title)
                yield title

        if len(titles) != len(set(titles)):
            print("Probably a loop, switching to next namespace")
            titles = list(set(titles))

    delay_session.release()


def getPageTitlesScraper(config: Config, session: requests.Session):
    """Scrape the list of page titles from Special:Allpages"""
    titles = []
    namespaces = getNamespacesScraper(config=config, session=session)
    r_title = r'title="(?P<title>[^>]+)">'
    r_suballpages1 = r'&amp;from=(?P<from>[^>"]+)&amp;to=(?P<to>[^>"]+)">'
    r_suballpages2 = r'Special:Allpages/(?P<from>[^>"]+)">'
    r_suballpages3 = r'&amp;from=(?P<from>[^>"]+)" title="[^>]+">'
    # Should be enough subpages on Special:Allpages
    deep = 50
    for namespace in namespaces:
        print("    Retrieving titles in the namespace", namespace)
        url = f"{config.index}?title=Special:Allpages&namespace={namespace}"
        r = session.get(url=url, timeout=30)
        raw = r.text
        raw = cleanHTML(raw)

        r_suballpages = ""
        if re.search(r_suballpages1, raw):
            r_suballpages = r_suballpages1
        elif re.search(r_suballpages2, raw):
            r_suballpages = r_suballpages2
        elif re.search(r_suballpages3, raw):
            r_suballpages = r_suballpages3
        c = 0
        # oldfr = ""
        checked_suballpages = []
        rawacum = raw
        while r_suballpages and re.search(r_suballpages, raw) and c < deep:
            # load sub-Allpages
            m = re.compile(r_suballpages).finditer(raw)
            currfr = None
            for i in m:
                fr = i.group("from")
                currfr = fr

                if r_suballpages == r_suballpages1:
                    to = i.group("to")
                    name = f"{fr}-{to}"
                    url = f"{config.index}?title=Special:Allpages&namespace={namespace}&from={fr}&to={to}"
                elif r_suballpages == r_suballpages2:
                    # clean &amp;namespace=\d, sometimes happens
                    fr = fr.split("&amp;namespace=")[0]
                    name = fr
                    url = f"{config.index}?title=Special:Allpages/{name}&namespace={namespace}"
                elif r_suballpages == r_suballpages3:
                    fr = fr.split("&amp;namespace=")[0]
                    name = fr
                    url = f"{config.index}?title=Special:Allpages&from={name}&namespace={namespace}"
                else:
                    assert False, "Unreachable"

                if name not in checked_suballpages:
                    # to avoid reload dupe subpages links
                    checked_suballpages.append(name)
                    Delay(config=config)
                    # print ('Fetching URL: ', url)
                    r = session.get(url=url, timeout=10)
                    raw = r.text
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

                Delay(config=config)

            assert (
                currfr is not None
            ), "re.search found the pattern, but re.finditer fails, why?"
            # oldfr = currfr
            c += 1

        c = 0
        m = re.compile(r_title).finditer(rawacum)
        for i in m:
            t = undoHTMLEntities(text=i.group("title"))
            if not t.startswith("Special:") and t not in titles:
                titles.append(t)
                c += 1
        print("    %d titles retrieved in the namespace %d" % (c, namespace))
    return titles


def getPageTitles(config: Config, session: requests.Session):
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
        except Exception:
            print("Error: could not get page titles from the API")
            titles = getPageTitlesScraper(config=config, session=session)
    elif config.index:
        titles = getPageTitlesScraper(config=config, session=session)

    titlesfilename = "{}-{}-titles.txt".format(
        domain2prefix(config=config), config.date
    )
    with open(f"{config.path}/{titlesfilename}", "w", encoding="utf-8") as titlesfile:
        c = 0
        for title in titles:
            titlesfile.write(str(title) + "\n")
            c += 1
        # TODO: Sort to remove dupes? In CZ, Widget:AddThis appears two times:
        # main namespace and widget namespace.
        # We can use sort -u in UNIX, but is it worth it?
        titlesfile.write("--END--\n")
    print("Titles saved at...", titlesfilename)

    print("%d page titles loaded" % (c))
    return titlesfilename


def checkTitleOk(
    config: Config,
):
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
    except Exception:
        lasttitle = ""  # probably file does not exists

    return lasttitle == "--END--"


def readTitles(config: Config, session: requests.Session, start: str, batch: bool):
    """Read title list from a file, from the title "start" """
    if not checkTitleOk(config):
        getPageTitles(config=config, session=session)

    titlesfilename = "{}-{}-titles.txt".format(
        domain2prefix(config=config), config.date
    )
    titlesfile = open(f"{config.path}/{titlesfilename}", encoding="utf-8")

    titlelist = []
    seeking = start != ""
    with titlesfile as f:
        for line in f:
            title = line.strip()
            if title == "--END--":
                break
            elif seeking and title != start:
                continue
            elif seeking:
                seeking = False

            if not batch:
                yield title
            else:
                titlelist.append(title)
                if len(titlelist) < batch:
                    continue
                yield titlelist
                titlelist = []
