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
import urllib

def welcome():
    """  """
    print "#"*73
    print """# Welcome to CommonsDownloader 0.1 by WikiTeam (GPL v3)                 #
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

def bye():
    """  """
    print "---> Congratulations! Your dump is complete <---"
    print "If you found any bug, report a new issue here (Gmail account required): http://code.google.com/p/wikiteam/issues/list"
    print "If this is a public wiki, please, consider sending us a copy of this dump. Contact us at http://code.google.com/p/wikiteam"
    print "Good luck! Bye!"

def main():
    welcome()
    
    filenamefeed = 'commonssql.csv' # feed
    #filenamefeed = 'a.csv'
    startdate = ''
    enddate = ''
    delta = datetime.timedelta(days=1) #chunks by day
    filenamelimit = 100 #do not change!!!
    if len(sys.argv) == 1:
        print 'Usage example: python script.py 2005-01-01 2005-01-10 [to download the first 10 days of 2005]'
        sys.exit()
    elif len(sys.argv) == 2: #use sys.argv[1] as start and enddata, just download a day
        startdate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        enddate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
    elif len(sys.argv) == 3:
        startdate = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        enddate = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d')
    else:
        sys.exit()
    
    print "Downloading Wikimedia Commons files from %s to %s" % (startdate.strftime('%Y-%m-%d'), enddate.strftime('%Y-%m-%d'))
    while startdate <= enddate:
        print '== %s ==' % (startdate.strftime('%Y-%m-%d'))
        savepath = startdate.strftime('%Y/%m/%d')
        filenamecsv = startdate.strftime('%Y-%m-%d.csv')
        filenamezip = startdate.strftime('%Y-%m-%d.zip')
        c = 0
        f = csv.reader(open(filenamefeed, 'r'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for img_name, img_timestamp, img_user, img_user_text, img_size, img_width, img_height in f:
            if img_timestamp.startswith(startdate.strftime('%Y%m%d')):
                if not c: #first loop
                    try: #create savepath if not exists
                        os.makedirs(savepath)
                    except:
                        pass
                    #csv header
                    h = open(filenamecsv, 'w')
                    h.write('img_name|img_saved_as|img_timestamp|img_user|img_user_text|img_size|img_width|img_height\n')
                    h.close()
                
                """
                wget: md5, quotedname, savepath, savefile
                curl: filedescpage, savepath, savefile.desc
                special cases: oldimage, falseoldimage
                truncatedfilename
                """
                
                img_name = unicode(img_name, 'utf-8')
                img_user_text = unicode(img_user_text, 'utf-8')
                original_name = img_name
                if re.search(ur"(?m)^\d{14}\!", original_name): #removing 20101005024534! (or similar) from name if present
                    original_name = original_name[15:]
                # quote weird chars to avoid errors while wgetting
                img_name_quoted = urllib.quote(img_name)
                # _ ending variables contains no spaces, and \" for command line
                img_name_ = re.sub(r'"', r'\"', re.sub(r' ', r'_', img_name.encode('utf-8'))) # do not use ur'', it is encoded
                original_name_ = re.sub(r'"', r'\"', re.sub(r' ', r'_', original_name.encode('utf-8'))) # do not use ur'', it is encoded
                print img_name, img_name_, img_timestamp
                md5hash = md5(re.sub(' ', '_', original_name.encode("utf-8"))).hexdigest() # do not use image_name, md5 needs the original name and without \"
                img_saved_as = ''
                if len(img_name) > filenamelimit: #truncate filename if it is long
                    img_saved_as = img_name[:filenamelimit] + md5(img_name).hexdigest() + '.' + img_name.split('.')[-1]
                    img_saved_as = re.sub(r' ', r'_', img_saved_as.encode('utf-8')) # do not use ur'', it is encoded
                    img_saved_as_ = re.sub(r'"', r'\"', re.sub(r' ', r'_', img_saved_as.encode('utf-8'))) # do not use ur'', it is encoded
                else:
                    img_saved_as = re.sub(r' ', r'_', img_name.encode('utf-8')) # do not use ur'', it is encoded
                    img_saved_as_ = re.sub(r'"', r'\"', re.sub(r' ', r'_', img_name.encode('utf-8'))) # do not use ur'', it is encoded
                
                #wget file
                if original_name != img_name: #the image is an old version, download using /archive/ path in server
                    os.system('wget -c "http://upload.wikimedia.org/wikipedia/commons/archive/%s/%s/%s" -O "%s/%s"' % (md5hash[0], md5hash[0:2], img_name_quoted, savepath, img_saved_as_))
                    if not os.path.getsize('%s/%s' % (savepath, img_saved_as_)): #empty file?...
                        #probably false 20101005024534! begining like this http://commons.wikimedia.org/wiki/File:20041028210012!Pilar.jpg
                        #ok, restore original_name to ! version and recalculate md5 and other variables that use original_name as source
                        original_name = img_name
                        original_name_ = re.sub(r'"', r'\"', re.sub(r' ', r'_', original_name.encode('utf-8')))
                        md5hash = md5.new(re.sub(' ', '_', original_name.encode("utf-8"))).hexdigest()
                        #redownload, now without /archive/ subpath
                        os.system('wget -c "http://upload.wikimedia.org/wikipedia/commons/%s/%s/%s" -O "%s/%s"' % (md5hash[0], md5hash[0:2], img_name_, savepath, img_saved_as_))
                else:
                    os.system('wget -c "http://upload.wikimedia.org/wikipedia/commons/%s/%s/%s" -O "%s/%s"' % (md5hash[0], md5hash[0:2], img_name_, savepath, img_saved_as_))
                
                #curl .xml description page with full history
                os.system('curl -d "&pages=File:%s&history=1&action=submit" http://commons.wikimedia.org/w/index.php?title=Special:Export -o "%s/%s.desc"' % (original_name_, savepath, img_saved_as_))
                
                #save csv info
                g = csv.writer(open(filenamecsv, 'a'), delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                g.writerow([img_name, img_saved_as, img_timestamp, img_user, img_user_text, img_size, img_width, img_height])
                c += 1
        #zip downloaded files
        os.system('zip -9 %s %s/*' % (filenamezip, savepath))
        startdate += delta
    bye()

if __name__ == "__main__":
    main()
