# Copyright (C) 2016 WikiTeam
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
import urllib

import pywikibot
from pywikibot import pagegenerators


def main():
    site = pywikibot.Site("wikiapiary", "wikiapiary")
    catname = "Category:Website"
    cat = pywikibot.Category(site, catname)
    gen = pagegenerators.CategorizedPageGenerator(cat, start="!")
    pre = pagegenerators.PreloadingGenerator(gen)

    for page in pre:
        if page.isRedirectPage():
            continue

        wtitle = page.title()
        wtext = page.text

        # if not wtitle.startswith('5'):
        #    continue

        if re.search("Internet Archive", wtext):
            # print('It has IA parameter')
            pass
        else:
            print("\n", "#" * 50, "\n", wtitle, "\n", "#" * 50)
            print("https://wikiapiary.com/wiki/%s" % (re.sub(" ", "_", wtitle)))
            print("Missing IA parameter")

            if re.search(r"(?i)API URL=http", wtext):
                apiurl = re.findall(r"(?i)API URL=(http[^\n]+?)\n", wtext)[0]
                print("API:", apiurl)
            else:
                print("No API found in WikiApiary, skiping")
                continue

            indexurl = "index.php".join(apiurl.rsplit("api.php", 1))
            urliasearch = (
                'https://archive.org/search.php?query=originalurl:"%s" OR originalurl:"%s"'
                % (apiurl, indexurl)
            )
            f = urllib.request.urlopen(urliasearch)
            raw = f.read().decode("utf-8")
            if re.search(r"(?i)Your search did not match any items", raw):
                print("No dumps found at Internet Archive")
            else:
                itemidentifier = re.findall(r'<a href="/details/([^ ]+?)" title=', raw)[
                    0
                ]
                itemurl = "https://archive.org/details/%s" % (itemidentifier)
                print("Item found:", itemurl)

                metaurl = "https://archive.org/download/{}/{}_files.xml".format(
                    itemidentifier,
                    itemidentifier,
                )
                g = urllib.request.urlopen(metaurl)
                raw2 = g.read().decode("utf-8")
                raw2 = raw2.split("</file>")
                itemfiles = []
                for raw2_ in raw2:
                    try:
                        x = re.findall(
                            r'(?im)<file name="[^ ]+-(\d{8})-[^ ]+" source="original">',
                            raw2_,
                        )[0]
                        y = re.findall(r"(?im)<size>(\d+)</size>", raw2_)[0]
                        itemfiles.append([int(x), int(y)])
                    except:
                        pass

                itemfiles.sort(reverse=True)
                print(itemfiles)
                itemdate = (
                    str(itemfiles[0][0])[0:4]
                    + "/"
                    + str(itemfiles[0][0])[4:6]
                    + "/"
                    + str(itemfiles[0][0])[6:8]
                )
                itemsize = itemfiles[0][1]

                iaparams = """|Internet Archive identifier={}
|Internet Archive URL={}
|Internet Archive added date={} 00:00:00
|Internet Archive file size={}""".format(
                    itemidentifier,
                    itemurl,
                    itemdate,
                    itemsize,
                )
                newtext = page.text
                newtext = re.sub(r"(?im)\n\}\}", "\n%s\n}}" % (iaparams), newtext)

                if page.text != newtext:
                    pywikibot.showDiff(page.text, newtext)
                    page.text = newtext
                    page.save(
                        "BOT - Adding dump details: %s, %s, %s bytes"
                        % (itemidentifier, itemdate, itemsize),
                        botflag=True,
                    )


if __name__ == "__main__":
    main()
