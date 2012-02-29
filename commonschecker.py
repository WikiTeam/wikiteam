#!/usr/bin/python
# -*- coding: utf8 -*-

# Copyright (C) 2011-2012 WikiTeam
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
import zipfile

def welcome():
    """  """
    print "#"*73
    print """# Welcome to CommonsChecker 0.1 by WikiTeam (GPL v3)                    #
# More info at: http://code.google.com/p/wikiteam/                      #"""
    print "#"*73
    print ''
    print "#"*73
    print """# Copyright (C) 2011-2012 WikiTeam                                      #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #"""
    print "#"*73
    print ''

def main():
    welcome()
    
    startdate = ''
    enddate = ''
    delta = datetime.timedelta(days=1) #chunks by day
    if len(sys.argv) == 1:
        print 'Usage example: python script.py 2005-01-01 2005-01-10 [to check the first 10 days of 2005]'
        sys.exit()
    elif len(sys.argv) == 2: #use sys.argv[1] as start and enddata, just check a day
        startdate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        enddate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    elif len(sys.argv) == 3:
        startdate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        enddate = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d')
    else:
        sys.exit()
    
    print "Checking Wikimedia Commons files from %s to %s" % (startdate.strftime('%Y-%m-%d'), enddate.strftime('%Y-%m-%d'))
    while startdate <= enddate:
        print '== %s ==' % (startdate.strftime('%Y-%m-%d'))
        filenamecsv = startdate.strftime('%Y-%m-%d.csv')
        filenamezip = startdate.strftime('%Y-%m-%d.zip')
        if os.path.exists(filenamecsv):
            f = csv.reader(open(filenamecsv, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            if os.path.exists(filenamezip):
                zipfiles = zipfile.ZipFile(filenamezip, 'r').infolist()
                errors = []
                for img_name, img_saved_as, img_timestamp, img_user, img_user_text, img_size, img_width, img_height in f:
                    if img_timestamp.startswith(startdate.strftime('%Y%m%d')):
                        #check img_saved_as existence in zip and check size
                        #img_saved_as = unicode(img_saved_as, 'utf-8')
                        ok = False
                        error = 'missing'
                        for i in zipfiles:
                            if i.filename == unicode('%s/%s' % (startdate.strftime('%Y/%m/%d'), img_saved_as), 'utf-8'):
                                if str(i.file_size) == img_size:
                                    ok = True
                                else:
                                    print i.file_size, img_size
                                    error = 'corrupt'
                        if not ok:
                            errors.append([img_saved_as, error])
                if errors:
                    print 'This .zip contains errors:'
                    print '\n'.join(['  -> "%s" is %s' % (filename, error) for filename, error in errors])
                else:
                    print 'No errors found'
            else:
                print 'Error, no %s available' % (filenamezip)
        else:
            print 'Error, no %s available' % (filenamecsv)
        startdate += delta
if __name__ == "__main__":
    main()
