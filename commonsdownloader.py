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
import md5
import os
import re
import sys

startdate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
enddate = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d')
delta = datetime.timedelta(days=1)
filename = 'commonssql.csv'

while startdate <= enddate:
    print '==', startdate.strftime('%Y-%m-%d'), '=='
    c = 1
    f = csv.reader(open(filename, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for img_name, img_timestamp, img_user, img_user_text, img_size, img_width, img_height in f:
        if c != 1:
            img_name = unicode(img_name, 'utf-8')
            img_user_text = unicode(img_user_text, 'utf-8')
            if img_timestamp.startswith(startdate.strftime('%Y%m%d')):
                print img_name.encode('utf-8'), img_timestamp
                img_name_ = re.sub('"', '\"', img_name)
                md5_ = md5.new(img_name.encode('utf-8')).hexdigest()
                #os.system('wget -c "http://upload.wikimedia.org/wikipedia/commons/%s/%s/%s" -O "%s' % (md5_[0], md5_[0:2], img_name, img_name_))
                #os.system('curl -d "&pages=File:%s&history=1&action=submit" http://commons.wikimedia.org/w/index.php?title=Special:Export -o "%s.desc' % (img_name_, img_name_))
        c += 1
    startdate += delta

