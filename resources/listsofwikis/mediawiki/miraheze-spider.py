#!/usr/bin/env python3

# Copyright (C) 2022 Simon Liu
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

import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def nextpage(soup):
    try:
        soup.find("span", text="Next page").parent["href"]
        return True
    except:
        return False


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
    }

    req = requests.get("https://meta.miraheze.org/wiki/Special:WikiDiscover")
    soup = BeautifulSoup(req.content, features="lxml")
    wikis = re.findall(
        r"<td class=\"TablePager_col_wiki_dbname\"><a href=\"([^>]+?)\">", req.text
    )

    while nextpage(soup):
        time.sleep(0.3)
        req = requests.get(
            urljoin(
                "https://meta.miraheze.org",
                soup.find("span", text="Next page").parent["href"],
            )
        )
        soup = BeautifulSoup(req.content, features="lxml")
        wikis.extend(
            re.findall(
                r"<td class=\"TablePager_col_wiki_dbname\"><a href=\"([^>]+?)\">",
                req.text,
            )
        )

    wikis = sorted(set(wikis))
    with open("miraheze.org", "w") as f:
        for wiki in wikis:
            f.write(urljoin(wiki, "w/api.php") + "\n")


if __name__ == "__main__":
    main()
