import datetime
import os
import re
import shutil
import sys
import time
import urllib.parse
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Union

import requests

from wikiteam3.dumpgenerator.api import get_JSON, handle_StatusCode
from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.dumpgenerator.config import Config, OtherConfig
from wikiteam3.dumpgenerator.dump.image.html_regexs import R_NEXT, REGEX_CANDIDATES
from wikiteam3.dumpgenerator.exceptions import FileSha1Error, FileSizeError
from wikiteam3.dumpgenerator.log import log_error
from wikiteam3.dumpgenerator.version import getVersion
from wikiteam3.utils.identifier import url2prefix_from_config
from wikiteam3.utils.monkey_patch import SessionMonkeyPatch
from wikiteam3.utils.util import clean_HTML, int_or_zero, sha1bytes, sha1sum, space, underscore, undo_HTML_entities

NULL = "null"
""" NULL value for image metadata """
FILENAME_LIMIT = 240
""" Filename not be longer than 240 **bytes**. (MediaWiki r98430 2011-09-29) """
STDOUT_IS_TTY = sys.stdout and sys.stdout.isatty()


WBM_EARLIEST = 1
WBN_LATEST = 2
WBM_BEST = 3


def check_response(r: requests.Response) -> None:
    if r.headers.get("cf-polished", ""):
        raise RuntimeError("Found cf-polished header in response, use --bypass-cdn-image-compression to bypass it")

class Image:

    @staticmethod
    def generate_image_dump(config: Config, other: OtherConfig, images: List[List],
                            session: requests.Session):
        """ Save files and descriptions using a file list """

        image_timestamp_intervals = None
        if other.image_timestamp_interval:
            image_timestamp_intervals = other.image_timestamp_interval.split("/")
            assert len(image_timestamp_intervals) == 2
            image_timestamp_intervals = [
                datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
                for x in image_timestamp_intervals]

        print("Retrieving images...")
        images_dir = Path(config.path) / "images"
        images_mismatch_dir = Path(config.path) / "images_mismatch"
        [os.makedirs(dir_, exist_ok=True) or print(f'Creating "{dir_}" directory')
         for dir_ in (images_dir, images_mismatch_dir) if not dir_.exists()]

        c_savedImageFiles = 0
        c_savedMismatchImageFiles = 0
        c_wbm_speedup_files = 0


        def delete_mismatch_image(filename_underscore: str) -> bool:
            """
            Delete mismatch image (in `images_mismatch` directory)
            
            return True if file is deleted, False if file not exists
            """
            assert filename_underscore == underscore(filename_underscore)

            if os.path.exists(images_mismatch_dir / filename_underscore):
                os.remove(images_mismatch_dir / filename_underscore)
                return True
            return False


        def modify_params(params: Optional[Dict] = None) -> Dict:
            """ bypass Cloudflare Polish (image optimization) """
            if params is None:
                params = {}
            if other.bypass_cdn_image_compression is True:
                # bypass Cloudflare Polish (image optimization)
                # <https://developers.cloudflare.com/images/polish/>
                params["_wiki_t"] = int(time.time()*1000)
                params["_wikiteam3_nocdn"] = "init_req" # this value will be changed on hard retry

            return params
        
        def modify_headers(headers: Optional[Dict] = None) -> Dict:
            """ add HTTP Referer header """
            if headers is None:
                headers = {}
            if other.add_referer_header:
                url = config.index if config.index else config.api
                parsed_url = urllib.parse.urlparse(
                    other.add_referer_header
                    if other.add_referer_header != "auto"
                    else url
                )

                headers["Referer"] = f"{parsed_url.scheme}://{parsed_url.netloc}/"

            return headers
            

        patch_sess = SessionMonkeyPatch(session=session, config=config, hard_retries=other.hard_retries)
        patch_sess.hijack()

        ia_session = requests.Session()
        ia_session.headers.update({"User-Agent": f"wikiteam3/{getVersion()}"})

        skip_to_filename = underscore('') # TODO: use this

        while images:
            filename_raw, url_raw, uploader_raw, size, sha1, timestamp = images.pop(0) # reduce memory usage by poping
            filename_underscore = underscore(filename_raw)
            # uploader_underscore = space(uploader_raw)

            # https://github.com/saveweb/wikiteam3/issues/52
            # --- Fandom PNG skip logic when resuming ---
            is_fandom = (
                "fandom.com" in (config.api or config.index) and
                "static.wikia.nocookie.net" in url_raw
            )
            is_pic = filename_underscore.lower().endswith(('.png', '.jpg', '.jpeg'))
            mismatch_file = (Path(config.path) / "images_mismatch" / filename_underscore)
            if is_fandom and is_pic and mismatch_file.is_file():
                print(f"Skipping Fandom PNG/JPG (already in images_mismatch): {filename_underscore}")
                continue
            # --- end skip logic ---

            if skip_to_filename and skip_to_filename != filename_underscore:
                print(f"    {filename_underscore}", end="\r")
                continue
            else:
                skip_to_filename = ''

            to_download = True

            if image_timestamp_intervals:
                if timestamp == NULL:
                    print(f"    {filename_underscore}|timestamp is unknown: {NULL}, downloading anyway...")
                else:
                    if not (
                        image_timestamp_intervals[0]
                        <= datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                        <= image_timestamp_intervals[1]
                    ):
                        print(f"    timestamp {timestamp} is not in interval {other.image_timestamp_interval}: {filename_underscore}")
                        continue
                    else:
                        print(f"    timestamp {timestamp} is in interval {other.image_timestamp_interval}: {filename_underscore}")

            # saving file
            if filename_underscore != urllib.parse.unquote(filename_underscore):
                print(f"WARNING:    {filename_underscore}|filename may not be unquoted: {filename_underscore}")
            if len(filename_underscore.encode('utf-8')) > FILENAME_LIMIT:
                log_error(
                    config=config, to_stdout=True,
                    text=f"Filename is too long(>{FILENAME_LIMIT} bytes), skipping: '{filename_underscore}'",
                )
                # TODO: hash as filename instead of skipping
                continue

            filepath_space = images_dir / space(filename_underscore)
            filepath_underscore = images_dir / filename_underscore

            if filepath_space.is_file():
                # rename file to underscore
                shutil.move(filepath_space, filepath_underscore)

            # check if file already exists in 'images' dir and has the same size and sha1
            if ((size != NULL
                and filepath_underscore.is_file()
                and os.path.getsize(filepath_underscore) == int(size)
                and sha1sum(filepath_underscore) == sha1)
            or (sha1 == NULL and filepath_underscore.is_file())): 
            # sha1 is NULL if file not in original wiki (probably deleted,
            # you will get a 404 error if you try to download it)
                c_savedImageFiles += 1
                to_download = False
                print_msg=f"    {c_savedImageFiles}|sha1 matched: {filename_underscore}"
                print(print_msg[0:70], end="\r")
                if sha1 == NULL:
                    log_error(config=config, to_stdout=True,
                        text=f"sha1 is {NULL} for {filename_underscore}, file may not in wiki site (probably deleted). "
                    )
            else:
                # Delay(config=config, delay=config.delay + random.uniform(0, 1))
                url = url_raw

                r: Optional[requests.Response] = None
                if other.ia_wbm_booster:
                    def get_ia_wbm_response() -> Optional[requests.Response]:
                        """ Get response from Internet Archive Wayback Machine
                        return None if not found / failed """
                        if other.ia_wbm_booster in (WBM_EARLIEST, WBN_LATEST):
                            ia_timestamp = other.ia_wbm_booster
                        elif other.ia_wbm_booster == WBM_BEST:
                            if timestamp != NULL:
                                ia_timestamp = [x for x in timestamp if x.isdigit()][0:8]
                                ia_timestamp = "".join(ia_timestamp)
                            else:
                                print(f"ia_wbm_booster:    timestamp is {NULL}, use latest timestamp")
                                ia_timestamp = 2
                        else:
                            raise ValueError(f"ia_wbm_booster is {other.ia_wbm_booster}, but it should be 0, 1, 2 or 3")

                        available_api = "http://archive.org/wayback/available"
                        # TODO: cdx_api = "http://web.archive.org/cdx/search/cdx"
                        snap_url = f"https://web.archive.org/web/{ia_timestamp}id_/{url}"

                        try:
                            _r = ia_session.get(available_api, params={"url": url}, headers={"User-Agent": "wikiteam3"},
                                            timeout=10)
                            if _r.status_code == 429:
                                raise Warning("IA API rate limit exceeded (HTTP 429)")
                            _r.raise_for_status()
                            api_result = _r.json()
                            if api_result["archived_snapshots"]:
                                r = ia_session.get(url=snap_url, allow_redirects=True)
                                # r.raise_for_status()
                            else:
                                r = None
                        except Exception as e:
                            print("ia_wbm_booster:",e)
                            r = None

                        return r
                    r = get_ia_wbm_response()

                    # verify response
                    if r and r.status_code != 200:
                        r = None
                    elif r and size != NULL and len(r.content) != int(size): # and r.status_code == 200:
                        # FileSizeError
                        # print(f"WARNING:    {filename_unquoted} size should be {size}, but got {len(r.content)} from WBM, use original url...")
                        r = None

                    if r is not None:
                        c_wbm_speedup_files += 1


                if r is None:
                    Delay(config=config)
                    try:
                        r = session.get(url=url, params=modify_params(), headers=modify_headers(), allow_redirects=True)
                    except requests.exceptions.ContentDecodingError as e:
                        # Workaround for https://fedoraproject.org/w/uploads/5/54/Duffy-f12-banner.svgz
                        # (see also https://cdn.digitaldragon.dev/wikibot/jobs/b0f52fc3-927b-4d14-aded-89a2795e8d4d/log.txt)
                        # server response with "Content-Encoding: gzip" (or other) but the transfer is not encoded/compressed actually
                        # If this workround can't get the original file, the file will be thrown to images_mismatch dir, not too bad :)
                        log_error(
                            config, to_stdout=True,
                            text=f"{e} when downloading {filename_underscore} with URL {url} . "
                            "Retrying with 'Accept-Encoding: identity' header and no transfer auto-decompresion..."
                        )
                        _headers = modify_headers()
                        _headers["Accept-Encoding"] = "identity"
                        r = session.get(url=url, params=modify_params(), headers=_headers, allow_redirects=True, stream=True)
                        r._content = r.raw.read()

                    check_response(r)

                    # a trick to get original file (fandom)
                    ori_url = url
                    if "fandom.com" in config.api \
                        and "static.wikia.nocookie.net" in url \
                        and "?" in url \
                        and (
                               sha1 != NULL and sha1bytes(r.content) != sha1
                            or size != NULL and len(r.content) != int(size)
                        ):
                        ori_url = url + "&format=original"
                        Delay(config=config)
                        r = session.get(url=ori_url, params=modify_params(), headers=modify_headers(), allow_redirects=True)
                        check_response(r)

                    # Try to fix a broken HTTP to HTTPS redirect
                    original_url_redirected: bool = r.url in (url, ori_url)
                    if r.status_code == 404 and original_url_redirected:
                        print(f"WARNING: {url} broken (404), trying to fix it...")
                        if (
                            url_raw.startswith("http://")
                            and url.startswith("https://")
                        ):
                            url = "https://" + url_raw.split("://")[1]
                            # print 'Maybe a broken http to https redirect, trying ', url
                            r = session.get(url=url, params=modify_params(), headers=modify_headers(), allow_redirects=True)
                            check_response(r)

                if r.status_code == 200:
                    try:
                        if (sha1 == NULL and size == NULL) \
                            or (
                                    (sha1 == NULL or sha1bytes(r.content) == sha1)
                                and (size == NULL or len(r.content) == int(size) )
                            ):
                            try:
                                with open(filepath_underscore, "wb") as imagefile:
                                    imagefile.write(r.content)
                            except KeyboardInterrupt:
                                if filepath_underscore.is_file():
                                    os.remove(filepath_underscore)
                                raise
                            delete_mismatch_image(filename_underscore) # delete previous mismatch image
                            c_savedImageFiles += 1
                        else:
                            if size != NULL and len(r.content) != int(size):
                                raise FileSizeError(file=filename_underscore,
                                                    got_size=len(r.content),
                                                    excpected_size=int(size),
                                                    online_url=url)
                            elif sha1bytes(r.content) != sha1:
                                raise FileSha1Error(file=filename_underscore, excpected_sha1=sha1)
                            else:
                                raise RuntimeError("Unknown error")
                    except OSError:
                        log_error(
                            config=config, to_stdout=True,
                            text=f"File '{filepath_underscore}' could not be created by OS",
                        )
                        continue
                    except (FileSha1Error, FileSizeError) as e:
                        log_error(
                            config=config, to_stdout=True,
                            text=f"{e}. saving to images_mismatch dir",
                        )
                        with open(images_mismatch_dir / filename_underscore, "wb") as imagefile:
                            imagefile.write(r.content)
                        c_savedMismatchImageFiles += 1
                        continue

                    if timestamp != NULL:
                        # try to set file timestamp (mtime)
                        try:
                            mtime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").timestamp()
                            atime = os.stat(filepath_underscore).st_atime
                            # atime is not modified
                            os.utime(filepath_underscore, times=(atime, mtime))
                            # print(atime, mtime)
                        except Exception as e:
                            print("Error setting file timestamp:", e)
                else:
                    log_error(
                        config=config, to_stdout=True,
                        text=f"Failed to download '{filename_underscore}' with URL '{url}' due to HTTP '{r.status_code}', skipping"
                    )

            if not to_download: # skip printing
                continue
            if STDOUT_IS_TTY:
                print_msg = f"              | {len(images)}=>{filename_underscore[0:50]}"
                print(print_msg, " "*(73 - len(print_msg)), end="\r")
            else:
                print(f'{len(images)}=>{filename_underscore}')

        # NOTE: len(images) == 0 here

        patch_sess.release()
        print(f"Downloaded {c_savedImageFiles} files to 'images' dir")
        print(f"Downloaded {c_savedMismatchImageFiles} files to 'images_mismatch' dir")
        if other.ia_wbm_booster and c_wbm_speedup_files:
            print(f"(WBM speedup: {c_wbm_speedup_files} files)")


    @staticmethod
    def get_image_names(config: Config, session: requests.Session):
        """Get list of image names"""

        print(")Retrieving image filenames")
        images = []
        if config.api:
            print("Using API to retrieve image names...")
            images = Image.get_image_names_API(config=config, session=session)
        elif config.index:
            print("Using index.php (Special:Imagelist) to retrieve image names...")
            images = Image.get_image_names_scraper(config=config, session=session)

        print(f"Sorting image filenames ({len(images)} images)...")
        images.sort()
        print("Done")

        return images


    @staticmethod
    def get_image_names_scraper(config: Config, session: requests.Session):
        """Retrieve file list: filename, url, uploader"""

        images = []
        limit = 5000
        retries = config.retries
        offset = None
        while offset or len(images) == 0:
            # 5000 overload some servers, but it is needed for sites like this with
            # no next links
            # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
            params = {"title": "Special:Imagelist", "limit": limit, "dir": "prev", "offset": offset}
            r = session.post(
                url=config.index,
                params=params,
                timeout=30,
            )
            raw = r.text
            Delay(config=config)
            # delicate wiki
            if re.search(
                r"(?i)(allowed memory size of \d+ bytes exhausted|Call to a member function getURL)",
                raw,
            ):
                if limit > 10:
                    print(f"Error: listing {limit} images in a chunk is not possible, trying tiny chunks")
                    limit = limit // 10
                    continue
                elif retries > 0:  # waste retries, then exit
                    retries -= 1
                    print("Retrying...")
                    continue
                else:
                    raise RuntimeError("retries exhausted")

            raw = clean_HTML(raw)

            # Select the regexp that returns more results
            best_matched = 0
            regexp_best = None
            for regexp in REGEX_CANDIDATES:
                _count = len(re.findall(regexp, raw))
                if _count > best_matched:
                    best_matched = _count
                    regexp_best = regexp
            assert regexp_best is not None, "Could not find a proper regexp to parse the HTML"
            m = re.compile(regexp_best).finditer(raw)

            # Iter the image results
            for i in m:
                url = i.group("url")
                url = Image.curate_image_URL(config=config, url=url)

                filename = i.group("filename")
                filename = undo_HTML_entities(text=filename)
                filename = urllib.parse.unquote(filename)

                uploader = i.group("uploader")
                uploader = undo_HTML_entities(text=uploader)
                uploader = urllib.parse.unquote(uploader)

                # timestamp = i.group("timestamp")
                # print("    %s" % (timestamp))

                size = NULL # size not accurate
                sha1 = NULL # sha1 not available
                timestamp = NULL # date formats are difficult to parse
                images.append([
                    underscore(filename), url, space(uploader),
                    size, sha1, timestamp,
                ])
                # print (filename, url)

            if re.search(R_NEXT, raw):
                new_offset = re.findall(R_NEXT, raw)[0]
                # Avoid infinite loop
                if new_offset != offset:
                    offset = new_offset
                    retries += 5  # add more retries if we got a page with offset
                else:
                    print("Warning: offset is not changing")
                    offset = ""
            else:
                print("INFO: no next link found, we may have reached the end")
                offset = ""

        if len(images) == 0:
            print("Warning: no images found")
        elif len(images) == limit:
            print(f"Warning: the number of images is equal to the limit parameter ({limit}), there may be more images")
        else:
            print(f"    Found {len(images)} images")

        images.sort()
        return images

    @staticmethod
    def get_image_names_API(config: Config, session: requests.Session):
        """Retrieve file list: filename, url, uploader, size, sha1"""
        use_oldAPI = False
        # # Commented by @yzqzss:
        # https://www.mediawiki.org/wiki/API:Allpages
        # API:Allpages requires MW >= 1.8
        # API:Allimages requires MW >= 1.13

        aifrom = "!"
        images = []
        countImages = 0
        while aifrom:
            print(f'Using API:Allimages to get the list of images, {len(images)} images found so far...', end='\r')
            params = {
                "action": "query",
                "list": "allimages",
                "aiprop": "url|user|size|sha1|timestamp",
                "aifrom": aifrom,
                "format": "json",
                "ailimit": config.api_chunksize,
            }
            # FIXME Handle HTTP Errors HERE
            r = session.get(url=config.api, params=params, timeout=30)
            handle_StatusCode(r)
            jsonimages = get_JSON(r)
            Delay(config=config)

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
                print(countImages, aifrom[0:30]+" "*(60-len(aifrom[0:30])),end="\r")

                for image in jsonimages["query"]["allimages"]:
                    image: Dict

                    url = image["url"]
                    url = Image.curate_image_URL(config=config, url=url)

                    filename = image.get("name", None)
                    if filename is None:
                        if  (
                            ".wikia." in config.api or ".fandom.com" in config.api
                        ):
                            filename = urllib.parse.unquote(
                                url.split("/")[-3]
                            )
                        else:
                            filename = urllib.parse.unquote(
                                url.split("/")[-1]
                            )

                    if "%u" in filename:
                        warnings.warn(
                            f"Filename {filename} may contains unquoted URL characters, please review it manually. FILENAME: {filename} URL:{url}",
                            UnicodeWarning,
                        )

                    uploader = image.get("user", "Unknown")
                    size: Union[bool,int] = image.get("size", NULL)
                    
                    # size or sha1 is not always available (e.g. https://wiki.mozilla.org/index.php?curid=20675)
                    sha1: Union[bool,str] = image.get("sha1", NULL)
                    timestamp = image.get("timestamp", NULL)
                    images.append([underscore(filename), url, space(uploader), size, sha1, timestamp])
            else:
                use_oldAPI = True
                break

        if use_oldAPI:
            print("    API:Allimages not available. Using API:Allpages generator instead.")
            gapfrom = "!"
            images = []
            while gapfrom:
                # Some old APIs doesn't have allimages query
                # In this case use allpages (in nm=6) as generator for imageinfo
                # Example:
                # http://minlingo.wiki-site.com/api.php?action=query&generator=allpages&gapnamespace=6
                # &gaplimit=500&prop=imageinfo&iiprop=user|url&gapfrom=!
                params = {
                    "action": "query",
                    "generator": "allpages",
                    "gapnamespace": 6,
                    "gaplimit": config.api_chunksize, # The value must be between 1 and 500.
                                    # TODO: Is it OK to set it higher, for speed?
                    "gapfrom": gapfrom,
                    "prop": "imageinfo",
                    "iiprop": "url|user|size|sha1|timestamp",
                    "format": "json",
                }
                # FIXME Handle HTTP Errors HERE
                r = session.get(url=config.api, params=params, timeout=30)
                handle_StatusCode(r)
                jsonimages = get_JSON(r)
                Delay(config=config)

                if "query" in jsonimages:
                    countImages += len(jsonimages["query"]["pages"])
                    print(countImages, gapfrom[0:30]+" "*(60-len(gapfrom[0:30])),end="\r")

                    gapfrom = ""

                    # all moden(at 20221231) wikis return 'continue' instead of 'query-continue'
                    if (
                        "continue" in jsonimages
                        and "gapcontinue" in jsonimages["continue"]
                    ):
                        gapfrom = jsonimages["continue"]["gapcontinue"]
                    
                    # prior to mw1.21, that raw continuation (query-continue) was the only option. 
                    elif (
                        "query-continue" in jsonimages
                        and "allpages" in jsonimages["query-continue"]
                    ):
                        if "gapfrom" in jsonimages["query-continue"]["allpages"]:
                            gapfrom = jsonimages["query-continue"]["allpages"][
                                "gapfrom"
                            ]


                    # print (gapfrom)
                    # print (jsonimages['query'])

                    for image, props in jsonimages["query"]["pages"].items():
                        url = props["imageinfo"][0]["url"]
                        url = Image.curate_image_URL(config=config, url=url)

                        filename = ":".join(props["title"].split(":")[1:])

                        uploader = props["imageinfo"][0]["user"]
                        size = props.get("imageinfo")[0].get("size", NULL)
                        sha1 = props.get("imageinfo")[0].get("sha1", NULL)
                        timestamp = props.get("imageinfo")[0].get("timestamp", NULL)
                        images.append([underscore(filename), url, space(uploader), size, sha1, timestamp])
                else:
                    # if the API doesn't return query data, then we're done
                    break

        if len(images) == 1:
            print("    Found 1 image")
        else:
            print("    Found %d images" % (len(images)))

        return images


    @staticmethod
    def save_image_names(config: Config, other: OtherConfig, images: List[List]):
        """Save image list in a file, including filename, url, uploader and other metadata"""

        images_filename = "{}-{}-images.txt".format(
            url2prefix_from_config(config=config), config.date
        )
        images_file = open(
            "{}/{}".format(config.path, images_filename), "w", encoding="utf-8"
        )

        c_images_size = 0
        for line in images:
            while 3 <= len(line) < 6:
                line.append(NULL) # At this point, make sure all lines have 5 elements
            filename, url, uploader, size, sha1, timestamp = line

            assert " " not in filename, "Filename contains space, it should be underscored"
            assert "_" not in uploader, "Uploader contains underscore, it should be spaced"

            # print(line,end='\r')
            c_images_size += int_or_zero(size)

            images_file.write(
                filename + "\t" + url + "\t" + uploader
                + "\t" + (str(size) if size else NULL)
                + "\t" + (str(sha1) if sha1 else NULL) # sha1 or size may be NULL
                + "\t" + (timestamp if timestamp else NULL)
                + "\n"
            )
        images_file.write("--END--\n")
        images_file.close()

        print("Image metadata (images.txt) saved at:", images_filename)
        print(f"Estimated size of all images (images.txt): {c_images_size} bytes ({c_images_size/1024/1024/1024:.2f} GiB)")

        try:
            assert len(images) <= other.assert_max_images if other.assert_max_images is not None else True
            print(f"--assert_max_images: {other.assert_max_images}, passed")
            assert c_images_size <= other.assert_max_images_bytes if other.assert_max_images_bytes is not None else True
            print(f"--assert_max_images_bytes: {other.assert_max_images_bytes}, passed")
        except AssertionError:
            import traceback
            traceback.print_exc()
            sys.exit(45)


    @staticmethod
    def curate_image_URL(config: Config, url: str):
        """Returns an absolute URL for an image, adding the domain if missing"""

        if config.index:
            # remove from :// (http or https) until the first / after domain
            domainalone = (
                config.index.split("://")[0]
                + "://"
                + config.index.split("://")[1].split("/")[0]
            )
        elif  config.api:
            domainalone = (
                config.api.split("://")[0]
                + "://"
                + config.api.split("://")[1].split("/")[0]
            )
        else:
            print("ERROR: no index nor API")
            sys.exit(1)
            return # useless but linting is happy

        if url.startswith("//"):  # Orain wikifarm returns URLs starting with //
            url = "{}:{}".format(domainalone.split("://")[0], url)
        # is it a relative URL?
        elif url[0] == "/" or (
            not url.startswith("http://") and not url.startswith("https://")
        ):
            if url[0] == "/":  # slash is added later
                url = url[1:]
            # concat http(s) + domain + relative url
            url = f"{domainalone}/{url}"
        url = undo_HTML_entities(text=url)
        # url = urllib.parse.unquote(url) #do not use unquote with url, it break some
        # urls with odd chars

        return underscore(url)
