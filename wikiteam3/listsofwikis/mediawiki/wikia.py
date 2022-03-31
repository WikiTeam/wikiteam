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
        list = getlist(wikia, offset, offset + limit)
        if list:
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

    undumped = []
    # Or we could iterate over each sublist while we get it?
    for i in domains:
        dbname = re.sub("[-_.]", "", domains[i]["domain"].replace(".wikia.com", ""))
        dbname = re.escape(dbname)
        print(dbname)
        first = dbname[0]
        # There are one-letter dbnames; the second letter is replaced by an underscore
        # http://s3.amazonaws.com/wikia_xml_dumps/n/n_/n_pages_full.xml.7z
        try:
            second = dbname[1]
        except:
            second = "_"
        base = (
            "http://s3.amazonaws.com/wikia_xml_dumps/"
            + first
            + "/"
            + first
            + second
            + "/"
            + dbname
        )
        full = base + "_pages_full.xml.7z"
        print(full)
        current = base + "_pages_current.xml.7z"
        images = base + "_images.tar"
        try:
            # subprocess.check_call(['wget', '-e', 'robots=off', '--fail', '-nc', '-a', 'wikia.log', full])
            # Use this instead, and comment out the next try, to only list.
            subprocess.call(["curl", "-I", "--fail", full])
        except subprocess.CalledProcessError as e:
            # We added --fail for this https://superuser.com/a/854102/283120
            if e.returncode == 22:
                print("Missing: " + domains[i]["domain"])
                undumped.append(domains[i]["domain"])

        # try:
        #    subprocess.check_call(['wget', '-e', 'robots=off', '-nc', '-a', 'wikia.log', current])
        #    subprocess.check_call(['wget', '-e', 'robots=off', '-nc', '-a', 'wikia.log', images])
        # except:
        #    pass

    with open("wikia.com-unarchived", "w+") as out:
        out.write("\n".join(str(domain) for domain in undumped))


if __name__ == "__main__":
    main()
