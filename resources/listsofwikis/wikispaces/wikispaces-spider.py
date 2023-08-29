#!/usr/bin/env python3

# Copyright (C) 2016 wikiTeam
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

import csv
import random
import re
import time
import urllib


def loadUsers():
    users = {}
    with open("users.txt") as f:
        for x in f.read().strip().splitlines():
            username = x.split(",")[0]
            numwikis = x.split(",")[1]
            users[username] = numwikis
    return users


def loadWikis():
    wikis = {}
    with open("wikis.txt") as f:
        for x in f.read().strip().splitlines():
            wikiname = x.split(",")[0]
            numusers = x.split(",")[1]
            wikis[wikiname] = numusers
    return wikis


def saveUsers(users):
    with open("users.txt", "w") as f:
        output = [f"{x},{y}" for x, y in users.items()]
        output.sort()
        output = "\n".join(output)
        f.write(output)


def saveWikis(wikis):
    with open("wikis.txt", "w") as f:
        output = [f"{x},{y}" for x, y in wikis.items()]
        output.sort()
        output = "\n".join(output)
        f.write(output)


def getUsers(wiki):
    wikiurl = f"https://{wiki}.wikispaces.com/wiki/members?utable=WikiTableMemberList&ut_csv=1"
    try:
        wikireq = urllib.Request(wikiurl, headers={"User-Agent": "Mozilla/5.0"})
        wikicsv = urllib.request.urlopen(wikireq)
        reader = csv.reader(wikicsv, delimiter=",", quotechar='"')
        headers = next(reader, None)
        return {row[0]: "?" for row in reader}
    except:
        print("Error reading", wikiurl)
        return {}


def getWikis(user):
    wikiurl = f"https://www.wikispaces.com/user/view/{user}"
    try:
        wikireq = urllib.Request(wikiurl, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(wikireq).read()
        if "Wikis: " in html:
            html = html.split("Wikis: ")[1].split("</div>")[0]
            return {
                x: "?"
                for x in re.findall(r'<a href="https://([^>]+).wikispaces.com/">', html)
            }
        return {}
    except:
        print("Error reading", wikiurl)
        return {}


def main():
    sleep = 0.1
    rand = 10
    users = loadUsers()
    wikis = loadWikis()

    usersc = len(users)
    wikisc = len(wikis)
    print("Loading files")
    print("Loaded", usersc, "users")
    print("Loaded", wikisc, "wikis")

    # find more users
    print("Scanning wikis for more users")
    for wiki, numusers in wikis.items():
        if numusers != "?":  # we have scanned this wiki before, skiping
            continue
        print(f"Scanning https://{wiki}.wikispaces.com for users")
        users2 = getUsers(wiki)
        wikis[wiki] = len(users2)
        c = 0
        for x2, y2 in users2.items():
            if x2 not in users.keys():
                users[x2] = "?"
                c += 1
        print(f"Found {c} new users")
        if c > 0:
            if random.randint(0, rand) == 0:
                saveUsers(users)
                users = loadUsers()
        if random.randint(0, rand) == 0:
            saveWikis(wikis)
        time.sleep(sleep)
    saveWikis(wikis)
    wikis = loadWikis()
    saveUsers(users)
    users = loadUsers()

    # find more wikis
    print("Scanning users for more wikis")
    for user, numwikis in users.items():
        if numwikis != "?":  # we have scanned this user before, skiping
            continue
        print(f"Scanning https://www.wikispaces.com/user/view/{user} for wikis")
        wikis2 = getWikis(user)
        users[user] = len(wikis2)
        c = 0
        for x2, y2 in wikis2.items():
            if x2 not in wikis.keys():
                wikis[x2] = "?"
                c += 1
        print(f"Found {c} new wikis")
        if c > 0:
            if random.randint(0, rand) == 0:
                saveWikis(wikis)
                wikis = loadWikis()
        if random.randint(0, rand) == 0:
            saveUsers(users)
        time.sleep(sleep)
    saveWikis(wikis)
    wikis = loadWikis()
    saveUsers(users)
    users = loadUsers()

    print("\nSummary:")
    print("Found", len(users) - usersc, "new users")
    print("Found", len(wikis) - wikisc, "new wikis")


if __name__ == "__main__":
    main()
