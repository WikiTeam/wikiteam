#!/usr/bin/env python3

# wikia.py List of not archived Wikia wikis
# Downloads Wikia's dumps and lists wikis which have none.
# TODO: check date, http://www.cyberciti.biz/faq/linux-unix-curl-if-modified-since-command-linux-example/
#
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

import re
import subprocess

from wikitools3 import api, wiki


def getlist(wikia, wkfrom=1, wkto=100):
    params = {
        "action": "query",
        "list": "wkdomains",
        "wkactive": "1",
        "wkfrom": wkfrom,
        "wkto": wkto,
    }
    request = api.APIRequest(wikia, params)
    return request.query()["query"]["wkdomains"]


def getall():
    wikia = wiki.Wiki("https://community.fandom.com/api.php")
    offset = 0
    limit = 100
    domains = {}
    empty = 0
    # This API module has no query continuation facility
    print("Getting list of active domains...")
    while True:
        if list := getlist(wikia, offset, offset + limit):
            print(offset)
            domains = dict(domains.items() + list.items())
            empty = 0
        else:
            empty += 1

        offset += limit
        if empty > 100:
            # Hopefully we don't have more than 10k wikis deleted in a row
            break
    return domains


def main():
    domains = getall()
    with open("wikia.com", "w") as out:
        out.write("\n".join(str(domains[i]["domain"]) for i in domains))

    # TODO: Remove the following code entirely. All Wikia wikis can now be
    # assumed to be undumped.
    return


if __name__ == "__main__":
    main()
