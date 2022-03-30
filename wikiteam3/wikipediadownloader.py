#!/usr/bin/env python3

# Copyright (C) 2011-2014 WikiTeam
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

import argparse
import os
import re
import sys
import time
import urllib


def main():
    parser = argparse.ArgumentParser(description="Downloader of Wikimedia dumps")
    # parser.add_argument('-f', '--families', help='Choose which family projects to download (e.g. all, wikipedia, wikibooks, wikinews, wikiquote, wikisource, wikivoyage, wiktionary)', required=False)
    parser.add_argument(
        "-r",
        "--maxretries",
        help="Max retries to download a dump when md5sum doesn't fit. Default: 3",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--start",
        help="Start to download from this project (e.g.: eswiki, itwikisource, etc)",
        required=False,
    )
    args = parser.parse_args()

    maxretries = 3
    if args.maxretries and int(args.maxretries) >= 0:
        maxretries = int(args.maxretries)

    dumpsdomain = "http://dumps.wikimedia.org"
    f = urllib.request.urlopen("%s/backup-index.html" % (dumpsdomain))
    raw = f.read()
    f.close()

    m = re.compile(
        r'<a href="(?P<project>[^>]+)/(?P<date>\d+)">[^<]+</a>: <span class=\'done\'>Dump complete</span>'
    ).finditer(raw)
    projects = []
    for i in m:
        projects.append([i.group("project"), i.group("date")])
    projects.reverse()  # download oldest dumps first
    # projects = [['enwiki', '20130805']]

    start = args.start
    for project, date in projects:
        if start:
            if start != project:
                print(f"Skipping {project}, {date}")
                continue
            else:
                start = ""  # reset

        print("-" * 50, "\n", "Checking", project, date, "\n", "-" * 50)
        time.sleep(1)  # ctrl-c
        f = urllib.request.urlopen(f"{dumpsdomain}/{project}/{date}/")
        htmlproj = f.read()
        # print (htmlproj)
        f.close()

        for dumpclass in [r"pages-meta-history\d*\.xml[^\.]*\.7z"]:
            corrupted = True
            maxretries2 = maxretries
            while corrupted and maxretries2 > 0:
                maxretries2 -= 1
                m = re.compile(
                    r'<a href="(?P<urldump>/%s/%s/%s-%s-%s)">'
                    % (project, date, project, date, dumpclass)
                ).finditer(htmlproj)
                urldumps = []
                # enwiki is splitted in several files, thats why we need a loop
                # here
                for i in m:
                    urldumps.append("{}/{}".format(dumpsdomain, i.group("urldump")))

                # print (urldumps)
                for urldump in urldumps:
                    dumpfilename = urldump.split("/")[-1]
                    path = f"{dumpfilename[0]}/{project}"
                    if not os.path.exists(path):
                        os.makedirs(path)
                    os.system(f"wget -c {urldump} -O {path}/{dumpfilename}")

                    # md5check
                    os.system(f"md5sum {path}/{dumpfilename} > md5")
                    f = open("md5")
                    raw = f.read()
                    f.close()
                    md51 = re.findall(
                        rf"(?P<md5>[a-f0-9]{{32}})\s+{path}/{dumpfilename}", raw
                    )[0]
                    print(md51)

                    f = urllib.request.urlopen(
                        "%s/%s/%s/%s-%s-md5sums.txt"
                        % (dumpsdomain, project, date, project, date)
                    )
                    raw = f.read()
                    f.close()
                    f = open(f"{path}/{project}-{date}-md5sums.txt", "w")
                    f.write(raw)
                    f.close()
                    md52 = re.findall(
                        r"(?P<md5>[a-f0-9]{32})\s+%s" % (dumpfilename), raw
                    )[0]
                    print(md52)

                    if md51 == md52:
                        print(r"md5sum is correct for this file, horay! \o/")
                        print("\n" * 3)
                        corrupted = False
                    else:
                        os.remove(f"{path}/{dumpfilename}")


if __name__ == "__main__":
    main()
