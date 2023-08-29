#!/usr/bin/env python3

# Copyright (C) 2019 WikiTeam developers
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

import requests


def main():
    wikis = []
    with open("wikidot-spider2.txt") as f:
        wikis = f.read().strip().splitlines()

    for _ in range(1, 1000000):
        url = random.choice(wikis)
        urlrandom = (
            url.endswith("/") and f"{url}random-site.php" or f"{url}/random-site.php"
        )
        print(f"URL exploring {urlrandom}")
        try:
            r = requests.get(urlrandom)
        except:
            continue
        redirect = ""
        if r.url and r.url.endswith("wikidot.com"):
            redirect = r.url
            print(redirect)
        else:
            continue
        wikis.append(redirect)

        with open("wikidot-spider2.txt", "w") as f:
            wikis2 = []
            for wiki in wikis:
                wiki = re.sub(r"https?://www\.", "http://", wiki)
                if wiki not in wikis2:
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
