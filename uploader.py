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

# Keys: http://archive.org/account/s3.php
# Documentation: http://archive.org/help/abouts3.txt
# https://wiki.archive.org/twiki/bin/view/Main/IAS3BulkUploader
# http://en.ecgpedia.org/api.php?action=query&meta=siteinfo&siprop=general|rightsinfo&format=xml

import os
import re
import subprocess
import sys
import time
import urllib
import urllib2

import dumpgenerator

listfile = sys.argv[1]

# Configuration goes here
# You need a file named keys.txt with access and secret keys, in two different lines
accesskey = open('keys.txt', 'r').readlines()[0].strip()
secretkey = open('keys.txt', 'r').readlines()[1].strip()
collection = 'wikiteam' # Replace with "opensource" if you are not an admin of the collection

# Nothing to change below
def log(wiki, dump, msg):
    f = open('uploader-%s.log' % (listfile), 'a')
    f.write('\n%s;%s;%s' % (wiki, dump, msg))
    f.close()

def upload(wikis):
    for wiki in wikis:
        print "#"*73
        print "# Uploading", wiki
        print "#"*73
        wiki = wiki.lower()
        prefix = dumpgenerator.domain2prefix(config={'api': wiki})
    
        wikiname = prefix.split('-')[0]
        dumps = []
        for dirname, dirnames, filenames in os.walk('.'):
            if dirname == '.':
                for f in filenames:
                    if f.startswith('%s-' % (wikiname)) and (f.endswith('-wikidump.7z') or f.endswith('-history.xml.7z')):
                        dumps.append(f)
                break

        c = 0
        for dump in dumps:
            time.sleep(0.1)
            wikidate = dump.split('-')[1]
            wikidate_text = wikidate[0:4]+'-'+wikidate[4:6]+'-'+wikidate[6:8]
            print wiki, wikiname, wikidate, dump
            
            #get metadata from api.php
            #first sitename and base url
            headers = {'User-Agent': dumpgenerator.getUserAgent()}
            params = {'action': 'query', 'meta': 'siteinfo', 'format': 'xml'}
            data = urllib.urlencode(params)
            req = urllib2.Request(url=wiki, data=data, headers=headers)
            xml = ''
            try:
                f = urllib2.urlopen(req)
                xml = f.read()
                f.close()
            except:
                pass
            
            sitename = ''
            baseurl = ''
            try:
                sitename = re.findall(ur"sitename=\"([^\"]+)\"", xml)[0]
                baseurl = re.findall(ur"base=\"([^\"]+)\"", xml)[0]
            except:
                pass
            
            if not sitename:
                sitename = wikiname
            if not baseurl:
                baseurl = re.sub(ur"(?im)/api\.php", ur"", wiki)
            
            #now copyright info from API
            params = {'action': 'query', 'siprop': 'general|rightsinfo', 'format': 'xml'}
            data = urllib.urlencode(params)
            req = urllib2.Request(url=wiki, data=data, headers=headers)
            xml = ''
            try:
                f = urllib2.urlopen(req)
                xml = f.read()
                f.close()
            except:
                pass
            
            rightsinfourl = ''
            rightsinfotext = ''
            try:
                rightsinfourl = re.findall(ur"rightsinfo url=\"([^\"]+)\"", xml)[0]
                rightsinfotext = re.findall(ur"text=\"([^\"]+)\"", xml)[0]
            except:
                pass
            
            #or copyright info from #footer in mainpage
            if baseurl and not rightsinfourl and not rightsinfotext:
                f = urllib.urlopen(baseurl)
                raw = f.read()
                f.close()
                rightsinfotext = ''
                rightsinfourl = ''
                try:
                    rightsinfourl = re.findall(ur"<link rel=\"copyright\" href=\"([^\"]+)\" />", raw)[0]
                except:
                    pass
                try:
                    rightsinfotext = re.findall(ur"<li id=\"copyright\">([^\n\r]*?)</li>", raw)[0]
                except:
                    pass
                if rightsinfotext and not rightsinfourl:
                    rightsinfourl = baseurl + '#footer'
            
            #retrieve some info from the wiki
            wikititle = "Wiki - %s" % (sitename) # Wiki - ECGpedia
            wikidesc = "<a href=\"%s\">%s</a> dumped with <a href=\"http://code.google.com/p/wikiteam/\" rel=\"nofollow\">WikiTeam</a> tools." % (baseurl, sitename)# "<a href=\"http://en.ecgpedia.org/\" rel=\"nofollow\">ECGpedia,</a>: a free electrocardiography (ECG) tutorial and textbook to which anyone can contribute, designed for medical professionals such as cardiac care nurses and physicians. Dumped with <a href=\"http://code.google.com/p/wikiteam/\" rel=\"nofollow\">WikiTeam</a> tools."
            wikikeys = ['wiki', 'wikiteam', 'MediaWiki', sitename, wikiname] # ecg; ECGpedia; wiki; wikiteam; MediaWiki
            if not rightsinfourl and not rightsinfotext:
                wikikeys.append('unknowncopyright')
            
            wikilicenseurl = rightsinfourl # http://creativecommons.org/licenses/by-nc-sa/3.0/
            wikirights = rightsinfotext # e.g. http://en.ecgpedia.org/wiki/Frequently_Asked_Questions : hard to fetch automatically, could be the output of API's rightsinfo if it's not a usable licenseurl or "Unknown copyright status" if nothing is found.
            wikiurl = wiki # we use api here http://en.ecgpedia.org/api.php
                        
            #creates curl command
            curl = ['curl', '--location', 
                '--header', "'x-amz-auto-make-bucket:1'", # Creates the item automatically, need to give some time for the item to correctly be created on archive.org, or everything else will fail, showing "bucket not found" error
                '--header', "'x-archive-queue-derive:0'",
                '--header', "'x-archive-size-hint:%d'" % (os.path.getsize(dump)), 
                '--header', "'authorization: LOW %s:%s'" % (accesskey, secretkey),
            ]
            if c == 0:
                curl += ['--header', "'x-archive-meta-mediatype:web'",
                    '--header', "'x-archive-meta-collection:%s'" % (collection),
                    '--header', "'x-archive-meta-title:%s'" % (wikititle),
                    '--header', "'x-archive-meta-description:%s'" % (wikidesc),
                    '--header', "'x-archive-meta-subject:%s'" % ('; '.join(wikikeys)), # Keywords should be separated by ; but it doesn't matter much; the alternative is to set one per field with subject[0], subject[1], ...
                    '--header', "'x-archive-meta-licenseurl:%s'" % (wikilicenseurl),
                    '--header', "'x-archive-meta-rights:%s'" % (wikirights),
                    '--header', "'x-archive-meta-originalurl:%s'" % (wikiurl),
                ]
            
            curl += ['--upload-file', "%s" % (dump),
                    "http://s3.us.archive.org/wiki-%s/%s" % (wikiname, dump), # It could happen that the identifier is taken by another user; only wikiteam collection admins will be able to upload more files to it, curl will fail immediately and get a permissions error by s3.
            ]
            curlline = ' '.join(curl)
            os.system(curlline)
            c += 1
            log(wiki, dump, 'ok')

def main():
    wikis = open(listfile, 'r').read().strip().splitlines()
    upload(wikis)

if __name__ == "__main__":
    main()
