import re
import traceback
from typing import Generator, Iterator, Optional
from urllib.parse import urlparse

import mwclient
import mwclient.page
import requests
from file_read_backwards import FileReadBackwards

from wikiteam3.dumpgenerator.api.namespaces import (
    getNamespacesAPI,
    getNamespacesScraper,
)
from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.utils import clean_HTML, undo_HTML_entities, url2prefix_from_config
from wikiteam3.utils.monkey_patch import SessionMonkeyPatch


def getPageTitlesAPI(config: Config, session: requests.Session):
    """Uses the API to get the list of page titles"""
    titles = []
    namespaces, namespacenames = getNamespacesAPI(config=config, session=session)

    # apply delay to the session for mwclient.Site.allpages()
    delay_session = SessionMonkeyPatch(
            session=session, config=config,
            add_delay=True, delay_msg="Session delay: "+__name__,
            hard_retries=3 # TODO: --hard-retries
        )
    delay_session.hijack()
    for namespace in namespaces:
        c = 0
        print("    Retrieving titles in the namespace %d" % (namespace))
        apiurl = urlparse(config.api)
        site = mwclient.Site(
            host=apiurl.netloc,
            path=apiurl.path.replace("api.php", ""),
            scheme=apiurl.scheme,
            pool=session
        )
        for page in site.allpages(namespace=namespace):
            assert isinstance(page, mwclient.page.Page)
            title = page.name
            titles.append(title)
            c += 1
            yield title

        if len(titles) != len(set(titles)):
            print("Probably a loop, switching to next namespace")
            titles = list(set(titles))

    delay_session.release()


def getPageTitlesScraper(config: Config, session: requests.Session):
    """Scrape the list of page titles from Special:Allpages"""
    titles = []
    namespaces, namespacenames = getNamespacesScraper(config=config, session=session)
    for namespace in namespaces:
        print("    Retrieving titles in the namespace", namespace)
        url = "{}?title=Special:Allpages&namespace={}".format(
            config.index, namespace
        )
        r = session.get(url=url, timeout=30)
        raw = r.text
        raw = clean_HTML(raw)

        r_title = r'title="(?P<title>[^>]+)">'
        r_suballpages = ""
        r_suballpages1 = r'&amp;from=(?P<from>[^>"]+)&amp;to=(?P<to>[^>"]+)">'
        r_suballpages2 = r'Special:Allpages/(?P<from>[^>"]+)">'
        r_suballpages3 = r'&amp;from=(?P<from>[^>"]+)" title="[^>]+">'
        if re.search(r_suballpages1, raw):
            r_suballpages = r_suballpages1
        elif re.search(r_suballpages2, raw):
            r_suballpages = r_suballpages2
        elif re.search(r_suballpages3, raw):
            r_suballpages = r_suballpages3
        else:
            pass  # perhaps no subpages

        # Should be enough subpages on Special:Allpages
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
                    url = "{}?title=Special:Allpages&namespace={}&from={}&to={}".format(
                        config.index,
                        namespace,
                        fr,
                        to,
                    )  # do not put urllib.parse.quote in fr or to
                # fix, this regexp doesn't properly save everything? or does r_title fail on this
                # type of subpage? (wikiindex)
                elif r_suballpages == r_suballpages2:
                    # clean &amp;namespace=\d, sometimes happens
                    fr = fr.split("&amp;namespace=")[0]
                    name = fr
                    url = "{}?title=Special:Allpages/{}&namespace={}".format(
                        config.index,
                        name,
                        namespace,
                    )
                elif r_suballpages == r_suballpages3:
                    fr = fr.split("&amp;namespace=")[0]
                    name = fr
                    url = "{}?title=Special:Allpages&from={}&namespace={}".format(
                        config.index,
                        name,
                        namespace,
                    )
                else:
                    assert False, "Unreachable"

                if name not in checked_suballpages:
                    # to avoid reload dupe subpages links
                    checked_suballpages.append(name)
                    Delay(config=config)
                    # print ('Fetching URL: ', url)
                    r = session.get(url=url, timeout=10)
                    raw = str(r.text)
                    raw = clean_HTML(raw)
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
            
            assert currfr is not None, "re.search found the pattern, but re.finditer fails, why?"
            oldfr = currfr
            c += 1

        c = 0
        m = re.compile(r_title).finditer(rawacum)
        for i in m:
            t = undo_HTML_entities(text=i.group("title"))
            if not t.startswith("Special:"):
                if t not in titles:
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
    titles = []
    if config.api:
        try:
            titles = getPageTitlesAPI(config=config, session=session)
        except Exception:
            traceback.print_exc()
            print("Error: could not get page titles from the API")
            titles = getPageTitlesScraper(config=config, session=session)
    elif config.index:
        titles = getPageTitlesScraper(config=config, session=session)

    titlesfilename = "{}-{}-titles.txt".format(
        url2prefix_from_config(config=config), config.date
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

def checkTitleOk(config: Config):
    try:
        with FileReadBackwards(
                "%s/%s-%s-titles.txt"
                % (
                        config.path,
                        url2prefix_from_config(config=config),
                        config.date,
                ),
                encoding="utf-8",
        ) as frb:
            lasttitle = frb.readline().strip()
            if lasttitle == "":
                lasttitle = frb.readline().strip()
    except FileNotFoundError:
        lasttitle = ""  # probably file does not exists

    if lasttitle != "--END--":
        return False
    return True


# @overload
# def read_titles(config: Config, session: requests.Session, start: Optional[str]=None, batch: bool = False) -> Generator[str, None, None]:
#     pass

# @overload
# def read_titles(config: Config, session: requests.Session, start: Optional[str]=None, batch: int = 1) -> Generator[List[str], None, None]:
#     pass

def read_titles(config: Config, session: requests.Session, start: Optional[str]=None
                    ) -> Generator[str, None, None]:
    """Read title list from a file, from the title "start" 
    
    start: title to start reading from, if `None`, start from the beginning
    """

    if not checkTitleOk(config):
        getPageTitles(config=config, session=session)

    titles_filename = "{}-{}-titles.txt".format(
        url2prefix_from_config(config=config), config.date
    )

    with open(f"{config.path}/{titles_filename}", encoding="utf-8") as f:
        yield from read_until_end(source=f, start=start)

def read_until_end(source: Iterator[str], start: Optional[str]=None) -> Generator[str, None, None]:
    seeking = start is not None
    """ If True, we are looking for the `start` title to start reading from """
    end_reached = False
    last_line = None

    for line in source:
        line = line.strip()

        if line == "--END--":
            end_reached = True
        else:
            end_reached = False

        if seeking and last_line != start:
            last_line = line
            continue
        else:
            seeking = False

        if last_line is not None:
            yield last_line

        last_line = line

    if not end_reached:
        raise EOFError("End of file flag `--END--` not found in the last line")