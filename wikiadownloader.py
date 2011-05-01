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

import datetime
import os
import re
import sys
import urllib

def month2num(month=''):
    month = month.strip().lower()
    if month in ['january', 'gen', 'janwoar', 'januarie', 'ocak', 'taneaksat']:
        return '01'
    elif month in ['february', ]:
        return '02'
    elif month in ['march', ]:
        return '03'
    elif month in ['april', ]:
        return '04'
    elif month in ['may', ]:
        return '05'
    elif month in ['june', ]:
        return '06'
    elif month in ['july', ]:
        return '07'
    elif month in ['august', ]:
        return '08'
    elif month in ['september', ]:
        return '09'
    elif month in ['october', ]:
        return '10'
    elif month in ['november', ]:
        return '11'
    elif month in ['december', 'desember']:
        return '12'
    sys.exit()

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
    path = '%s/%s/%s' % (prefix[0], prefix[0:2], prefix)
    
    f = urllib.urlopen('%s/wiki/Special:Statistics' % (wiki))
    html = f.read()
    #print html
    f.close()
    
    m = re.compile(r'(?i)<a href="(?P<urldump>http://[^<>]+pages_(?P<dump>current|full)\.xml\.gz)">(?P<hour>\d\d:\d\d), (?P<month>[a-z]+) (?P<day>\d+), (?P<year>\d+)</a>').finditer(html)
    for i in m:
        urldump = i.group("urldump")
        dump = i.group("dump")
        hour = i.group("hour")
        month = i.group("month")
        day = i.group("day")
        year = i.group("year")
        print urldump, dump, hour, month, day, year
        
        date = datetime.datetime(year=int(year), month=int(month2num(month=month)), day=int(day))
        
        print 'Downloading', wiki
        if not os.path.exists(path):
            os.makedirs(path)
        
        os.system('wget -c "%s" -O %s/%s-%s-pages-meta-%s.gz' % (urldump, path, prefix, date.strftime('%Y%m%d'), dump.lower() == 'current' and 'current' or 'history'))
