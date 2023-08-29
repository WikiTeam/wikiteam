#!/usr/bin/env python3

# Copyright (C) 2018 WikiTeam developers
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

# Documentation for users: https://github.com/WikiTeam/wikiteam/wiki
# Documentation for developers: http://wikiteam.readthedocs.com
"""
# You need a file with access and secret keys, in two different lines
iakeysfilename = '%s/.iakeys' % (os.path.expanduser('~'))
if os.path.exists(iakeysfilename):
    accesskey = open(iakeysfilename, 'r').readlines()[0].strip()
    secretkey = open(iakeysfilename, 'r').readlines()[1].strip()
else:
    print('Error, no %s file with S3 keys for Internet Archive account' % (iakeysfilename))
    sys.exit()
"""
import csv
import datetime
import os
import random
import re
import subprocess
import sys
import time
import urllib.request

# from internetarchive import get_item

# Requirements:
# zip command (apt-get install zip)
# ia command (pip install internetarchive, and configured properly)


def saveURL(wikidomain="", url="", filename="", path="", overwrite=False, iteration=1):
    filename2 = f"{wikidomain}/{filename}"
    if path:
        filename2 = f"{wikidomain}/{path}/{filename}"
    if os.path.exists(filename2):
        if not overwrite:
            print(
                "Warning: file exists on disk. Skipping download. Force download with parameter --overwrite"
            )
            return
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)
    try:
        urllib.request.urlretrieve(url, filename2)
    except:
        sleep = 10  # seconds
        maxsleep = 30
        while sleep <= maxsleep:
            try:
                print(f"Error while retrieving: {url}")
                print(f"Retry in {sleep} seconds...")
                time.sleep(sleep)
                urllib.request.urlretrieve(url, filename2)
                return
            except:
                sleep *= 2
        print("Download failed")

    # sometimes wikispaces returns invalid data, redownload in that cases
    # only 'pages'. 'files' binaries are a pain to open and check
    if (os.path.exists(filename2) and "pages" in path) or (
        os.path.exists(filename2)
        and path == ""
        and filename2.split(".")[-1] in ["xml", "html", "csv"]
    ):
        sleep2 = 60 * iteration
        raw = ""
        try:
            with open(filename2, encoding="utf-8") as f:
                raw = f.read()
        except:
            with open(filename2, encoding="latin-1") as f:
                raw = f.read()
        if re.findall(r"(?im)<title>TES and THE Status</title>", raw):
            print(
                "Warning: invalid content. Waiting %d seconds and re-downloading"
                % (sleep2)
            )
            time.sleep(sleep2)
            saveURL(
                wikidomain=wikidomain,
                url=url,
                filename=filename,
                path=path,
                overwrite=overwrite,
                iteration=iteration + 1,
            )


def undoHTMLEntities(text=""):
    """Undo some HTML codes"""

    # i guess only < > & " ' need conversion
    # http://www.w3schools.com/html/html_entities.asp
    text = re.sub("&lt;", "<", text)
    text = re.sub("&gt;", ">", text)
    text = re.sub("&amp;", "&", text)
    text = re.sub("&quot;", '"', text)
    text = re.sub("&#039;", "'", text)

    return text


def convertHTML2Wikitext(wikidomain="", filename="", path=""):
    wikitext = ""
    wikitextfile = f"{wikidomain}/{path}/{filename}"
    if not os.path.exists(wikitextfile):
        print("Error retrieving wikitext, page is a redirect probably")
        return
    with open(wikitextfile) as f:
        wikitext = f.read()
    with open(wikitextfile, "w") as f:
        if m := re.findall(
            r'(?im)<div class="WikispacesContent WikispacesBs3">\s*<pre>',
            wikitext,
        ):
            try:
                wikitext = wikitext.split(m[0])[1].split("</pre>")[0].strip()
                wikitext = undoHTMLEntities(text=wikitext)
            except:
                pass
        f.write(wikitext)


def downloadPage(wikidomain="", wikiurl="", pagename="", overwrite=False):
    pagenameplus = re.sub(" ", "+", pagename)
    pagename_ = urllib.parse.quote(pagename)

    # page current revision (html & wikitext)
    pageurl = f"{wikiurl}/{pagename_}"
    filename = f"{pagenameplus}.html"
    print(f"Downloading page: {filename}")
    saveURL(
        wikidomain=wikidomain,
        url=pageurl,
        filename=filename,
        path="pages",
        overwrite=overwrite,
    )
    pageurl2 = f"{wikiurl}/page/code/{pagename_}"
    filename2 = f"{pagenameplus}.wikitext"
    print(f"Downloading page: {filename2}")
    saveURL(
        wikidomain=wikidomain,
        url=pageurl2,
        filename=filename2,
        path="pages",
        overwrite=overwrite,
    )
    convertHTML2Wikitext(wikidomain=wikidomain, filename=filename2, path="pages")

    # csv with page history
    csvurl = (
        f"{wikiurl}/page/history/{pagename_}?utable=WikiTablePageHistoryList&ut_csv=1"
    )
    csvfilename = f"{pagenameplus}.history.csv"
    print(f"Downloading page: {csvfilename}")
    saveURL(
        wikidomain=wikidomain,
        url=csvurl,
        filename=csvfilename,
        path="pages",
        overwrite=overwrite,
    )


def downloadFile(wikidomain="", wikiurl="", filename="", overwrite=False):
    filenameplus = re.sub(" ", "+", filename)
    filename_ = urllib.parse.quote(filename)

    # file full resolution
    fileurl = f"{wikiurl}/file/view/{filename_}"
    filename = filenameplus
    print(f"Downloading file: {filename}")
    saveURL(
        wikidomain=wikidomain,
        url=fileurl,
        filename=filename,
        path="files",
        overwrite=overwrite,
    )

    # csv with file history
    csvurl = f"{wikiurl}/file/detail/{filename_}?utable=WikiTablePageList&ut_csv=1"
    csvfilename = f"{filenameplus}.history.csv"
    print(f"Downloading file: {csvfilename}")
    saveURL(
        wikidomain=wikidomain,
        url=csvurl,
        filename=csvfilename,
        path="files",
        overwrite=overwrite,
    )


def downloadPagesAndFiles(wikidomain="", wikiurl="", overwrite=False):
    print(f"Downloading Pages and Files from {wikiurl}")
    # csv all pages and files
    csvurl = f"{wikiurl}/space/content?utable=WikiTablePageList&ut_csv=1"
    saveURL(wikidomain=wikidomain, url=csvurl, filename="pages-and-files.csv", path="")
    # download every page and file
    totallines = 0
    with open(f"{wikidomain}/pages-and-files.csv") as f:
        totallines = len(f.read().splitlines()) - 1
    with open(f"{wikidomain}/pages-and-files.csv") as csvfile:
        filesc = 0
        pagesc = 0
        print("This wiki has %d pages and files" % (totallines))
        rows = csv.reader(csvfile, delimiter=",", quotechar='"')
        for row in rows:
            if row[0] == "file":
                filesc += 1
                filename = row[1]
                downloadFile(
                    wikidomain=wikidomain,
                    wikiurl=wikiurl,
                    filename=filename,
                    overwrite=overwrite,
                )
            elif row[0] == "page":
                pagesc += 1
                pagename = row[1]
                downloadPage(
                    wikidomain=wikidomain,
                    wikiurl=wikiurl,
                    pagename=pagename,
                    overwrite=overwrite,
                )
            if (filesc + pagesc) % 10 == 0:
                print("  Progress: %d of %d" % ((filesc + pagesc), totallines))
        print("  Progress: %d of %d" % ((filesc + pagesc), totallines))
    print("Downloaded %d pages" % (pagesc))
    print("Downloaded %d files" % (filesc))


def downloadSitemap(wikidomain="", wikiurl="", overwrite=False):
    print("Downloading sitemap.xml")
    saveURL(
        wikidomain=wikidomain,
        url=wikiurl,
        filename="sitemap.xml",
        path="",
        overwrite=overwrite,
    )


def downloadMainPage(wikidomain="", wikiurl="", overwrite=False):
    print("Downloading index.html")
    saveURL(
        wikidomain=wikidomain,
        url=wikiurl,
        filename="index.html",
        path="",
        overwrite=overwrite,
    )


def downloadLogo(wikidomain="", wikiurl="", overwrite=False):
    index = f"{wikidomain}/index.html"
    if os.path.exists(index):
        raw = ""
        try:
            with open(index, encoding="utf-8") as f:
                raw = f.read()
        except:
            with open(index, encoding="latin-1") as f:
                raw = f.read()
        if m := re.findall(r'class="WikiLogo WikiElement"><img src="([^<> "]+?)"', raw):
            logourl = m[0]
            logofilename = logourl.split("/")[-1]
            print("Downloading logo")
            saveURL(
                wikidomain=wikidomain,
                url=logourl,
                filename=logofilename,
                path="",
                overwrite=overwrite,
            )
            return logofilename
    return ""


def printhelp():
    helptext = """This script downloads (and uploads) WikiSpaces wikis.

Parameters available:

--upload: upload compressed file with downloaded wiki
--admin: add item to WikiTeam collection (if you are an admin in that collection)
--overwrite: download again even if files exists locally
--overwrite-ia: upload again to Internet Archive even if item exists there
--help: prints this help text

Examples:

python3 wikispaces.py https://mywiki.wikispaces.com
   It downloads that wiki

python3 wikispaces.py wikis.txt
   It downloads a list of wikis (file format is a URL per line)

python3 wikispaces.py https://mywiki.wikispaces.com --upload
   It downloads that wiki, compress it and uploading to Internet Archive
"""
    print(helptext)
    sys.exit()


def duckduckgo():
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)

    wikis = []
    ignorewikis = [
        "https://wikispaces.com",
        "https://www.wikispaces.com",
        "https://wikispaces.net",
        "https://www.wikispaces.net",
    ]
    for _ in range(1, 100000):
        url = f"https://duckduckgo.com/html/?q={random.randint(100, 5000)}%20{random.randint(1000, 9999)}%20site:wikispaces.com"
        print("URL search", url)
        try:
            html = urllib.request.urlopen(url).read().decode("utf-8")
        except:
            print("Search error")
            time.sleep(30)
            continue
        html = urllib.parse.unquote(html)
        m = re.findall(r"://([^/]+?\.wikispaces\.com)", html)
        for wiki in m:
            wiki = f"https://{wiki}"
            wiki = re.sub(r"https://www\.", "https://", wiki)
            if wiki not in wikis and wiki not in ignorewikis:
                wikis.append(wiki)
                yield wiki
        sleep = random.randint(5, 20)
        print("Sleeping %d seconds" % (sleep))
        time.sleep(sleep)


def main():
    upload = False
    isadmin = False
    overwrite = False
    overwriteia = False
    if len(sys.argv) < 2:
        printhelp()
    param = sys.argv[1]
    if not param:
        printhelp()
    if len(sys.argv) > 2:
        if "--upload" in sys.argv:
            upload = True
        if "--admin" in sys.argv:
            isadmin = True
        if "--overwrite" in sys.argv:
            overwrite = True
        if "--overwrite-ia" in sys.argv:
            overwriteia = True
        if "--help" in sys.argv:
            printhelp()

    wikilist = []
    if "://" in param:
        wikilist.append(param.rstrip("/"))
    elif param.lower() == "duckduckgo":
        wikilist = duckduckgo()
        # for wiki in wikilist:
        #    print(wiki)
    else:
        with open(param) as f:
            wikilist = f.read().strip().splitlines()
            wikilist2 = []
            for wiki in wikilist:
                wikilist2.append(wiki.rstrip("/"))
            wikilist = wikilist2

    for wikiurl in wikilist:
        wikidomain = wikiurl.split("://")[1].split("/")[0]
        print("\n")
        print("#" * 40, "\n Downloading:", wikiurl)
        print("#" * 40, "\n")

        if upload and not overwriteia:
            itemid = "wiki-%s" % (wikidomain)
            try:
                iahtml = ""
                try:
                    iahtml = (
                        urllib.request.urlopen(
                            "https://archive.org/details/%s" % (itemid)
                        )
                        .read()
                        .decode("utf-8")
                    )
                except:
                    time.sleep(10)
                    iahtml = (
                        urllib.request.urlopen(
                            "https://archive.org/details/%s" % (itemid)
                        )
                        .read()
                        .decode("utf-8")
                    )
                if iahtml and not re.findall(r"(?im)Item cannot be found", iahtml):
                    if not overwriteia:
                        print(
                            "Warning: item exists on Internet Archive. Skipping wiki. Force with parameter --overwrite-ia"
                        )
                        print(
                            "You can find it in https://archive.org/details/%s"
                            % (itemid)
                        )
                        time.sleep(1)
                        continue
            except:
                pass

        dirfiles = "%s/files" % (wikidomain)
        if not os.path.exists(dirfiles):
            print("Creating directory %s" % (dirfiles))
            os.makedirs(dirfiles)
        dirpages = "%s/pages" % (wikidomain)
        if not os.path.exists(dirpages):
            print("Creating directory %s" % (dirpages))
            os.makedirs(dirpages)
        sitemapurl = "https://%s/sitemap.xml" % (wikidomain)

        downloadSitemap(wikidomain=wikidomain, wikiurl=sitemapurl, overwrite=overwrite)
        if not os.path.exists("%s/sitemap.xml" % (wikidomain)):
            print("Error, wiki was probably deleted. Skiping wiki...")
            continue
        else:
            sitemapraw = ""
            try:
                with open("%s/sitemap.xml" % (wikidomain), encoding="utf-8") as g:
                    sitemapraw = g.read()
            except:
                with open("%s/sitemap.xml" % (wikidomain), encoding="latin-1") as g:
                    sitemapraw = g.read()
            if re.search(r"(?im)<h1>This wiki has been deactivated</h1>", sitemapraw):
                print("Error, wiki was deactivated. Skiping wiki...")
                continue

        downloadMainPage(wikidomain=wikidomain, wikiurl=wikiurl, overwrite=overwrite)
        if not os.path.exists("%s/index.html" % (wikidomain)):
            print("Error, wiki was probably deleted or expired. Skiping wiki...")
            continue
        else:
            indexraw = ""
            try:
                with open("%s/index.html" % (wikidomain), encoding="utf-8") as g:
                    indexraw = g.read()
            except:
                with open("%s/index.html" % (wikidomain), encoding="latin-1") as g:
                    indexraw = g.read()
            if re.search(r"(?im)<h1>Subscription Expired</h1>", indexraw):
                print("Error, wiki subscription expired. Skiping wiki...")
                continue

        downloadPagesAndFiles(
            wikidomain=wikidomain, wikiurl=wikiurl, overwrite=overwrite
        )
        logofilename = downloadLogo(
            wikidomain=wikidomain, wikiurl=wikiurl, overwrite=overwrite
        )

        if upload:
            itemid = "wiki-%s" % (wikidomain)
            print("\nCompressing dump...")
            wikidir = wikidomain
            os.chdir(wikidir)
            print("Changed directory to", os.getcwd())
            wikizip = "%s.zip" % (wikidomain)
            subprocess.call(
                "zip"
                + " -r ../%s files/ pages/ index.html pages-and-files.csv sitemap.xml %s"
                % (wikizip, logofilename),
                shell=True,
            )
            os.chdir("..")
            print("Changed directory to", os.getcwd())

            print("\nUploading to Internet Archive...")
            indexfilename = "%s/index.html" % (wikidir)
            if not os.path.exists(indexfilename):
                print("\nError dump incomplete, skipping upload\n")
                continue
            indexhtml = ""
            try:
                with open(indexfilename, encoding="utf-8") as f:
                    indexhtml = f.read()
            except:
                with open(indexfilename, encoding="latin-1") as f:
                    indexhtml = f.read()

            wikititle = ""
            try:
                wikititle = (
                    indexhtml.split("wiki: {")[1]
                    .split("}")[0]
                    .split("text: '")[1]
                    .split("',")[0]
                    .strip()
                )
            except:
                wikititle = wikidomain
            if not wikititle:
                wikititle = wikidomain
            wikititle = wikititle.replace("\\'", " ")
            wikititle = wikititle.replace('\\"', " ")
            itemtitle = "Wiki - %s" % wikititle
            itemdesc = (
                '<a href="%s">%s</a> dumped with <a href="https://github.com/WikiTeam/wikiteam" rel="nofollow">WikiTeam</a> tools.'
                % (wikiurl, wikititle)
            )
            itemtags = [
                "wiki",
                "wikiteam",
                "wikispaces",
                wikititle,
                wikidomain.split(".wikispaces.com")[0],
                wikidomain,
            ]
            itemoriginalurl = wikiurl
            itemlicenseurl = ""
            m = ""
            try:
                m = re.findall(
                    r'<a rel="license" href="([^<>]+?)">',
                    indexhtml.split('<div class="WikiLicense')[1].split("</div>")[0],
                )
            except:
                m = ""
            if m:
                itemlicenseurl = m[0]
            if not itemlicenseurl:
                itemtags.append("unknowncopyright")
            itemtags_ = " ".join(
                ["--metadata='subject:%s'" % (tag) for tag in itemtags]
            )
            itemcollection = isadmin and "wikiteam" or "opensource"
            itemlang = "Unknown"
            itemdate = datetime.datetime.now().strftime("%Y-%m-%d")
            itemlogo = logofilename and f"{wikidir}/{logofilename}" or ""
            callplain = "ia upload {} {} {} --metadata='mediatype:web' --metadata='collection:{}' --metadata='title:{}' --metadata='description:{}' --metadata='language:{}' --metadata='last-updated-date:{}' --metadata='originalurl:{}' {} {}".format(
                itemid,
                wikizip,
                itemlogo and itemlogo or "",
                itemcollection,
                itemtitle,
                itemdesc,
                itemlang,
                itemdate,
                itemoriginalurl,
                itemlicenseurl
                and "--metadata='licenseurl:%s'" % (itemlicenseurl)
                or "",
                itemtags_,
            )
            print(callplain)
            subprocess.call(callplain, shell=True)

            """
            md = {
                'mediatype': 'web',
                'collection': itemcollection,
                'title': itemtitle,
                'description': itemdesc,
                'language': itemlang,
                'last-updated-date': itemdate,
                'subject': '; '.join(itemtags),
                'licenseurl': itemlicenseurl,
                'originalurl': itemoriginalurl,
            }
            item = get_item(itemid)
            item.upload(wikizip, metadata=md, access_key=accesskey, secret_key=secretkey, verbose=True, queue_derive=False)
            item.modify_metadata(md)
            if itemlogo:
                item.upload(itemlogo, access_key=accesskey, secret_key=secretkey, verbose=True)
            """

            print("You can find it in https://archive.org/details/%s" % (itemid))
            os.remove(wikizip)


if __name__ == "__main__":
    main()
