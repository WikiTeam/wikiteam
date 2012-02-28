#!/usr/bin/python
# -*- coding: utf8 -*-

# Copyright (C) 2012 WikiTeam
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
import datetime
try:
    from hashlib import md5
except ImportError:             # Python 2.4 compatibility
    from md5 import new as md5
import os
import re
import sys

filename = 'commonssql.csv'
filename = 'a.csv'
startdate = ''
enddate = ''
delta = datetime.timedelta(days=1)
if len(sys.argv) == 1:
    print 'Usage: python script.py 2005-01-01 2005-01-10 [to download the first 10 days of 2005]'
    sys.exit()
elif len(sys.argv) == 2:
    startdate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    enddate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
elif len(sys.argv) == 3:
    startdate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    enddate = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d')
else:
    sys.exit()

print "Downloading Wikimedia Commons files from %s to %s" % (startdate.strftime('%Y-%m-%d'), enddate.strftime('%Y-%m-%d'))
while startdate <= enddate:
    print '==', startdate.strftime('%Y-%m-%d'), '=='
    path = startdate.strftime('%Y/%m/%d')
    filenamezip = startdate.strftime('%Y-%m-%d.zip')
    try:
        os.makedirs(path)
    except:
        pass
    c = 1
    f = csv.reader(open(filename, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for img_name, img_timestamp, img_user, img_user_text, img_size, img_width, img_height in f:
        if c != 1:
            img_name = unicode(img_name, 'utf-8')
            original_name = img_name
            if re.search(ur"(?m)^\d{14}\!", original_name):#removing XXXXXXX! from name if present
                original_name = original_name[15:]
            img_user_text = unicode(img_user_text, 'utf-8')
            if img_timestamp.startswith(startdate.strftime('%Y%m%d')):
                original_name_ = re.sub(r'"', r'\"', re.sub(r' ', r'_', original_name.encode('utf-8'))) # do not use ur'', it is encoded
                img_name_ = re.sub(r'"', r'\"', re.sub(r' ', r'_', img_name.encode('utf-8'))) # do not use ur'', it is encoded
                print img_name, img_name_, img_timestamp
                md5_ = md5(re.sub(' ', '_', original_name.encode("utf-8"))).hexdigest() # do not use img_name_, md5 needs the original name without \"
                if original_name != img_name:
                    os.system('wget -c "http://upload.wikimedia.org/wikipedia/commons/archive/%s/%s/%s" -O "%s/%s"' % (md5_[0], md5_[0:2], img_name_, path, img_name_))
                    if not os.path.getsize('%s/%s' % (path, img_name_)): #empty file?, false XXXXXX! begining like this  http://commons.wikimedia.org/wiki/File:20041028210012!Pilar.jpg ? ok, restore original_name to ! version
                        #recalculate md5 and other variables that use original_name as source
                        original_name = img_name
                        original_name_ = re.sub(r'"', r'\"', re.sub(r' ', r'_', original_name.encode('utf-8')))
                        md5_ = md5.new(re.sub(' ', '_', original_name.encode("utf-8"))).hexdigest()
                        #redownload, now without /archive/ subpath
                        os.system('wget -c "http://upload.wikimedia.org/wikipedia/commons/%s/%s/%s" -O "%s/%s"' % (md5_[0], md5_[0:2], img_name_, path, img_name_))
                else:
                    os.system('wget -c "http://upload.wikimedia.org/wikipedia/commons/%s/%s/%s" -O "%s/%s"' % (md5_[0], md5_[0:2], img_name_, path, img_name_))
                os.system('curl -d "&pages=File:%s&history=1&action=submit" http://commons.wikimedia.org/w/index.php?title=Special:Export -o "%s/%s.desc"' % (original_name_, path, img_name_))
        c += 1
    #zip files
    os.system('zip -9 %s %s/*' % (filenamezip, path))
    startdate += delta

