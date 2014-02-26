#!/usr/bin/env python2
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

f = open('wikia.com', 'r')
wikia = f.read().strip().split('\n')
f.close()

print len(wikia), 'wikis in Wikia'

start = '!'
if len(sys.argv) > 1:
    start = sys.argv[1]

for wiki in wikia:
    prefix = wiki.split('http://')[1]
    if prefix < start:
        continue
    print wiki
    path = '%s/%s/%s' % (prefix[0], prefix[0:2], prefix)
    
    f = urllib.urlopen('%s/wiki/Special:Statistics' % (wiki))
    html = f.read()
    #print html
    f.close()
    
    m = re.compile(r'(?i)<a href="(?P<urldump>http://[^<>]+pages_(?P<dump>current|full)\.xml\.gz)">(?P<hour>\d\d:\d\d), (?P<month>[a-z]+) (?P<day>\d+), (?P<year>\d+)</a>').finditer(html)
    for i in m:
        urldump = i.group("urldump")
        dump = i.group("dump")

        print 'Downloading', wiki
        if not os.path.exists(path):
            os.makedirs(path)
        
        f = urllib.urlopen('%s/index.json' % ('/'.join(urldump.split('/')[:-1])))
        json = f.read()
        f.close()
        #{"name":"pages_full.xml.gz","timestamp":1273755409,"mwtimestamp":"20100513125649"}
        #{"name":"pages_current.xml.gz","timestamp":1270731925,"mwtimestamp":"20100408130525"}
        date = re.findall(r'{"name":"pages_%s.xml.gz","timestamp":\d+,"mwtimestamp":"(\d{8})\d{6}"}' % (dump.lower()), json)[0]
        print urldump, dump, date #, hour, month, day, year
        
        #-q, turn off verbose
        os.system('wget -q -c "%s" -O %s/%s-%s-pages-meta-%s.gz' % (urldump, path, prefix, date, dump.lower() == 'current' and 'current' or 'history'))
