#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (C) 2011-2014 WikiTeam
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

import getopt
import os
import re
import subprocess
import sys
import time
import urllib
import urllib2
from xml.sax.saxutils import quoteattr

import dumpgenerator

# Configuration goes here
# You need a file named keys.txt with access and secret keys, in two different lines
accesskey = open('keys.txt', 'r').readlines()[0].strip()
secretkey = open('keys.txt', 'r').readlines()[1].strip()
# Use --admin if you are a wikiteam collection admin, or specify another collection:
collection = 'opensource'

# Nothing to change below
convertlang = {'ar': 'Arabic', 'de': 'German', 'en': 'English', 'es': 'Spanish', 'fr': 'French', 'it': 'Italian', 'ja': 'Japanese', 'nl': 'Dutch', 'pl': 'Polish', 'pt': 'Portuguese', 'ru': 'Russian'}
listfile = sys.argv[1]
uploadeddumps = []
try:
    uploadeddumps = [l.split(';')[1] for l in open('uploader-%s.log' % (listfile), 'r').read().strip().splitlines()]
except:
    pass
print '%d dumps uploaded previously' % (len(uploadeddumps))

def getParameters(params=[]):
    if not params:
        params = sys.argv[2:]
    config = {
        'prune-directories': False,
        'prune-wikidump': False,
        'collection': collection
    }
    #console params
    try:
        opts, args = getopt.getopt(params, "", ["h", "help", "prune-directories", "prune-wikidump", "admin"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h","--help"):
            usage()
            sys.exit()
        elif o in ("--prune-directories"):
            config['prune-directories'] = True
        elif o in ("--prune-wikidump"):
            config['prune-wikidump'] = True
        elif o in ("--admin"):
            config['collection'] = "wikiteam"
    return config

def usage():
    """  """
    print """uploader.py
This script takes the filename of a list of wikis as argument and uploads their dumps to archive.org.
The list must be a text file with the wiki's api.php URLs, one per line.
Dumps must be in the same directory and follow the -wikidump.7z/-history.xml.7z format
as produced by launcher.py (explained in https://code.google.com/p/wikiteam/wiki/NewTutorial#Publishing_the_dump ).
You need a file named keys.txt with access and secret keys, in two different lines
You also need dumpgenerator.py in the same directory as this script.
Use --help to print this help."""

def log(wiki, dump, msg):
    f = open('uploader-%s.log' % (listfile), 'a')
    f.write('\n%s;%s;%s' % (wiki, dump, msg))
    f.close()

def upload(wikis, config={}):
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
            wikidate = dump.split('-')[1]
            if dump in uploadeddumps:
                if config['prune-directories']:
                    rmline='rm -rf %s-%s-wikidump/' % (wikiname, wikidate)
                    # With -f the deletion might have happened before and we won't know
                    if not os.system(rmline):
                        print 'DELETED %s-%s-wikidump/' % (wikiname, wikidate)
                if config['prune-wikidump'] and dump.endswith('wikidump.7z'):
                        # Simplistic quick&dirty check for the presence of this file in the item
                        stdout, stderr = subprocess.Popen(["md5sum", dump], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                        dumphash = re.sub(' +.+\n?', '', stdout)

                        headers = {'User-Agent': dumpgenerator.getUserAgent()}
                        itemdata = urllib2.Request(url='http://archive.org/metadata/wiki-' + wikiname, headers=headers)
                        if re.search(dumphash, urllib2.urlopen(itemdata).read()):
                            log(wiki, dump, 'verified')
                            rmline='rm -rf %s' % dump
                            if not os.system(rmline):
                                print 'DELETED ' + dump
                            print '%s was uploaded before, skipping...' % (dump)
                            continue
                        else:
                            print 'ERROR: The online item misses ' + dump
                            log(wiki, dump, 'missing')
                            # We'll exit this if and go upload the dump
                else:
                    print '%s was uploaded before, skipping...' % (dump)
                    continue

            time.sleep(0.1)
            wikidate_text = wikidate[0:4]+'-'+wikidate[4:6]+'-'+wikidate[6:8]
            print wiki, wikiname, wikidate, dump

            # Does the item exist already?
            headers = {'User-Agent': dumpgenerator.getUserAgent()}
            itemdata = urllib2.Request(url='http://archive.org/metadata/wiki-' + wikiname, headers=headers)
            if urllib2.urlopen(itemdata).read() == '{}':
                ismissingitem = True
            else:
                ismissingitem = False

            # We don't know a way to fix/overwrite metadata if item exists already:
            # just pass bogus data and save some time
            if ismissingitem:
                #get metadata from api.php
                #first sitename and base url
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
                lang = ''
                try:
                    sitename = re.findall(ur"sitename=\"([^\"]+)\"", xml)[0]
                except:
                    pass
                try:
                    baseurl = re.findall(ur"base=\"([^\"]+)\"", xml)[0]
                except:
                    pass
                try:
                    lang = re.findall(ur"lang=\"([^\"]+)\"", xml)[0]
                except:
                    pass

                if not sitename:
                    sitename = wikiname
                if not baseurl:
                    baseurl = re.sub(ur"(?im)/api\.php", ur"", wiki)
                if lang:
                    lang = convertlang.has_key(lang.lower()) and convertlang[lang.lower()] or lang.lower()

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
                    raw = ''
                    try:
                        f = urllib.urlopen(baseurl)
                        raw = f.read()
                        f.close()
                    except:
                        pass
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
                wikidesc = "<a href=\"%s\">%s</a> dumped with <a href=\"https://github.com/WikiTeam/wikiteam\" rel=\"nofollow\">WikiTeam</a> tools." % (baseurl, sitename)# "<a href=\"http://en.ecgpedia.org/\" rel=\"nofollow\">ECGpedia,</a>: a free electrocardiography (ECG) tutorial and textbook to which anyone can contribute, designed for medical professionals such as cardiac care nurses and physicians. Dumped with <a href=\"https://github.com/WikiTeam/wikiteam\" rel=\"nofollow\">WikiTeam</a> tools."
                wikikeys = ['wiki', 'wikiteam', 'MediaWiki', sitename, wikiname] # ecg; ECGpedia; wiki; wikiteam; MediaWiki
                if not rightsinfourl and not rightsinfotext:
                    wikikeys.append('unknowncopyright')

                wikilicenseurl = rightsinfourl # http://creativecommons.org/licenses/by-nc-sa/3.0/
                wikirights = rightsinfotext # e.g. http://en.ecgpedia.org/wiki/Frequently_Asked_Questions : hard to fetch automatically, could be the output of API's rightsinfo if it's not a usable licenseurl or "Unknown copyright status" if nothing is found.
                wikiurl = wiki # we use api here http://en.ecgpedia.org/api.php
            else:
                print 'Item already exists.'
                lang = 'foo'
                wikititle = 'foo'
                wikidesc = 'foo'
                wikikeys = 'foo'
                wikilicenseurl = 'foo'
                wikirights = 'foo'
                wikiurl = 'foo'

            #creates curl command
            curl = ['curl', '--location',
                '--header', "'x-amz-auto-make-bucket:1'", # Creates the item automatically, need to give some time for the item to correctly be created on archive.org, or everything else will fail, showing "bucket not found" error
                '--header', "'x-archive-queue-derive:0'",
                '--header', "'x-archive-size-hint:%d'" % (os.path.getsize(dump)),
                '--header', "'authorization: LOW %s:%s'" % (accesskey, secretkey),
            ]
            if c == 0:
                curl += ['--header', "'x-archive-meta-mediatype:web'",
                    '--header', "'x-archive-meta-collection:%s'" % (config['collection']),
                    '--header', quoteattr('x-archive-meta-title:' + wikititle),
                    '--header', "'x-archive-meta-description:%s'" % wikidesc.replace("'", r"\'"),
                    '--header', quoteattr('x-archive-meta-language:' + lang),
                    '--header', "'x-archive-meta-last-updated-date:%s'" % (wikidate_text),
                    '--header', "'x-archive-meta-subject:%s'" % ('; '.join(wikikeys)), # Keywords should be separated by ; but it doesn't matter much; the alternative is to set one per field with subject[0], subject[1], ...
                    '--header', quoteattr('x-archive-meta-licenseurl:' + wikilicenseurl),
                    '--header', "'x-archive-meta-rights:%s'" % wikirights.replace("'", r"\'"),
                    '--header', quoteattr('x-archive-meta-originalurl:' + wikiurl),
                ]

            curl += ['--upload-file', "%s" % (dump),
                    "http://s3.us.archive.org/wiki-%s/%s" % (wikiname, dump), # It could happen that the identifier is taken by another user; only wikiteam collection admins will be able to upload more files to it, curl will fail immediately and get a permissions error by s3.
                    '> /dev/null',
                    #FIXME: Must be NUL instead on Windows, how to make compatible?
            ]
            #now also to update the metadata
            #TODO: not needed for the second file in an item
            curlmeta = ['curl --silent',
                '--data-urlencode -target=metadata',
                """--data-urlencode -patch='{"replace":"/last-updated-date", "value":"%s"}'""" % (wikidate_text),
                '--data-urlencode access=' + accesskey,
                '--data-urlencode secret=' + secretkey,
                'http://archive.org/metadata/wiki-' + wikiname,
                '> /dev/null'
            ]
            curlline = ' '.join(curl)
            curlmetaline = ' '.join(curlmeta)
            if not os.system(curlline):
                uploadeddumps.append(dump)
                log(wiki, dump, 'ok')
                if not ismissingitem:
                    os.system(curlmetaline)
            c += 1

def main(params=[]):

    config = getParameters(params=params)
    wikis = open(listfile, 'r').read().strip().splitlines()
    upload(wikis, config)

if __name__ == "__main__":
    main()
