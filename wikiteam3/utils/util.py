import hashlib
import re
import sys


def cleanHTML(raw: str = "") -> str:
    """Extract only the real wiki content and remove rubbish
    This function is ONLY used to retrieve page titles
    and file names when no API is available
    DO NOT use this function to extract page content"""
    # different "tags" used by different MediaWiki versions to mark where
    # starts and ends content
    if re.search("<!-- bodytext -->", raw):
        raw = raw.split("<!-- bodytext -->")[1].split("<!-- /bodytext -->")[0]
    elif re.search("<!-- start content -->", raw):
        raw = raw.split("<!-- start content -->")[1].split("<!-- end content -->")[0]
    elif re.search("<!-- Begin Content Area -->", raw):
        raw = raw.split("<!-- Begin Content Area -->")[1].split(
            "<!-- End Content Area -->"
        )[0]
    elif re.search("<!-- content -->", raw):
        raw = raw.split("<!-- content -->")[1].split("<!-- mw_content -->")[0]
    elif re.search(r'<article id="WikiaMainContent" class="WikiaMainContent">', raw):
        raw = raw.split('<article id="WikiaMainContent" class="WikiaMainContent">')[
            1
        ].split("</article>")[0]
    elif re.search("<body class=", raw):
        raw = raw.split("<body class=")[1].split('<div class="printfooter">')[0]
    else:
        print(raw[:250])
        print("This wiki doesn't use marks to split content")
        sys.exit()
    return raw


def undoHTMLEntities(text: str = "") -> str:
    """Undo some HTML codes"""

    # i guess only < > & " ' need conversion
    # http://www.w3schools.com/html/html_entities.asp
    text = re.sub("&lt;", "<", text)
    text = re.sub("&gt;", ">", text)
    text = re.sub("&amp;", "&", text)
    text = re.sub("&quot;", '"', text)
    text = re.sub("&#039;", "'", text)

    return text


def removeIP(raw: str = "") -> str:
    """Remove IP from HTML comments <!-- -->"""

    raw = re.sub(r"\d+\.\d+\.\d+\.\d+", "0.0.0.0", raw)
    # http://www.juniper.net/techpubs/software/erx/erx50x/swconfig-routing-vol1/html/ipv6-config5.html
    # weird cases as :: are not included
    raw = re.sub(
        r"(?i)[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}",
        "0:0:0:0:0:0:0:0",
        raw,
    )

    return raw


def cleanXML(xml: str = "") -> str:
    """Trim redundant info from the XML however it comes"""
    # do not touch XML codification, leave AS IS
    # EDIT 2022: we are making this explicitly Unicode
    # for Windows compatibility.
    # If the encoding has to stay as is, we'll have
    # to change all the file encodings, as well.

    if re.search(r"</siteinfo>\n", xml):
        xml = xml.split("</siteinfo>\n")[1]
    if re.search(r"</mediawiki>", xml):
        xml = xml.split("</mediawiki>")[0]
    return xml


def sha1File(filename: str = "") -> str:
    """Return the SHA1 hash of a file"""

    sha1 = hashlib.sha1()
    with open(filename, "rb") as f:
        while True:
            if data := f.read(65536):
                sha1.update(data)
            else:
                break
    return sha1.hexdigest()
