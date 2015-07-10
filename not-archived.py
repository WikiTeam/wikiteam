#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# not-archived.py List of not archived wikis, using WikiApiary data
# NOTE: unreliable! https://github.com/WikiApiary/WikiApiary/issues/130
#
# Copyright (C) 2015 WikiTeam developers
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

def getdomain(wiki):
    domain = wiki
    domain = domain.split('://')[1].split('/')[0]
    domain = re.sub(ur'(?im)^www\d*\.', '', domain)
    return domain
    
def main():
    doneurl = 'https://archive.org/advancedsearch.php?q=collection%3A%28wikiteam%29+AND+originalurl%3A[%22http%22+TO+null]&fl[]=description&sort[]=&sort[]=&sort[]=&rows=100000&page=1&output=json&callback=callback'
    f = urllib.urlopen(doneurl)
    wikiurls = re.findall(ur'(?im)<a href=\\"(http[^>]+?)\\" rel=\\"nofollow\\">[^<]+?</a> dumped with', f.read())
    donewikis = [getdomain(wikiurl) for wikiurl in wikiurls]
    #print 'Loaded %d done wikis' % len(donewikis)
    
    offset = 0
    limit = 500
    wikis = []
    while True:
        url = 'https://wikiapiary.com/wiki/Special:Ask/-5B-5BCategory:Website-20not-20archived-5D-5D-20-5B-5BIs-20defunct::False-5D-5D-20-5B-5BIs-20in-20farm::False-5D-5D/-3F%%3DWiki-23/-3FHas-20API-20URL%%3DAPI/-3FHas-20pages-20count%%3DPages/-3FHas-20images-20count%%3DImages/format%%3Dtable/limit%%3D%d/link%%3Dall/sort%%3DHas-20pages-20count,Has-20images-20count/order%%3Dasc/mainlabel%%3DWiki/searchlabel%%3D%%E2%%80%%A6-20further-20results/offset%%3D%d' % (limit, offset)
        f = urllib.urlopen(url)
        raw = f.read()
        m = re.findall(ur'(?im)<tr class="row-(?:odd|even)"><td class="[^<>]+?"><a href="/wiki/[^<>]+?" title="[^<>]+?">([^<>]+?)</a></td><td class="[^<>]+?"><a href="/wiki/[^<>]+?" title="[^<>]+?">[^<>]+?</a></td><td class="[^<>]+?"><a class="external" rel="nofollow" href="([^<>]+?)">[^<>]+?</a></td><td data-sort-value="([^<>]+?)" class="[^<>]+?">[^<>]+?</td><td data-sort-value="([^<>]+?)" class="[^<>]+?">[^<>]+?</td></tr>', raw)
        for i in m:
            domain = getdomain(i[1])
            if domain not in donewikis and not domain.endswith('editthis.info') and not domain.endswith('wiki-site.com'):
                print i[0], i[1], i[2], i[3]
        
        if not re.search(ur'rel="nofollow">Next</a>', raw):
            break
        offset += limit

if __name__ == '__main__':
    main()
