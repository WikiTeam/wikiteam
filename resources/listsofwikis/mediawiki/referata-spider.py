#!/usr/bin/env python3

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

import random
import re
import time

import requests


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
    }

    keyword = "site:referata.com"
    for start in range(0, 1000, 10):
        url = "https://www.google.es/search?q=%s&start=%d" % (
            re.sub(" ", "%20", keyword),
            start,
        )
        r = requests.get(url, headers=headers)
        raw = r.text

        m = re.findall(r'(?im)<h3 class="r"><a href=\"([^ ]+?)" onmouse', raw)
        for i in m:
            print(i)

        if re.search(r'id="ofr"', raw):  # resultados omitidos, final
            break

        time.sleep(random.randint(3, 10))


if __name__ == "__main__":
    main()
