#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (C) 2011-2016 WikiTeam
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

# Instructions: https://github.com/WikiTeam/wikiteam/wiki/Tutorial#Download_a_list_of_wikis
# Requires python 2.7 or more (for subprocess.check_output)

import os
import re
import subprocess
import sys
import time

import dumpgenerator

def main():
    if len(sys.argv) < 2:
        print 'python script.py file-with-apis.txt'
        sys.exit()

    print 'Reading list of APIs from', sys.argv[1]
    wikis = open(sys.argv[1], 'r').read().splitlines()
    print '%d APIs found' % (len(wikis))

    for wiki in wikis:
        print "#"*73
        print "# Downloading", wiki
        print "#"*73
        wiki = wiki.lower()
        # Make the prefix in standard way; api and index must be defined, not important which is which
        prefix = dumpgenerator.domain2prefix(config={'api': wiki, 'index': wiki})

        #check if compressed, in that case dump was finished previously
        compressed = False
        for f in os.listdir('.'):
            if f.startswith(prefix) and f.endswith('.7z'):
                compressed = True
                zipfilename = f
                break #stop searching, dot not explore subdirectories

        if compressed:
            print 'Skipping... This wiki was downloaded and compressed before in', zipfilename
            # Get the archive's file list.
            if ( ( ( sys.version_info[0] == 3 ) and ( sys.version_info[1] > 0 ) ) or ( ( sys.version_info[0] == 2 ) and ( sys.version_info[1] > 6 ) ) ):
                archivecontent = subprocess.check_output (['7z', 'l', zipfilename])
                if re.search(ur"%s.+-history\.xml" % (prefix), archivecontent) is None:
                    # We should perhaps not create an archive in this case, but we continue anyway.
                    print "ERROR: The archive contains no history!"
                if re.search(ur"Special:Version\.html", archivecontent) is None:
                    print "WARNING: The archive doesn't contain Special:Version.html, this may indicate that download didn't finish."
            else:
                print "WARNING: Content of the archive not checked, we need python 2.7+ or 3.1+."
                # TODO: Find a way like grep -q below without doing a 7z l multiple times?
            continue

        #download
        started = False #was this wiki download started before? then resume
        wikidir = ''
        for f in os.listdir('.'):
            # Does not find numbered wikidumps not verify directories
            if f.startswith(prefix) and f.endswith('wikidump'):
                wikidir = f
                started = True
                break #stop searching, dot not explore subdirectories

        # time.sleep(60)
        # Uncomment what above and add --delay=60 in the dumpgenerator.py calls below for broken wiki farms
        # such as editthis.info, wiki-site.com, wikkii (adjust the value as needed;
        # typically they don't provide any crawl-delay value in their robots.txt).
        if started and wikidir: #then resume
            print 'Resuming download, using directory', wikidir
            subprocess.call('./dumpgenerator.py --api=%s --xml --images --resume --path=%s' % (wiki, wikidir), shell=True)
        else: #download from scratch
            subprocess.call('./dumpgenerator.py --api=%s --xml --images --delay=1' % wiki, shell=True)
            started = True
            #save wikidir now
            for f in os.listdir('.'):
                # Does not find numbered wikidumps not verify directories
                if f.startswith(prefix) and f.endswith('wikidump'):
                    wikidir = f
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
            subprocess.call('grep "<title>" *.xml -c;grep "<page>" *.xml -c;grep "</page>" *.xml -c;grep "<revision>" *.xml -c;grep "</revision>" *.xml -c', shell=True)
            # Make a non-solid archive with all the text and metadata at default compression. You can also add config.txt if you don't care about your computer and user names being published or you don't use full paths so that they're not stored in it.
            subprocess.call('7z' + ' a -ms=off ../%s-history.xml.7z.tmp %s-history.xml %s-titles.txt index.html Special:Version.html errors.log siteinfo.json' % (prefix, prefix, prefix), shell=True)
            subprocess.call('mv' + ' ../%s-history.xml.7z.tmp ../%s-history.xml.7z' % (prefix, prefix), shell=True)
            # Now we add the images, if there are some, to create another archive, without recompressing everything, at the min compression rate, higher doesn't compress images much more.
            subprocess.call('cp' + ' ../%s-history.xml.7z ../%s-wikidump.7z.tmp' % (prefix, prefix), shell=True)
            subprocess.call('7z' + ' a -ms=off -mx=1 ../%s-wikidump.7z.tmp %s-images.txt images/' % (prefix, prefix), shell=True)
            subprocess.call('mv' + ' ../%s-wikidump.7z.tmp ../%s-wikidump.7z' % (prefix, prefix), shell=True)
            os.chdir('..')
            print 'Changed directory to', os.getcwd()
            time.sleep(1)

if __name__ == "__main__":
    main()
