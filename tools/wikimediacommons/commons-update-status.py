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

import json
import urllib


def main():
    queryurl = "https://archive.org/advancedsearch.php?q=collection%3Awikimediacommons&fl[]=identifier&sort[]=&sort[]=&sort[]=&rows=1000&page=1&output=json&callback=callback"
    raw = urllib.request.urlopen(queryurl).read()
    raw = raw.split("callback(")[1].strip(")")
    result = json.loads(raw)["response"]["docs"]

    identifiers = {}
    for item in result:
        identifier = item["identifier"]
        if "wikimediacommons-20" in identifier:
            date = identifier.split("wikimediacommons-")[1]
            t = date.split("-")
            if len(t) == 1:
                if len(t[0]) == 4:  # YYYY
                    identifiers[t[0]] = identifier
                elif len(t[0]) == 6:  # YYYYMM
                    identifiers[f"{t[0][:4]}-{t[0][4:6]}"] = identifier
                elif len(t[0]) == 8:  # YYYYMMDD
                    identifiers[f"{t[0][:4]}-{t[0][4:6]}-{t[0][6:8]}"] = identifier
                else:
                    print("ERROR, dont understand date format in %s" % (identifier))
            elif len(t) == 2:
                if len(t[0]) == 4 and len(t[1]) == 2:  # YYYY-MM
                    identifiers[f"{t[0]}-{t[1]}"] = identifier
                else:
                    print("ERROR, dont understand date format in %s" % (identifier))
            elif len(t) == 3:
                if len(t[0]) == 4 and len(t[1]) == 2 and len(t[2]) == 2:  # YYYY-MM-DD
                    identifiers[f"{t[0]}-{t[1]}-{t[2]}"] = identifier
                else:
                    print("ERROR, dont understand date format in %s" % (identifier))

    identifiers_list = [[k, v] for k, v in identifiers.items()]
    identifiers_list.sort()

    rows = [
        f"|-\n| {k} || [https://archive.org/details/{v} {v}] || ??? || ???"
        for k, v in identifiers_list
    ]
    output = """
{| class="wikitable sortable"
! Date !! Identifier !! Files !! Size (GB)
%s
|}""" % (
        "\n".join(rows)
    )
    print(output)


if __name__ == "__main__":
    main()
