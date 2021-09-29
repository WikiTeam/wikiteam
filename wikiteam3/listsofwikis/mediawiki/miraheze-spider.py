#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2014-2017 WikiTeam developers
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

import requests


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
    }

    url = "https://meta.miraheze.org/wiki/Special:SiteMatrix"
    r = requests.get(url, headers=headers)
    raw = r.text
    m = re.findall(r'<tr><td>(<del>)?<a href="https://([^>]+?)/">[^<]+</a>', raw)
    m.sort()
    for i in m:
        print("https://" + i[1] + "/w/api.php")


if __name__ == "__main__":
    main()
