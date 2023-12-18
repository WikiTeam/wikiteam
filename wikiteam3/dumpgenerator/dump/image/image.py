import os
import random
import re
import sys
import time
import urllib.parse
from typing import Dict, List, Optional

import requests

from wikiteam3.dumpgenerator.api import getJSON, handleStatusCode
from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.dumpgenerator.dump.image.html_regexs import R_NEXT, REGEX_CANDIDATES
from wikiteam3.dumpgenerator.dump.page.xmlexport.page_xml import getXMLPage
from wikiteam3.dumpgenerator.exceptions import FileSizeError, PageMissingError
from wikiteam3.dumpgenerator.log import logerror
from wikiteam3.utils import cleanHTML, domain2prefix, sha1File, undoHTMLEntities


class Image:
    @staticmethod
    def getXMLFileDesc(config: Config = None, title="", session=None):
        """Get XML for image description page"""
        config.curonly = 1  # tricky to get only the most recent desc
        return "".join(
            list(getXMLPage(config=config, title=title, verbose=False, session=session))
        )

    @staticmethod
    def generateImageDump(
        config: Config = None,
        other: Dict = None,
        images: List[List] = None,
        session: requests.Session = None,
    ):
        """Save files and descriptions using a file list\n
        Deprecated: `start` is not used anymore."""

        # fix use subdirectories md5
        print("Retrieving images...")
        imagepath = f"{config.path}/images"
        if not os.path.isdir(imagepath):
            print(f'Creating "{imagepath}" directory')
            os.makedirs(imagepath)

        c_savedImageFiles = 0
        c_savedImageDescs = 0

        bypass_cdn_image_compression: bool = other["bypass_cdn_image_compression"]
        disable_image_verify: bool = other["disable_image_verify"]

        def modify_params(params: Optional[Dict] = None) -> Dict:
            """bypass Cloudflare Polish (image optimization)"""
            if params is None:
                params = {}
            if bypass_cdn_image_compression:
                # bypass Cloudflare Polish (image optimization)
                # <https://developers.cloudflare.com/images/polish/>
                params["_wiki_t"] = int(time.time() * 1000)
                params[f"_wiki_{random.randint(10,99)}_"] = "random"

            return params

        def check_response(r: requests.Response) -> None:
            assert not r.headers.get(
                "cf-polished", ""
            ), "Found cf-polished header in response, use --bypass-cdn-image-compression to bypass it"

        for filename, url, uploader, size, sha1 in images:
            toContinue = 0

            # saving file
            filename2 = urllib.parse.unquote(filename)
            if len(filename2.encode("utf-8")) > other["filenamelimit"]:
                logerror(
                    config=config,
                    to_stdout=True,
                    text=f"Filename is too long(>240 bytes), skipping: '{filename2}'",
                )
                continue
            filename3 = f"{imagepath}/{filename2}"

            # check if file already exists and has the same size and sha1
            if (
                size != "False"
                and os.path.isfile(filename3)
                and os.path.getsize(filename3) == int(size)
                and sha1File(filename3) == sha1
            ) or (sha1 == "False" and os.path.isfile(filename3)):
                # sha1 is 'False' if file not in original wiki (probably deleted,
                # you will get a 404 error if you try to download it)
                c_savedImageFiles += 1
                toContinue += 1
                print_msg = f"    {c_savedImageFiles}|sha1 matched: {filename2}"
                print(print_msg[:70], end="\r")
                if sha1 == "False":
                    logerror(
                        config=config,
                        to_stdout=True,
                        text=f"sha1 is 'False' for {filename2}, file may not in wiki site (probably deleted). "
                        + "we will not try to download it...",
                    )
            else:
                Delay(config=config, session=session)
                original_url = url
                r = session.head(url=url, params=modify_params(), allow_redirects=True)
                check_response(r)
                original_url_redirected = len(r.history) > 0

                if original_url_redirected:
                    # print 'Site is redirecting us to: ', r.url
                    original_url = url
                    url = r.url

                r = session.get(url=url, params=modify_params(), allow_redirects=False)
                check_response(r)

                # Try to fix a broken HTTP to HTTPS redirect
                if r.status_code == 404 and original_url_redirected:
                    if (
                        original_url.split("://")[0] == "http"
                        and url.split("://")[0] == "https"
                    ):
                        url = "https://" + original_url.split("://")[1]
                        # print 'Maybe a broken http to https redirect, trying ', url
                        r = session.get(
                            url=url, params=modify_params(), allow_redirects=False
                        )
                        check_response(r)

                if r.status_code == 200:
                    try:
                        if (
                            size == "False"
                            or len(r.content) == int(size)
                            or disable_image_verify
                        ):
                            # size == 'False' means size is unknown
                            with open(filename3, "wb") as imagefile:
                                imagefile.write(r.content)
                            c_savedImageFiles += 1
                        else:
                            raise FileSizeError(file=filename3, size=size)
                    except OSError:
                        logerror(
                            config=config,
                            to_stdout=True,
                            text=f"File '{filename3}' could not be created by OS",
                        )
                    except FileSizeError as e:
                        # TODO: add a --force-download-image or --nocheck-image-size option to download anyway
                        logerror(
                            config=config,
                            to_stdout=True,
                            text=f"File '{e.file}' size is not match '{e.size}', skipping",
                        )
                else:
                    logerror(
                        config=config,
                        to_stdout=True,
                        text=f"Failed to download '{filename2}' with URL '{url}' due to HTTP '{r.status_code}', skipping",
                    )

            if os.path.isfile(f"{filename3}.desc"):
                toContinue += 1
            else:
                Delay(config=config, session=session)
                # saving description if any
                title = f"Image:{filename}"
                try:
                    if (
                        config.xmlrevisions
                        and config.api
                        and config.api.endswith("api.php")
                    ):
                        r = session.get(
                            config.api
                            + "?action=query&export&exportnowrap&titles="
                            + urllib.parse.quote(title)
                        )
                        xmlfiledesc = r.text
                    else:
                        xmlfiledesc = Image.getXMLFileDesc(
                            config=config, title=title, session=session
                        )  # use Image: for backwards compatibility
                except PageMissingError:
                    xmlfiledesc = ""
                    logerror(
                        config=config,
                        to_stdout=True,
                        text=f'The image description page "{str(title)}" was missing in the wiki (probably deleted)',
                    )

                try:
                    # <text xml:space="preserve" bytes="36">Banner featuring SG1, SGA, SGU teams</text>
                    if not re.search(r"</page>", xmlfiledesc):
                        # failure when retrieving desc? then save it as empty .desc
                        xmlfiledesc = ""

                    # Fixup the XML
                    if xmlfiledesc != "" and not re.search(
                        r"</mediawiki>", xmlfiledesc
                    ):
                        xmlfiledesc += "</mediawiki>"

                    with open(
                        f"{imagepath}/{filename2}.desc", "w", encoding="utf-8"
                    ) as f:
                        f.write(xmlfiledesc)
                    c_savedImageDescs += 1

                    if not xmlfiledesc:
                        logerror(
                            config=config,
                            to_stdout=True,
                            text=f"Created empty .desc file: '{imagepath}/{filename2}.desc'",
                        )

                except OSError:
                    logerror(
                        config=config,
                        to_stdout=True,
                        text=f"File {imagepath}/{filename2}.desc could not be created by OS",
                    )

            if toContinue == 2:  # skip printing
                continue
            print_msg = (
                f"              | {len(images) - c_savedImageFiles}=>{filename2[:50]}"
            )
            print(print_msg, " " * (73 - len(print_msg)), end="\r")

        print(
            f"Downloaded {c_savedImageFiles} images and {c_savedImageDescs} .desc files."
        )

    @staticmethod
    def getImageNames(config: Config = None, session: requests.Session = None):
        """Get list of image names"""

        print(")Retrieving image filenames")
        images = []
        if config.api:
            print("Using API to retrieve image names...")
            images = Image.getImageNamesAPI(config=config, session=session)
        elif config.index:
            print("Using index.php (Special:Imagelist) to retrieve image names...")
            images = Image.getImageNamesScraper(config=config, session=session)

        # images = list(set(images)) # it is a list of lists
        print("Sorting image filenames")
        images.sort()

        print("%d image names loaded" % (len(images)))
        return images

    @staticmethod
    def getImageNamesScraper(config: Config = None, session: requests.Session = None):
        """Retrieve file list: filename, url, uploader"""

        images = []
        offset = "29990101000000"  # january 1, 2999
        limit = 5000
        retries = config.retries
        while offset:
            # 5000 overload some servers, but it is needed for sites like this with
            # no next links
            # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
            r = session.post(
                url=config.index,
                params={"title": "Special:Imagelist", "limit": limit, "offset": offset},
                timeout=30,
            )
            raw = r.text
            Delay(config=config, session=session)
            # delicate wiki
            if re.search(
                r"(?i)(allowed memory size of \d+ bytes exhausted|Call to a member function getURL)",
                raw,
            ):
                if limit > 10:
                    print(
                        "Error: listing %d images in a chunk is not possible, trying tiny chunks"
                        % (limit)
                    )
                    limit = limit / 10
                    continue
                elif retries > 0:  # waste retries, then exit
                    retries -= 1
                    print("Retrying...")
                    continue
                else:
                    print("No more retries, exit...")
                    break

            raw = cleanHTML(raw)

            # Select the regexp that returns more results
            best_matched = 0
            regexp_best = None
            for regexp in REGEX_CANDIDATES:
                _count = len(re.findall(regexp, raw))
                if _count > best_matched:
                    best_matched = _count
                    regexp_best = regexp
            assert (
                regexp_best is not None
            ), "Could not find a proper regexp to parse the HTML"
            m = re.compile(regexp_best).finditer(raw)

            # Iter the image results
            for i in m:
                url = i.group("url")
                url = Image.curateImageURL(config=config, url=url)
                filename = re.sub("_", " ", i.group("filename"))
                filename = undoHTMLEntities(text=filename)
                filename = urllib.parse.unquote(filename)
                uploader = re.sub("_", " ", i.group("uploader"))
                uploader = undoHTMLEntities(text=uploader)
                uploader = urllib.parse.unquote(uploader)
                images.append(
                    [
                        filename,
                        url,
                        uploader,
                        "False",
                        "False",  # size, sha1 not available
                    ]
                )
                # print (filename, url)

            if re.search(R_NEXT, raw):
                new_offset = re.findall(R_NEXT, raw)[0]
                # Avoid infinite loop
                if new_offset != offset:
                    offset = new_offset
                    retries += 5  # add more retries if we got a page with offset
                else:
                    offset = ""
            else:
                offset = ""

        if len(images) == 1:
            print("    Found 1 image")
        else:
            print("    Found %d images" % (len(images)))

        images.sort()
        return images

    @staticmethod
    def getImageNamesAPI(config: Config = None, session: requests.Session = None):
        """Retrieve file list: filename, url, uploader, size, sha1"""
        # # Commented by @yzqzss:
        # https://www.mediawiki.org/wiki/API:Allpages
        # API:Allpages requires MW >= 1.8
        # (Note: The documentation says that it requires MediaWiki >= 1.18, but that's not true.)
        # (Read the revision history of [[API:Allpages]] and the source code of MediaWiki, you will
        # know that it's existed since MW 1.8) (2023-05-09)
        # https://www.mediawiki.org/wiki/API:Allimages
        # API:Allimages requires MW >= 1.13

        aifrom = "!"
        images = []
        countImages = 0
        oldAPI = False
        while aifrom:
            print(
                f"Using API:Allimages to get the list of images, {len(images)} images found so far...",
                end="\r",
            )
            params = {
                "action": "query",
                "list": "allimages",
                "aiprop": "url|user|size|sha1",
                "aifrom": aifrom,
                "format": "json",
                "ailimit": config.api_chunksize,
            }
            # FIXME Handle HTTP Errors HERE
            r = session.get(url=config.api, params=params, timeout=30)
            handleStatusCode(r)
            jsonimages = getJSON(r)
            Delay(config=config, session=session)

            if "query" in jsonimages:
                countImages += len(jsonimages["query"]["allimages"])

                # oldAPI = True
                # break
                # # uncomment to force use API:Allpages generator
                # # may also can as a fallback if API:Allimages response is wrong

                aifrom = ""
                if (
                    "query-continue" in jsonimages
                    and "allimages" in jsonimages["query-continue"]
                ):
                    if "aicontinue" in jsonimages["query-continue"]["allimages"]:
                        aifrom = jsonimages["query-continue"]["allimages"]["aicontinue"]
                    elif "aifrom" in jsonimages["query-continue"]["allimages"]:
                        aifrom = jsonimages["query-continue"]["allimages"]["aifrom"]
                elif "continue" in jsonimages:
                    if "aicontinue" in jsonimages["continue"]:
                        aifrom = jsonimages["continue"]["aicontinue"]
                    elif "aifrom" in jsonimages["continue"]:
                        aifrom = jsonimages["continue"]["aifrom"]
                print(
                    countImages, aifrom[:30] + " " * (60 - len(aifrom[:30])), end="\r"
                )

                for image in jsonimages["query"]["allimages"]:
                    url = image["url"]
                    url = Image.curateImageURL(config=config, url=url)
                    # encoding to ascii is needed to work around this horrible bug:
                    # http://bugs.python.org/issue8136
                    # (ascii encoding removed because of the following)
                    #
                    # unquote() no longer supports bytes-like strings
                    # so unicode may require the following workaround:
                    # https://izziswift.com/how-to-unquote-a-urlencoded-unicode-string-in-python/
                    if ".wikia." in config.api or ".fandom.com" in config.api:
                        filename = urllib.parse.unquote(
                            re.sub("_", " ", url.split("/")[-3])
                        )
                    else:
                        filename = urllib.parse.unquote(
                            re.sub("_", " ", url.split("/")[-1])
                        )
                    if "%u" in filename:
                        raise NotImplementedError(
                            f"Filename {filename} contains unicode. Please file an issue with MediaWiki Dump Generator."
                        )
                    uploader = re.sub("_", " ", image.get("user", "Unknown"))
                    size = image.get("size", "False")

                    # size or sha1 is not always available (e.g. https://wiki.mozilla.org/index.php?curid=20675)
                    sha1 = image.get("sha1", "False")
                    images.append([filename, url, uploader, size, sha1])
            else:
                oldAPI = True
                break

        if oldAPI:
            print(
                "    API:Allimages not available. Using API:Allpages generator instead."
            )
            gapfrom = "!"
            images = []
            while gapfrom:
                sys.stderr.write(".")  # progress
                # Some old APIs doesn't have allimages query
                # In this case use allpages (in nm=6) as generator for imageinfo
                # Example:
                # http://minlingo.wiki-site.com/api.php?action=query&generator=allpages&gapnamespace=6
                # &gaplimit=500&prop=imageinfo&iiprop=user|url&gapfrom=!
                params = {
                    "action": "query",
                    "generator": "allpages",
                    "gapnamespace": 6,
                    "gaplimit": config.api_chunksize,  # The value must be between 1 and 500.
                    # TODO: Is it OK to set it higher, for speed?
                    "gapfrom": gapfrom,
                    "prop": "imageinfo",
                    "iiprop": "url|user|size|sha1",
                    "format": "json",
                }
                # FIXME Handle HTTP Errors HERE
                r = session.get(url=config.api, params=params, timeout=30)
                handleStatusCode(r)
                jsonimages = getJSON(r)
                Delay(config=config, session=session)

                if "query" not in jsonimages:
                    # if the API doesn't return query data, then we're done
                    break

                countImages += len(jsonimages["query"]["pages"])
                print(
                    countImages, gapfrom[:30] + " " * (60 - len(gapfrom[:30])), end="\r"
                )

                gapfrom = ""

                # all moden(at 20221231) wikis return 'continue' instead of 'query-continue'
                if "continue" in jsonimages and "gapcontinue" in jsonimages["continue"]:
                    gapfrom = jsonimages["continue"]["gapcontinue"]

                # legacy code, not sure if it's still needed by some old wikis
                elif (
                    "query-continue" in jsonimages
                    and "allpages" in jsonimages["query-continue"]
                ):
                    if "gapfrom" in jsonimages["query-continue"]["allpages"]:
                        gapfrom = jsonimages["query-continue"]["allpages"]["gapfrom"]

                # print (gapfrom)
                # print (jsonimages['query'])

                for image, props in jsonimages["query"]["pages"].items():
                    url = props["imageinfo"][0]["url"]
                    url = Image.curateImageURL(config=config, url=url)

                    tmp_filename = ":".join(props["title"].split(":")[1:])

                    filename = re.sub("_", " ", tmp_filename)
                    uploader = re.sub("_", " ", props["imageinfo"][0]["user"])
                    size = props.get("imageinfo")[0].get("size", "False")
                    sha1 = props.get("imageinfo")[0].get("sha1", "False")
                    images.append([filename, url, uploader, size, sha1])
        if len(images) == 1:
            print("    Found 1 image")
        else:
            print("    Found %d images" % (len(images)))

        return images

    @staticmethod
    def saveImageNames(config: Config = None, images: List[List] = None, session=None):
        """Save image list in a file, including filename, url, uploader, size and sha1"""

        imagesfilename = "{}-{}-images.txt".format(
            domain2prefix(config=config), config.date
        )
        with open(
            f"{config.path}/{imagesfilename}", "w", encoding="utf-8"
        ) as imagesfile:
            for line in images:
                while 3 <= len(line) < 5:
                    line.append(
                        "False"
                    )  # At this point, make sure all lines have 5 elements
                filename, url, uploader, size, sha1 = line
                print(line, end="\r")
                imagesfile.write(
                    filename
                    + "\t"
                    + url
                    + "\t"
                    + uploader
                    + "\t"
                    + str(size)
                    + "\t"
                    + str(sha1)
                    # sha1 or size may be `False` if file is missing, so convert bool to str
                    + "\n"
                )
            imagesfile.write("--END--")
        print("Image filenames and URLs saved at...", imagesfilename)

    @staticmethod
    def curateImageURL(config: Config = None, url=""):
        """Returns an absolute URL for an image, adding the domain if missing"""

        if config.index:
            # remove from :// (http or https) until the first / after domain
            domainalone = (
                config.index.split("://")[0]
                + "://"
                + config.index.split("://")[1].split("/")[0]
            )
        elif config.api:
            domainalone = (
                config.api.split("://")[0]
                + "://"
                + config.api.split("://")[1].split("/")[0]
            )
        else:
            print("ERROR: no index nor API")
            sys.exit()

        if url.startswith("//"):  # Orain wikifarm returns URLs starting with //
            url = f'{domainalone.split("://")[0]}:{url}'
        elif url[0] == "/" or (
            not url.startswith("http://") and not url.startswith("https://")
        ):
            if url[0] == "/":  # slash is added later
                url = url[1:]
            # concat http(s) + domain + relative url
            url = f"{domainalone}/{url}"
        url = undoHTMLEntities(text=url)
        # url = urllib.parse.unquote(url) #do not use unquote with url, it break some
        # urls with odd chars
        url = re.sub(" ", "_", url)

        return url
