#!/usr/bin/env python3

# Copyright (C) 2014-2022 WikiTeam developers
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
from urllib import parse

import requests


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
    }

    urls = [
        "http://www.wiki.co.il/active-wiki-all.html",
        "http://www.wiki.co.il/active-wiki-en.html",
    ]
    wikis = []
    for url in urls:
        req = requests.get(url, headers=headers)
        wikis.extend(re.findall(r'<td><a href="([^>]+?)"', req.text))

    wikis = sorted(set(wikis))
    with open("wiki-site.com", "w") as f:
        for wiki in wikis:
            f.write(parse.urljoin(wiki, "api.php") + "\n")


if __name__ == "__main__":
    main()
