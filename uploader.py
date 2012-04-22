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

# http://archive.org/account/s3.php
# http://archive.org/help/abouts3.txt
# https://wiki.archive.org/twiki/bin/view/Main/IAS3BulkUploader
# http://en.ecgpedia.org/api.php?action=query&meta=siteinfo&siprop=general|rightsinfo

import os
import re
import subprocess
import urllib

accesskey = ''
secretkey = ''

def upload(wikis):
    for wiki, dumps in wikis.items():
        wikiname = '-'.join(wiki.split('-')[:-1])
        wikidate = wiki.split('-')[-1]
        c = 0
        for dump in dumps:
            print wiki, wikiname, wikidate, dump
            #get api.php
            pass
            
            #retrieve some info from the wiki
            wikititle = "Wiki - " # Wiki - ECGpedia
            wikidesc = "... Dumped with <a href=\"http://code.google.com/p/wikiteam/\" rel=\"nofollow\">WikiTeam</a> tool." # "<a href=\"http://en.ecgpedia.org/\" rel=\"nofollow\">ECGpedia,</a>: a free electrocardiography (ECG) tutorial and textbook to which anyone can contribute, designed for medical professionals such as cardiac care nurses and physicians. Dumped with <a href=\"http://code.google.com/p/wikiteam/\" rel=\"nofollow\">WikiTeam</a> tool."
            wikikeys = [, 'wiki', 'wikiteam', 'MediaWiki'] # ecg; ECGpedia; wiki; wikiteam; MediaWiki
            wikilicenseurl = "" # http://creativecommons.org/licenses/by-nc-sa/3.0/
            wikirights = "" # e.g. http://en.ecgpedia.org/wiki/Frequently_Asked_Questions : hard to fetch automaticall, could be the output of API's rightsinfo if it's not a usable licenseurl or "Unknown copyright status" if nothing is found.
            wikiurl = "" # we use api here http://en.ecgpedia.org/api.php
                        
            #creates curl command
            curl = ['curl', '--location', 
                '--header', "'x-amz-auto-make-bucket:1'",
                '--header', "'x-archive-queue-derive:0'",
                '--header', "'x-archive-size-hint:%d'" % (os.path.getsize(dump)), 
                '--header', "'authorization: LOW %s:%s'" % (accesskey, secretkey),
            ]
            if c == 0:
                curl += ['--header', "'x-archive-meta-mediatype:web'",
                    '--header', "'x-archive-meta-collection:opensource'", #replace with wikiteam if you're an admin of the collection
                    '--header', "'x-archive-meta-title:%s'" % (wikititle),
                    '--header', "'x-archive-meta-description:%s'" % (wikidesc),
                    '--header', "'x-archive-meta-subject:%s'" % ('; '.join(wikikeys)), # keywords should be separated by ; but it doesn't matter much; the alternative is to set one per field with subject[0], subject[1], ...
                    '--header', "'x-archive-meta-licenseurl:%s'" % (wikilicenseurl),
                    '--header', "'x-archive-meta-rights:%s'" % (wikirights),
                    '--header', "'x-archive-meta-originalurl:%s'" % (wikiurl),
                ]
            
            curl += ['--upload-file', "%s" % (dump),
                    "http://s3.us.archive.org/wiki-%s/%s" % (wikiname, dump), # it could happen that the identifier is taken by another user; only wikiteam collection admins will be able to upload more files to it
            ]
            print '\n'.join(curl)
            #log = subprocess.check_output(curl)
            #print log
            c += 1

wikis = {}
def main():
    for dirname, dirnames, filenames in os.walk('.'):
        if dirname == '.':
            for f in filenames:
                if f.endswith('-wikidump.7z') or f.endswith('-history.xml.7z'):
                    wiki = f.split('-wikidump.7z')[0].split('-history.xml.7z')[0]
                    if not wikis.has_key(wiki):
                        wikis[wiki] = []
                    wikis[wiki].append(f)
            break
    
    upload(wikis)

if __name__ == "__main__":
    main()
