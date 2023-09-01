#!/usr/bin/env python3

# Copyright (C) 2011-2016 WikiTeam
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import getopt
import hashlib
import os
import re
import shutil
import subprocess
import time
import urllib.parse
from io import BytesIO
from pathlib import Path

import requests
from internetarchive import get_item

from wikiteam3.dumpgenerator.config import Config
from wikiteam3.utils import domain2prefix, getUserAgent

# Nothing to change below
convertlang = {
    "ar": "Arabic",
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "ja": "Japanese",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
}


def log(logfile, wiki, dump, msg):
    logfile.write(f"\n{wiki};{dump.name};{msg}")


def read_ia_keys(config):
    with open(config.keysfile) as f:
        key_lines = f.readlines()

        accesskey = key_lines[0].strip()
        secretkey = key_lines[1].strip()

        return {"access": accesskey, "secret": secretkey}


# We have to use md5 because the internet archive API doesn't provide
# sha1 for all files.
def file_md5(path):
    buffer = bytearray(65536)
    view = memoryview(buffer)
    digest = hashlib.md5()

    with open(path, mode="rb") as f:
        while True:
            if n := f.readinto(buffer):
                digest.update(view[:n])

            else:
                break

    return digest.hexdigest()


def upload(wikis, logfile, config={}, uploadeddumps=[]):
    ia_keys = read_ia_keys(config)

    headers = {"User-Agent": getUserAgent()}
    dumpdir = Path(config.wikidump_dir)

    for wiki in wikis:
        print("#" * 73)
        print("# Uploading", wiki)
        print("#" * 73)
        wiki = wiki.lower()
        try:
            prefix = domain2prefix(Config(api=wiki))
        except KeyError:
            print("ERROR: could not produce the prefix for %s" % wiki)

        wikiname = prefix.split("-")[0]
        dumps = []
        for f in dumpdir.iterdir():
            if f.name.startswith("%s-" % (wikiname)) and (
                f.name.endswith("-wikidump.7z") or f.name.endswith("-history.xml.7z")
            ):
                print("%s found" % f)
                dumps.append(f)
                # Re-introduce the break here if you only need to upload one file
                # and the I/O is too slow
                # break

        c = 0
        identifier = "wiki-" + wikiname
        item = get_item(identifier)
        first_item_exists = item.exists
        for dump in dumps:
            wikidate = dump.name.split("-")[1]
            if first_item_exists and config.append_date and not config.admin:
                identifier = "wiki-" + wikiname + "-" + wikidate
                item = get_item(identifier)
            if dump.name in uploadeddumps:
                if config.prune_directories:
                    rmpath = dumpdir / f"{wikiname}-{wikidate}-wikidump"
                    if rmpath.exists():
                        shutil.rmtree(rmpath)
                        print(f"DELETED {rmpath.name}/")

                if config.prune_wikidump and dump.name.endswith("wikidump.7z"):
                    # Simplistic quick&dirty check for the presence of this file in the item
                    print("Checking content in previously uploaded files")
                    dumphash = file_md5(dump)

                    if dumphash in map(lambda x: x["md5"], item.files):
                        log(logfile, wiki, dump, "verified")
                        dump.unlink()
                        print("DELETED " + str(dump))
                        print("%s was uploaded before, skipping..." % (dump.name))
                        continue
                    else:
                        print("ERROR: The online item misses " + dump.name)
                        log(logfile, wiki, dump, "missing")
                        # We'll exit this if and go upload the dump
                else:
                    print("%s was uploaded before, skipping..." % (dump.name))
                    continue
            else:
                print("%s was not uploaded before" % dump.name)

            time.sleep(0.1)
            wikidate_text = wikidate[0:4] + "-" + wikidate[4:6] + "-" + wikidate[6:8]
            print(wiki, wikiname, wikidate, dump)

            # Does the item exist already?
            ismissingitem = not item.exists

            # Logo path
            logourl = ""

            if ismissingitem or config.update:
                # get metadata from api.php
                # first sitename and base url
                params = {"action": "query", "meta": "siteinfo", "format": "xml"}
                try:
                    r = requests.get(url=wiki, params=params, headers=headers)
                    if r.status_code < 400:
                        xml = r.text
                except requests.exceptions.ConnectionError as e:
                    pass

                sitename = ""
                baseurl = ""
                lang = ""
                try:
                    sitename = re.findall(r"sitename=\"([^\"]+)\"", xml)[0]
                except:
                    pass
                try:
                    baseurl = re.findall(r"base=\"([^\"]+)\"", xml)[0]
                except:
                    pass
                try:
                    lang = re.findall(r"lang=\"([^\"]+)\"", xml)[0]
                except:
                    pass

                if not sitename:
                    sitename = wikiname
                if not baseurl:
                    baseurl = re.sub(r"(?im)/api\.php", r"", wiki)
                # Convert protocol-relative URLs
                baseurl = re.sub("^//", "https://", baseurl)
                if lang:
                    lang = (
                        convertlang[lang.lower()]
                        if (lang.lower() in convertlang)
                        else lang.lower()
                    )

                # now copyright info from API
                params = {
                    "action": "query",
                    "meta": "siteinfo",
                    "siprop": "general|rightsinfo",
                    "format": "xml",
                }
                xml = ""
                try:
                    r = requests.get(url=wiki, params=params, headers=headers)
                    if r.status_code < 400:
                        xml = r.text
                except requests.exceptions.ConnectionError as e:
                    pass

                rightsinfourl = ""
                rightsinfotext = ""
                try:
                    rightsinfourl = re.findall(r"rightsinfo url=\"([^\"]+)\"", xml)[0]
                    rightsinfotext = re.findall(r"text=\"([^\"]+)\"", xml)[0]
                except:
                    pass

                raw = ""
                try:
                    r = requests.get(url=baseurl, headers=headers)
                    if r.status_code < 400:
                        raw = r.text
                except requests.exceptions.ConnectionError as e:
                    pass

                # or copyright info from #footer in mainpage
                if baseurl and not rightsinfourl and not rightsinfotext:
                    print("INFO: Getting license from the HTML")
                    rightsinfotext = ""
                    rightsinfourl = ""
                    try:
                        rightsinfourl = re.findall(
                            r"<link rel=\"copyright\" href=\"([^\"]+)\" />", raw
                        )[0]
                    except:
                        pass
                    try:
                        rightsinfotext = re.findall(
                            r"<li id=\"copyright\">([^\n\r]*?)</li>", raw
                        )[0]
                    except:
                        pass
                    if rightsinfotext and not rightsinfourl:
                        rightsinfourl = baseurl + "#footer"
                try:
                    logourl = re.findall(
                        r'p-logo["\'][^>]*>\s*<a [^>]*background-image:\s*(?:url\()?([^;)"]+)',
                        raw,
                    )
                    if logourl:
                        logourl = logourl[0]
                    else:
                        logourl = re.findall(
                            r'"wordmark-image">[^<]*<a[^>]*>[^<]*<img src="([^"]+)"',
                            raw,
                        )[0]
                    if "http" not in logourl:
                        # Probably a relative path, construct the absolute path
                        logourl = urllib.parse.urljoin(wiki, logourl)
                except:
                    pass

                # retrieve some info from the wiki
                wikititle = "Wiki - %s" % (sitename)  # Wiki - ECGpedia
                wikidesc = (
                    '<a href="%s">%s</a> dumped with <a href="https://github.com/mediawiki-client-tools/mediawiki-dump-generator/" rel="nofollow">MediaWiki Dump Generator</a> (aka WikiTeam3) tools.'
                    % (baseurl, sitename)
                )  # "<a href=\"http://en.ecgpedia.org/\" rel=\"nofollow\">ECGpedia,</a>: a free electrocardiography (ECG) tutorial and textbook to which anyone can contribute, designed for medical professionals such as cardiac care nurses and physicians. Dumped with <a href=\"https://github.com/WikiTeam/wikiteam\" rel=\"nofollow\">WikiTeam</a> tools."
                wikikeys = [
                    "wiki",
                    "wikiteam",
                    "wikiteam3",
                    "mediawiki-dump-generator",
                    "MediaWikiDumpGenerator",
                    "MediaWiki",
                    sitename,
                    wikiname,
                ]  # ecg; ECGpedia; wiki; wikiteam; MediaWiki

                if not rightsinfourl and not rightsinfotext:
                    wikikeys.append("unknowncopyright")
                if "www.fandom.com" in rightsinfourl and "/licensing" in rightsinfourl:
                    # Link the default license directly instead
                    rightsinfourl = "https://creativecommons.org/licenses/by-sa/3.0/"
                wikilicenseurl = (
                    rightsinfourl  # http://creativecommons.org/licenses/by-nc-sa/3.0/
                )
                wikirights = rightsinfotext  # e.g. http://en.ecgpedia.org/wiki/Frequently_Asked_Questions : hard to fetch automatically, could be the output of API's rightsinfo if it's not a usable licenseurl or "Unknown copyright status" if nothing is found.

                wikiurl = wiki  # we use api here http://en.ecgpedia.org/api.php
            else:
                print("Item already exists.")
                lang = "foo"
                wikititle = "foo"
                wikidesc = "foo"
                wikikeys = "foo"
                wikilicenseurl = "foo"
                wikirights = "foo"
                wikiurl = "foo"

            if c == 0:
                # Item metadata
                md = {
                    "mediatype": "web",
                    "collection": config.collection,
                    "title": wikititle,
                    "description": wikidesc,
                    "language": lang,
                    "last-updated-date": wikidate_text,
                    "subject": "; ".join(
                        wikikeys
                    ),  # Keywords should be separated by ; but it doesn't matter much; the alternative is to set one per field with subject[0], subject[1], ...
                    "licenseurl": wikilicenseurl
                    and urllib.parse.urljoin(wiki, wikilicenseurl),
                    "rights": wikirights,
                    "originalurl": wikiurl,
                }

            # Upload files and update metadata
            try:
                item.upload(
                    str(dump),
                    metadata=md,
                    access_key=ia_keys["access"],
                    secret_key=ia_keys["secret"],
                    verbose=True,
                    queue_derive=False,
                )
                retry = 20
                while not item.exists and retry > 0:
                    retry -= 1
                    print(
                        'Waitting for item "%s" to be created... (%s)'
                        % (identifier, retry)
                    )
                    time.sleep(10)
                    item = get_item(identifier)

                # Update metadata
                r = item.modify_metadata(
                    md, access_key=ia_keys["access"], secret_key=ia_keys["secret"]
                )
                if r.status_code != 200:
                    print("Error when updating metadata")
                    print(r.status_code)
                    print(r.text)

                print(
                    "You can find it in https://archive.org/details/%s" % (identifier)
                )
                uploadeddumps.append(dump.name)
            except Exception as e:
                print(wiki, dump, "Error when uploading?")
                print(e)
            try:
                log(logfile, wiki, dump, "ok")
                if logourl:
                    logo = BytesIO(requests.get(logourl, timeout=10).content)
                    if ".png" in logourl:
                        logoextension = "png"
                    elif logourl.split("."):
                        logoextension = logourl.split(".")[-1]
                    else:
                        logoextension = "unknown"
                    logoname = "wiki-" + wikiname + "_logo." + logoextension
                    item.upload(
                        {logoname: logo},
                        access_key=ia_keys["access"],
                        secret_key=ia_keys["secret"],
                        verbose=True,
                    )
            except requests.exceptions.ConnectionError as e:
                print(wiki, dump, "Error when uploading logo?")
                print(e)

            c += 1


def main(params=[]):
    parser = argparse.ArgumentParser(
        """uploader.py

This script takes the filename of a list of wikis as argument and uploads their dumps to archive.org.
The list must be a text file with the wiki's api.php URLs, one per line.
Dumps must be in the same directory and follow the -wikidump.7z/-history.xml.7z format
as produced by launcher.py (explained in https://github.com/WikiTeam/wikiteam/wiki/Tutorial#Publishing_the_dump ).
You need a file named keys.txt with access and secret keys, in two different lines

Use --help to print this help."""
    )

    parser.add_argument("-pd", "--prune_directories", action="store_true")
    parser.add_argument("-pw", "--prune_wikidump", action="store_true")
    parser.add_argument("-a", "--admin", action="store_true")
    parser.add_argument("-c", "--collection", default="opensource")
    parser.add_argument("-wd", "--wikidump_dir", default=".")
    parser.add_argument("-u", "--update", action="store_true")
    parser.add_argument("-kf", "--keysfile", default="keys.txt")
    parser.add_argument("-lf", "--logfile", default=None)
    parser.add_argument("-d", "--append_date", action="store_true")
    parser.add_argument("listfile")
    config = parser.parse_args()
    if config.admin:
        config.collection = "wikiteam"
    uploadeddumps = []
    listfile = config.listfile
    try:
        uploadeddumps = [
            l.split(";")[1]
            for l in open("uploader-%s.log" % (listfile)).read().strip().splitlines()
            if len(l.split(";")) > 1
        ]
    except:
        pass

    if config.logfile is None:
        config.logfile = "uploader-" + Path(listfile).name + ".log"

    print("%d dumps uploaded previously" % (len(uploadeddumps)))
    wikis = open(listfile).read().strip().splitlines()

    with open(config.logfile, "a") as logfile:
        upload(wikis, logfile, config, uploadeddumps)


if __name__ == "__main__":
    main()
