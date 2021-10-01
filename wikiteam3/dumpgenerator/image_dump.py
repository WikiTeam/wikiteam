import os
import delay
import re
import urllib

from exceptions import PageMissingError
from image_description import getXMLFileDesc
from log_error import logerror
from truncate import truncateFilename


def generateImageDump(config={}, other={}, images=[], start="", session=None):
    """Save files and descriptions using a file list"""

    # fix use subdirectories md5
    print('Retrieving images from "%s"' % (start and start or "start"))
    imagepath = "%s/images" % (config["path"])
    if not os.path.isdir(imagepath):
        print('Creating "%s" directory' % (imagepath))
        os.makedirs(imagepath)

    c = 0
    lock = True
    if not start:
        lock = False
    for filename, url, uploader in images:
        if filename == start:  # start downloading from start (included)
            lock = False
        if lock:
            continue
        delay(config=config, session=session)

        # saving file
        # truncate filename if length > 100 (100 + 32 (md5) = 132 < 143 (crash
        # limit). Later .desc is added to filename, so better 100 as max)
        filename2 = urllib.parse.unquote(filename)
        if len(filename2) > other["filenamelimit"]:
            # split last . (extension) and then merge
            filename2 = truncateFilename(other=other, filename=filename2)
            print("Filename is too long, truncating. Now it is:", filename2)
        filename3 = u"%s/%s" % (imagepath, filename2)
        imagefile = open(filename3, "wb")

        r = session.head(url=url, allow_redirects=True)
        original_url_redirected = len(r.history) > 0

        if original_url_redirected:
            # print 'Site is redirecting us to: ', r.url
            original_url = url
            url = r.url

        r = session.get(url=url, allow_redirects=False)

        # Try to fix a broken HTTP to HTTPS redirect
        if r.status_code == 404 and original_url_redirected:
            if (
                original_url.split("://")[0] == "http"
                and url.split("://")[0] == "https"
            ):
                url = "https://" + original_url.split("://")[1]
                # print 'Maybe a broken http to https redirect, trying ', url
                r = session.get(url=url, allow_redirects=False)

        if r.status_code == 404:
            logerror(
                config=config, text=u"File %s at URL %s is missing" % (filename2, url)
            )

        imagefile.write(r.content)
        imagefile.close()
        # saving description if any
        try:
            title = u"Image:%s" % (filename)
            if (
                config["xmlrevisions"]
                and config["api"]
                and config["api"].endswith("api.php")
            ):
                r = session.get(
                    config["api"]
                    + u"?action=query&export&exportnowrap&titles=%s" % title
                )
                xmlfiledesc = r.text
            else:
                xmlfiledesc = getXMLFileDesc(
                    config=config, title=title, session=session
                )  # use Image: for backwards compatibility
        except PageMissingError:
            xmlfiledesc = ""
            logerror(
                config=config,
                text=u'The page "%s" was missing in the wiki (probably deleted)'
                % (str(title)),
            )

        f = open("%s/%s.desc" % (imagepath, filename2), "w")
        # <text xml:space="preserve" bytes="36">Banner featuring SG1, SGA, SGU teams</text>
        if not re.search(r"</page>", xmlfiledesc):
            # failure when retrieving desc? then save it as empty .desc
            xmlfiledesc = ""

        # Fixup the XML
        if xmlfiledesc != "" and not re.search(r"</mediawiki>", xmlfiledesc):
            xmlfiledesc += "</mediawiki>"

        f.write(str(xmlfiledesc))
        f.close()
        delay(config=config, session=session)
        c += 1
        if c % 10 == 0:
            print("    Downloaded %d images" % (c))

    print("Downloaded %d images" % (c))
