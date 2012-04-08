#!/usr/bin/python
# -*- coding: utf-8 -*-

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

import os
import re
import sys
import time

import dumpgenerator

wikis = open(sys.argv[1], 'r').read().splitlines()
for wiki in wikis:
    wiki = wiki.lower()
    prefix = dumpgenerator.domain2prefix(config={'api': wiki})
    
    #check if compressed, in that case it is finished
    compressed = False
    for dirname, dirnames, filenames in os.walk('.'):
        if dirname == '.':
            for f in filenames:
                if f.startswith(prefix) and f.endswith('.7z'):
                    compressed = True
                    zipfilename = f
    
    if compressed:
        print 'Skiping... This wiki was downloaded and compressed before in', zipfilename
        continue
    
    #download
    started = False #was this wiki download started before? then resume
    wikidir = ''
    for dirname, dirnames, filenames in os.walk('.'):
        if dirname == '.':
            for d in dirnames:
                if d.startswith(prefix):
                    wikidir = d
                    started = True
    
    if started and wikidir: #then resume
        print 'Resuming download, using directory', wikidir
        os.system('python dumpgenerator.py --api=%s --xml --images --resume --path=%s' % (wiki, wikidir))
    else: #download from scratch
        os.system('python dumpgenerator.py --api=%s --xml --images' % wiki)
        #save wikidir now
        for dirname, dirnames, filenames in os.walk('.'):
            if dirname == '.':
                for d in dirnames:
                    if d.startswith(prefix):
                        wikidir = d
    
    #compress
    if wikidir and prefix:
        time.sleep(1)
        os.chdir(wikidir)
        print 'Changed directory to', os.getcwd()
        os.system('grep "<title>" *.xml -c;grep "<page>" *.xml -c;grep "</page>" *.xml -c;grep "<revision>" *.xml -c;grep "</revision>" *.xml -c')
        os.system('7z a ../%s-wikidump.7z %s-history.xml %s-titles.txt %s-images.txt index.html Special:Version.html errors.log images/' % (prefix, prefix, prefix, prefix))
        os.system('7z a ../%s-history.xml.7z %s-history.xml %s-titles.txt index.html Special:Version.html errors.log' % (prefix, prefix, prefix))
        os.chdir('..')
        print 'Changed directory to', os.getcwd()
        time.sleep(1)

