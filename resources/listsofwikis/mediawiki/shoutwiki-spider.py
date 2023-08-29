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

import time

import requests
from tqdm import tqdm


def main():
    ids, wikis = [], []
    gcont = "tmp"
    url = "http://www.shoutwiki.com/w/api.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0"
    }

    # grab wiki pages
    params = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "generator": "categorymembers",
        "inprop": "url",
        "gcmtitle": "Category:Flat_list_of_all_wikis",
        "gcmlimit": "max",
    }
    while gcont:
        if gcont != "tmp":
            params["gcmcontinue"] = gcont
        json = requests.get(url, params=params, headers=headers).json()
        gcont = json["continue"]["gcmcontinue"] if "continue" in json else ""
        query = json["query"]["pages"]
        ids.extend(iter(query))
    # grab wiki API
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "formatversion": "2",
        "rvprop": "content",
        "rvslots": "*",
    }
    for n in tqdm(range(0, len(ids), 50)):
        params["pageids"] = "|".join(ids[n : n + 50])
        json = requests.get(url, params=params, headers=headers).json()

        for wiki in json["query"]["pages"]:
            for val in wiki["revisions"][0]["slots"]["main"]["content"].split("\n|"):
                if "subdomain" in val:
                    wikis.append(
                        f'http://{val.split("subdomain =")[-1].strip()}.shoutwiki.com/w/api.php'
                    )
                    break

        time.sleep(0.3)
    wikis = sorted(set(wikis))
    with open("shoutwiki.com", "w") as f:
        f.write("\n".join(wikis))


if __name__ == "__main__":
    main()
