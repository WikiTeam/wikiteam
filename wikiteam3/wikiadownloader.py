#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2011 WikiTeam
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

# using a list of wikia subdomains, it downloads all dumps available in Special:Statistics pages
# you can use the list available at the "listofwikis" directory, the file is called wikia.com and it contains +200k wikis

import datetime
import os
import re
import sys
import urllib

""" 
instructions: 

it requires a list of wikia wikis
there is one in the repository (listofwikis directory)

run it: python wikiadownloader.py

it you want to resume: python wikiadownloader.py wikitostartfrom

where wikitostartfrom is the last downloaded wiki in the previous session

"""

f = open("wikia.com", "r")
wikia = f.read().strip().split("\n")
f.close()

print(len(wikia), "wikis in Wikia list")

start = "!"
if len(sys.argv) > 1:
    start = sys.argv[1]

for wiki in wikia:
    wiki = wiki.lower()
    prefix = wiki.split("http://")[1]
    if prefix < start:
        continue
    sys.stderr.write("Starting:", wiki)

    f = urllib.urlopen("%s/wiki/Special:Statistics" % (wiki))
    html = f.read()
    f.close()

    m = re.compile(
        r'(?i)<a href="(?P<urldump>http://[^<>]+pages_(?P<dump>current|full)\.xml\.(?P<compression>gz|7z|bz2))">(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}) (?P<time>\d\d:\d\d:\d\d)'
    )

    for i in m.finditer(html):
        urldump = i.group("urldump")
        dump = i.group("dump")
        date = "%s-%s-%s" % (i.group("year"), i.group("month"), i.group("day"))
        compression = i.group("compression")

        sys.stderr.write("Downloading", wiki, dump.lower())

        # {"name":"pages_full.xml.gz","timestamp":1273755409,"mwtimestamp":"20100513125649"}
        # {"name":"pages_current.xml.gz","timestamp":1270731925,"mwtimestamp":"20100408130525"}

        # -q, turn off verbose
        os.system(
            'wget -q -c "%s" -O %s-%s-pages-meta-%s.%s'
            % (
                urldump,
                prefix,
                date,
                dump.lower() == "current" and "current" or "history",
                compression,
            )
        )

    if not m.search(html):
        sys.stderr.write(sys.stderr, "Failed to download:", wiki)
        sys.stderr.write(sys.stderr, wiki)
