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
import subprocess
import sys
import time

import dumpgenerator

wikis = open(sys.argv[1], 'r').read().splitlines()
for wiki in wikis:
    print "#"*73
    print "# Downloading", wiki
    print "#"*73
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
            break #stop searching, dot not explore subdirectories
    
    if compressed:
        print 'Skipping... This wiki was downloaded and compressed before in', zipfilename
        # Get the archive's file list.
        archivecontent = subprocess.check_output (['7z', 'l', zipfilename])
        if re.search(ur"%s.+-history\.xml" % (prefix), archivecontent) is None:
            # We should perhaps not create an archive in this case, but we continue anyway.
            print "ERROR: The archive contains no history!"
        if re.search(ur"Special:Version\.html", archivecontent) is None:
            print "WARNING: The archive doesn't contain Special:Version.html, this may indicate that download didn't finish."
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
            break #stop searching, dot not explore subdirectories
    
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
                break #stop searching, dot not explore subdirectories
    
    prefix = wikidir.split('-wikidump')[0]
    
    finished = False
    if started and wikidir and prefix:
        if (subprocess.call (['tail -n 1 %s/%s-history.xml | grep -q "</mediawiki>"' % (wikidir, prefix)], shell=True) ):
            print "No </mediawiki> tag found: dump failed, needs fixing; resume didn't work. Exiting."
        else:
            finished = True
    # You can also issue this on your working directory to find all incomplete dumps:
    # tail -n 1 */*-history.xml | grep -Ev -B 1 "</page>|</mediawiki>|==|^$"
    
    #compress
    if finished:
        time.sleep(1)
        os.chdir(wikidir)
        print 'Changed directory to', os.getcwd()
        # Basic integrity check for the xml. The script doesn't actually do anything, so you should check if it's broken. Nothing can be done anyway, but redownloading.
        os.system('grep "<title>" *.xml -c;grep "<page>" *.xml -c;grep "</page>" *.xml -c;grep "<revision>" *.xml -c;grep "</revision>" *.xml -c')
        # Make a non-solid archive with all the text and metadata at default compression. You can also add config.txt if you don't care about your computer and user names being published or you don't use full paths so that they're not stored in it.
        os.system('7z a -ms=off ../%s-history.xml.7z %s-history.xml %s-titles.txt index.html Special:Version.html errors.log' % (prefix, prefix, prefix))
        # Now we add the images, if there are some, to create another archive, without recompressing everything, at the min compression rate, higher doesn't compress images much more.
        os.system('cp ../%s-history.xml.7z ../%s-wikidump.7z' % (prefix, prefix))
        os.system('7z a -ms=off -mx=1 ../%s-wikidump.7z %s-images.txt images/' % (prefix, prefix))
        os.chdir('..')
        print 'Changed directory to', os.getcwd()
        time.sleep(1)
