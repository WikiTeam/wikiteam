#!/usr/bin/python
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

import os
import re
import time

f = open('wikkii.txt', 'r')
wikis = f.read().splitlines()
f.close()

for wiki in wikis:
    os.system('python ../dumpgenerator.py --index=%s/w/index.php --xml --images' % wiki)
    wikiname = re.sub(r'(\.|^www\.)', '', wiki.split('://')[1])
    wikiname = re.sub('-', '_', wikiname)
    wikidir = ''
    for dirname, dirnames, filenames in os.walk('.'):
        if dirname == '.':
            for d in dirnames:
                if d.startswith(wikiname):
                    wikidir = d
    prefix = wikidir.split('-wikidump')[0]
    
    if wikidir and prefix:
        os.chdir(wikidir)
        print 'Changed directory to', os.getcwd()
        os.system('grep "<title>" *.xml -c;grep "<page>" *.xml -c;grep "</page>" *.xml -c;grep "<revision>" *.xml -c;grep "</revision>" *.xml -c')
        os.system('7z a ../%s-wikidump.7z %s-history.xml %s-titles.txt %s-images.txt index.html Special:Version.html errors.log images/' % (prefix, prefix, prefix, prefix))
        os.system('7z a ../%s-history.xml.7z %s-history.xml %s-titles.txt index.html Special:Version.html errors.log' % (prefix, prefix, prefix))
        os.chdir('..')
        print 'Changed directory to', os.getcwd()
        time.sleep(1)

