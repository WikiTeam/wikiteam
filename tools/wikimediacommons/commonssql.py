#!/usr/bin/env python3

# Copyright (C) 2012-2016 WikiTeam developers
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
import re
import sys

import pymysql


def main():
    year = int(sys.argv[1])
    filename = f"commonssql-{year}.csv"
    with open(filename, "w") as f:
        f.write(
            "img_name|img_timestamp|img_user|img_user_text|img_size|img_width|img_height\n"
        )
    # http://www.mediawiki.org/wiki/Manual:Image_table
    # http://www.mediawiki.org/wiki/Manual:Oldimage_table

    queries = [
        "SELECT /* commonssql.py SLOW_OK */ img_name, img_timestamp, img_user, img_user_text, img_size, img_width, img_height FROM image WHERE img_timestamp>=%d0101000000 AND img_timestamp<=%d1231235959 ORDER BY img_timestamp ASC"
        % (year, year),
        "SELECT /* commonssql.py SLOW_OK */ oi_archive_name AS img_name, oi_timestamp AS img_timestamp, oi_user AS img_user, oi_user_text AS img_user_text, oi_size AS img_size, oi_width AS img_width, oi_height AS img_height FROM oldimage WHERE oi_deleted=0 AND oi_timestamp>=%d0101000000 AND oi_timestamp<=%d1231235959 ORDER BY oi_timestamp ASC"
        % (year, year),  # do not get unavailable images
    ]

    f = csv.writer(
        open(filename, "a"), delimiter="|", quotechar='"', quoting=csv.QUOTE_MINIMAL
    )
    conn = pymysql.connect(
        host="s4.labsdb",
        db="commonswiki_p",
        read_default_file="~/replica.my.cnf",
        use_unicode=True,
    )
    for query in queries:
        conn.query(query)
        r = conn.store_result()
        c = 0
        row = r.fetch_row(maxrows=1, how=1)
        rows = []
        while row:
            if len(row) == 1:
                img_name = re.sub(" ", "_", row[0]["img_name"])
                img_timestamp = row[0]["img_timestamp"]
                img_user = row[0]["img_user"]
                img_user_text = re.sub(" ", "_", row[0]["img_user_text"])
                img_size = row[0]["img_size"]
                img_width = row[0]["img_width"]
                img_height = row[0]["img_height"]

                rows.append(
                    [
                        img_name,
                        img_timestamp,
                        img_user,
                        img_user_text,
                        img_size,
                        img_width,
                        img_height,
                    ]
                )
                c += 1
                if c % 10000 == 0:
                    print(c)
                    f.writerows(rows)
                    rows = []
            row = r.fetch_row(maxrows=1, how=1)
        f.writerows(rows)


if __name__ == "__main__":
    main()
