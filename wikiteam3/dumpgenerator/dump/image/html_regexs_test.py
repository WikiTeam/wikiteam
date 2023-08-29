import os
import re
from pathlib import Path
from typing import Dict, List

import pytest
import requests

from wikiteam3.dumpgenerator.dump.image.html_regexs import REGEX_CANDIDATES

ONLINE = True

HTML_DIR = Path("test/data/html_regexs")
os.makedirs(HTML_DIR, exist_ok=True)


def prepare_raws_from_urls(urls: Dict[str, str]):
    sess = requests.Session()
    raws: Dict[str, str] = {}
    for site, url in urls.items():
        try:
            resp = sess.get(url, timeout=10, allow_redirects=True)
        except Exception as e:
            pytest.warns(UserWarning, match=f"Could not fetch {url}: {e}")
            continue

        if resp.status_code == 200:
            raws[url] = resp.text
            if not os.path.exists(HTML_DIR / f"{site}.html"):
                with open(HTML_DIR / f"{site}.html", "w", encoding="utf-8") as f:
                    f.write(resp.text)
        else:
            pytest.warns(
                UserWarning,
                match=f"Could not fetch {url}: status_code: {resp.status_code}",
            )

    return raws


class TestRegexs:
    class TestRegexsOnline:
        listFiles_urls = {
            # site-date: url , `limit=` for counting the number of matches
            "group0.mediawiki.demo.save-web.org_mediawiki-1.16.5-20230701": "http://group0.mediawiki.demo.save-web.org/mediawiki-1.16.5/index.php?title=特殊:文件列表&limit=2",
            "group2.mediawiki.demo.save-web.org_mediawiki-1.39.1-20230701": "http://group2.mediawiki.demo.save-web.org/mediawiki-1.39.1/index.php?title=Special:ListFiles&limit=1",
            "archiveteam.org-20230701": "https://wiki.archiveteam.org/index.php?title=Special:ListFiles&sort=byname&limit=7",
            "wiki.othing.xyz-20230701": "https://wiki.othing.xyz/index.php?title=Special:ListFiles&sort=byname",
            "mediawiki.org-20230701": "https://www.mediawiki.org/w/index.php?title=Special:ListFiles&sort=byname&limit=7",
            "asoiaf.fandom.com-20230701": "https://asoiaf.fandom.com/zh/wiki/Special:文件列表?sort=byname&limit=7",
            # only for local testing:
            # "commons.moegirl.org.cn-20230701": "https://commons.moegirl.org.cn/index.php?title=Special:ListFiles&sort=byname&limit=7",
            # # login required:
            # "group0.mediawiki.demo.save-web.org_mediawiki-1.23.17-20230701": "http://group0.mediawiki.demo.save-web.org/mediawiki-1.23.17/index.php?title=Special:文件列表&limit=1",
            # "group1.mediawiki.demo.save-web.org_mediawiki-1.27.7-20230701": "http://group1.mediawiki.demo.save-web.org/mediawiki-1.27.7/index.php?title=Special:ListFiles&limit=2",
        }
        raws: Dict[str, str] = {}

        def test_online(self):
            if not ONLINE:
                pytest.skip("Online test skipped")
            self.raws = prepare_raws_from_urls(self.listFiles_urls)
            assert len(self.raws) != 0, "Could not fetch any of the URLs"
            for url, raw in self.raws.items():
                best_matched = 0
                regexp_best = None

                for regexp in REGEX_CANDIDATES:
                    _count = len(re.findall(regexp, raw))
                    if _count > best_matched:
                        best_matched = _count
                        regexp_best = regexp

                assert (
                    regexp_best is not None
                ), f"Could not find a proper regexp to parse the HTML for {url} (online)"

                if "limit=" in url:
                    limit = int(url.split("limit=")[-1])
                    assert (
                        len(re.findall(regexp_best, raw)) == limit
                    ), f"Could not find {limit} matches for {url} (online)"

    class TestRegexsOffline:
        html_files = os.listdir(HTML_DIR)
        raws: Dict[str, str] = {}
        for html_file in html_files:
            with open(HTML_DIR / html_file, encoding="utf-8") as f:
                raws[html_file] = f.read()
        assert len(raws) != 0, f"Could not find any HTML files in {HTML_DIR}"

        def test_offline(self):
            assert len(self.raws) != 0, "Could not fetch any of the URLs"
            for site, raw in self.raws.items():
                best_matched = 0
                regexp_best = None

                for regexp in REGEX_CANDIDATES:
                    _count = len(re.findall(regexp, raw))
                    if _count > best_matched:
                        best_matched = _count
                        regexp_best = regexp

                assert (
                    regexp_best is not None
                ), f"Could not find a proper regexp to parse the HTML for {site} (local)"
