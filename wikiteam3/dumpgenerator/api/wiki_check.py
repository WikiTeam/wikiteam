import re

import requests

from wikiteam3.utils import getUserAgent


def getWikiEngine(url="", session: requests.Session=None) -> str:
    """Returns the wiki engine of a URL, if known"""

    if not session:
        session = requests.Session()  # Create a new session
        session.headers.update({"User-Agent": getUserAgent()})
    r = session.post(url=url, timeout=30)
    if r.status_code == 405 or r.text == "":
        r = session.get(url=url, timeout=120)
    result = r.text

    wikiengine = "Unknown"
    if re.search(
        '(?im)(<meta name="generator" content="DokuWiki)|dokuwiki__site', result
    ):
        wikiengine = "DokuWiki"
    elif re.search(
        '(?im)(alt="Powered by MediaWiki"|<meta name="generator" content="MediaWiki|class="mediawiki)',
        result,
    ):
        wikiengine = "MediaWiki"
    elif re.search(
        '(?im)(>MoinMoin Powered</a>|<option value="LocalSiteMap">)', result
    ):
        wikiengine = "MoinMoin"
    elif re.search(
        "(?im)(twikiCurrentTopicLink|twikiCurrentWebHomeLink|twikiLink)", result
    ):
        wikiengine = "TWiki"
    elif re.search("(?im)(<!--PageHeaderFmt-->)", result):
        wikiengine = "PmWiki"
    elif re.search(
        '(?im)(<meta name="generator" content="PhpWiki|<meta name="PHPWIKI_VERSION)',
        result,
    ):
        wikiengine = "PhpWiki"
    elif re.search(
        r'(?im)(<meta name="generator" content="Tiki Wiki|Powered by <a href="http://(www\.)?tiki\.org"| id="tiki-(top|main)")',
        result,
    ):
        wikiengine = "TikiWiki"
    elif re.search(
        r'(?im)(foswikiNoJs|<meta name="foswiki\.|foswikiTable|foswikiContentFooter)',
        result,
    ):
        wikiengine = "FosWiki"
    elif re.search(r'(?im)(<meta http-equiv="powered by" content="MojoMojo)', result):
        wikiengine = "MojoMojo"
    elif re.search(
        r'(?im)(id="xwiki(content|nav_footer|platformversion|docinfo|maincontainer|data)|/resources/js/xwiki/xwiki|XWiki\.webapppath)',
        result,
    ):
        wikiengine = "XWiki"
    elif re.search(r'(?im)(<meta id="confluence-(base-url|context-path)")', result):
        wikiengine = "Confluence"
    elif re.search(r'(?im)(<meta name="generator" content="Banana Dance)', result):
        wikiengine = "Banana Dance"
    elif re.search(
        r'(?im)(Wheeled by <a class="external-link" href="http://www\.wagn\.org">|<body id="wagn">)',
        result,
    ):
        wikiengine = "Wagn"
    elif re.search(r'(?im)(<meta name="generator" content="MindTouch)', result):
        wikiengine = "MindTouch"  # formerly DekiWiki
    elif re.search(
        r'(?im)(<div class="wikiversion">\s*(<p>)?JSPWiki|xmlns:jspwiki="http://www\.jspwiki\.org")',
        result,
    ):
        wikiengine = "JSPWiki"
    elif re.search(
        r'(?im)(Powered by:?\s*(<br ?/>)?\s*<a href="http://kwiki\.org">|\bKwikiNavigation\b)',
        result,
    ):
        wikiengine = "Kwiki"
    elif re.search(r'(?im)(Powered by <a href="http://www\.anwiki\.com")', result):
        wikiengine = "Anwiki"
    elif re.search(
        '(?im)(<meta name="generator" content="Aneuch|is powered by <em>Aneuch</em>|<!-- start of Aneuch markup -->)',
        result,
    ):
        wikiengine = "Aneuch"
    elif re.search(r'(?im)(<meta name="generator" content="bitweaver)', result):
        wikiengine = "bitweaver"
    elif re.search(r'(?im)(powered by <a href="[^"]*\bzwiki.org(/[^"]*)?">)', result):
        wikiengine = "Zwiki"
    # WakkaWiki forks
    elif re.search(
        r'(?im)(<meta name="generator" content="WikkaWiki|<a class="ext" href="(http://wikka\.jsnx\.com/|http://wikkawiki\.org/)">)',
        result,
    ):
        wikiengine = "WikkaWiki"  # formerly WikkaWakkaWiki
    elif re.search(r'(?im)(<meta name="generator" content="CoMa Wiki)', result):
        wikiengine = "CoMaWiki"
    elif re.search(r'(?im)(Fonctionne avec <a href="http://www\.wikini\.net)', result):
        wikiengine = "WikiNi"
    elif re.search(r'(?im)(Powered by <a href="[^"]*CitiWiki">CitiWiki</a>)', result):
        wikiengine = "CitiWiki"
    elif re.search(
        r'(?im)(Powered by <a href="http://wackowiki\.com/|title="WackoWiki")', result
    ):
        wikiengine = "WackoWiki"
    elif re.search(r'(?im)(Powered by <a href="http://www\.wakkawiki\.com)', result):
        # This may not work for heavily modded/themed installations, e.g.
        # http://operawiki.info/
        wikiengine = "WakkaWiki"
    # Custom wikis used by wiki farms
    elif re.search(r'(?im)(var wikispaces_page|<div class="WikispacesContent)', result):
        wikiengine = "Wikispaces"
    elif re.search(
        r'(?im)(Powered by <a href="http://www\.wikidot\.com">|wikidot-privacy-button-hovertip|javascript:WIKIDOT\.page)',
        result,
    ):
        wikiengine = "Wikidot"
    elif re.search(
        r"(?im)(IS_WETPAINT_USER|wetpaintLoad|WPC-bodyContentContainer)", result
    ):
        wikiengine = "Wetpaint"
    elif re.search(
        '(?im)(<div id="footer-pbwiki">|ws-nav-search|PBinfo *= *{)', result
    ):
        # formerly PBwiki
        wikiengine = "PBworks"
    # if wikiengine == 'Unknown': print (result)

    return wikiengine
