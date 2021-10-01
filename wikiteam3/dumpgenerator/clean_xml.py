import re


def cleanXML(xml=""):
    """Trim redundant info from the XML however it comes"""
    # do not touch XML codification, leave AS IS
    if re.search(r"</siteinfo>\n", xml):
        xml = xml.split("</siteinfo>\n")[1]
    if re.search(r"</mediawiki>", xml):
        xml = xml.split("</mediawiki>")[0]
    return xml
