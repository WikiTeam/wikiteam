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

import re
import os
import time
import urllib

f = urllib.urlopen('http://dumps.wikimedia.org/backup-index.html')
raw = f.read()
f.close()

m = re.compile(r'<a href="(?P<project>[^>]+)/(?P<date>\d+)">[^<]+</a>: <span class=\'done\'>Dump complete</span>').finditer(raw)
projects = []
for i in m:
    projects.append([i.group('project'), i.group('date')])

projects.reverse() #oldest project dump, download first

#projects = [['enwiki', '20110405']]

for project, date in projects:
    time.sleep(1) #ctrl-c
    f = urllib.urlopen('http://dumps.wikimedia.org/%s/%s/' % (project, date))
    htmlproj = f.read()
    #print htmlproj
    f.close()
    
    for dumpclass in ['pages-meta-history\d*\.xml\.7z']:
        corrupted = True
        maxretries = 3
        while corrupted and maxretries > 0:
            maxretries -= 1
            m = re.compile(r'<a href="(?P<urldump>http://[^/>]+/%s/%s/%s-%s-%s)">' % (project, date, project, date, dumpclass)).finditer(htmlproj)
            urldumps = []
            for i in m:
                urldumps.append(i.group('urldump')) #enwiki is splitted in several files
            
            #print urldumps
            for urldump in urldumps:
                dumpfilename = urldump.split('/')[-1]
                path = '%s/%s' % (dumpfilename[0], project)
                if not os.path.exists(path):
                    os.makedirs(path)
                os.system('wget -c %s -O %s/%s' % (urldump, path, dumpfilename))
                
                #md5check
                os.system('md5sum %s/%s > md5' % (path, dumpfilename))
                f = open('md5', 'r')
                raw = f.read()
                f.close()
                md51 = re.findall(r'(?P<md5>[a-f0-9]{32})\s+%s/%s' % (path, dumpfilename), raw)[0]
                print md51
                
                f = urllib.urlopen('http://dumps.wikimedia.org/%s/%s/%s-%s-md5sums.txt' % (project, date, project, date))
                raw = f.read()
                f.close()
                f = open('%s/%s-%s-md5sums.txt' % (path, project, date), 'w')
                f.write(raw)
                f.close()
                md52 = re.findall(r'(?P<md5>[a-f0-9]{32})\s+%s' % (dumpfilename), raw)[0]
                print md52
                
                if md51 == md52:
                    print 'md5sum is correct for this file, horay! \o/'
                    print '\n'*3
                    corrupted = False
                else:
                    os.remove('%s/%s' % (path, dumpfilename))
