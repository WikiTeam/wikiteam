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

import random
import re
import sys
import time
import urllib.request


def main():
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)

    wikis = []
    with open("wikidot-spider.txt") as f:
        wikis = f.read().strip().splitlines()

    for i in range(1, 1000000):
        url = random.choice(wikis)
        print("URL search", url)
        try:
            html = urllib.request.urlopen(url).read().decode("utf-8")
        except:
            print("Search error")
            time.sleep(30)
            continue
        html = urllib.parse.unquote(html)
        m = re.findall(r"://([^/]+?\.wikidot\.com)", html)
        for wiki in m:
            wiki = "http://" + wiki
            if not wiki in wikis:
                wikis.append(wiki)
                wikis.sort()
                print(wiki)
        with open("wikidot-spider.txt", "w") as f:
            wikis2 = []
            for wiki in wikis:
                wiki = re.sub(r"https?://www\.", "http://", wiki)
                if not wiki in wikis2:
                    wikis2.append(wiki)
            wikis = wikis2
            wikis.sort()
            f.write("\n".join(wikis))
        print("%d wikis found" % (len(wikis)))
        sleep = random.randint(1, 5)
        print("Sleeping %d seconds" % (sleep))
        time.sleep(sleep)


if __name__ == "__main__":
    main()
