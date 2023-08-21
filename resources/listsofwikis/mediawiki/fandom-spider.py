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
from urllib import parse

import requests
from tqdm import tqdm


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
    }

    # grab lvl3 links
    req = requests.get(
        "https://community.fandom.com/wiki/Sitemap?level=2", headers=headers
    )
    map_lvl3 = re.findall(r"<a class=\"title\" href=\"([^>]+?)\">", req.text)

    # grab wiki links
    wikis = []
    for lvl3 in tqdm(map_lvl3):
        time.sleep(0.3)
        req = requests.get("https://community.fandom.com%s" % lvl3)
        if req.status_code != 200:
            time.sleep(5)
            req = requests.get("https://community.fandom.com%s" % lvl3)
        wikis.extend(
            [
                wiki.replace("http://", "https://")
                for wiki in re.findall(
                    r"<a class=\"title\" href=\"([^>]+?)\">", req.text
                )
            ]
        )

    wikis = list(set(wikis))
    wikis.sort()
    with open("fandom.com", "w") as f:
        for wiki in wikis:
            f.write(parse.urljoin(wiki, "api.php") + "\n")


if __name__ == "__main__":
    main()
