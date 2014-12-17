#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# wikia.py List of not archived Wikia wikis
# Downloads Wikia's dumps and lists wikis which have none.
# TODO: check date
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

import subprocess
import re
from wikitools import wiki, api

def getlist(wikia, wkfrom = 1, wkto = 1000):
    params = {'action': 'query', 'list': 'wkdomains', 'wkactive': '1', 'wkfrom': wkfrom, 'wkto': wkto,}
    request = api.APIRequest(wikia, params)
    return request.query()['query']['wkdomains']

def getall():
    wikia = wiki.Wiki('http://community.wikia.com/api.php')
    offset = 0
    limit = 1000
    domains = {}
    while True:
        list = getlist(wikia, offset, limit)
        if list:
            domains = dict(domains.items() + list.items() )
            offset += 1000
        else:
            break
    return domains

def main():
    domains = getall()
    undumped = []
    for i in domains:
        #print domains
        dbname = domains[i]['domain'].replace('.wikia.com', '').translate('-_.')
        dbname = re.escape(dbname)
        base = 'http://s3.amazonaws.com/wikia_xml_dumps/' + dbname[0] + '/' \
            + dbname[0] + dbname[1] + '/' + dbname
        full = base + '_pages_full.xml.gz'
        current = base + '_pages_current.xml.gz'
        images = base + '_images.tar'
        try:
            subprocess.check_call(['wget', '-e', 'robots=off', '-nc', '-a', 'wikia.log', full])
            # Use this instead, and comment out the next try, to only list.
            #subprocess.check_call(['curl', '-I', full])
        except:
            undumped += dbname

        try:
            subprocess.check_call(['wget', '-e', 'robots=off', '-nc', '-a', 'wikia.log', current])
            subprocess.check_call(['wget', '-e', 'robots=off', '-nc', '-a', 'wikia.log', images])
        except:
            pass
    print undumped

if __name__ == '__main__':
    main()
