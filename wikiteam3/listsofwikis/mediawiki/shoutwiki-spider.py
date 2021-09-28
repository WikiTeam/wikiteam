#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2014 WikiTeam developers
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

import json
import random
import re
import time

import requests


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
    }
    swfrom = 1
    swlimit = 500
    while swfrom:
        params = {
            "action": "listwikis",
            "swfrom": swfrom,
            "swlimit": swlimit,
            "format": "json",
        }
        url = "http://www.shoutwiki.com/w/api.php"
        r = requests.get(url, params=params, headers=headers)
        jsonsites = json.loads(r.text)

        for site in jsonsites["query"]["listwikis"]:
            siteid = int(site["id"])
            siteurl = site["url"]
            print(siteurl)

        if len(jsonsites["query"]["listwikis"]) == int(swlimit):
            # there are more
            swfrom = siteid + 1
        else:
            swfrom = ""

        time.sleep(random.randint(3, 10))


if __name__ == "__main__":
    main()
