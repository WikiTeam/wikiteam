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

import getopt
import argparse
import os
import re
import subprocess
import sys
import time
import urllib
import urllib2
import urlparse
import StringIO
from xml.sax.saxutils import quoteattr
from internetarchive import get_item

import dumpgenerator

# You need a file named keys.txt with access and secret keys, in two different lines
accesskey = open('keys.txt', 'r').readlines()[0].strip()
secretkey = open('keys.txt', 'r').readlines()[1].strip()

# Nothing to change below
convertlang = {'ar': 'Arabic', 'de': 'German', 'en': 'English', 'es': 'Spanish', 'fr': 'French', 'it': 'Italian', 'ja': 'Japanese', 'nl': 'Dutch', 'pl': 'Polish', 'pt': 'Portuguese', 'ru': 'Russian'}

def log(wiki, dump, msg, config={}):
    f = open('uploader-%s.log' % (config.listfile), 'a')
    f.write('\n%s;%s;%s' % (wiki, dump, msg))
    f.close()

def upload(wikis, config={}, uploadeddumps=[]):
    headers = {'User-Agent': dumpgenerator.getUserAgent()}
    dumpdir = config.wikidump_dir

    filelist = os.listdir(dumpdir)
    for wiki in wikis:
        print "#"*73
        print "# Uploading", wiki
        print "#"*73
        wiki = wiki.lower()
        configtemp = config
        try:
            prefix = dumpgenerator.domain2prefix(config={'api': wiki})
        except KeyError:
            print "ERROR: could not produce the prefix for %s" % wiki
        config = configtemp

        wikiname = prefix.split('-')[0]
        dumps = []
        for f in filelist:
            if f.startswith('%s-' % (wikiname)) and (f.endswith('-wikidump.7z') or f.endswith('-history.xml.7z')):
                print "%s found" % f
                dumps.append(f)
                # Re-introduce the break here if you only need to upload one file
                # and the I/O is too slow
                # break

        c = 0
        for dump in dumps:
            wikidate = dump.split('-')[1]
            item = get_item('wiki-' + wikiname)
            if dump in uploadeddumps:
                if config.prune_directories:
                    rmline='rm -rf %s-%s-wikidump/' % (wikiname, wikidate)
                    # With -f the deletion might have happened before and we won't know
                    if not os.system(rmline):
                        print 'DELETED %s-%s-wikidump/' % (wikiname, wikidate)
                if config.prune_wikidump and dump.endswith('wikidump.7z'):
                        # Simplistic quick&dirty check for the presence of this file in the item
                        print "Checking content in previously uploaded files"
                        stdout, stderr = subprocess.Popen(["md5sum", dumpdir + '/' + dump], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                        dumphash = re.sub(' +.+\n?', '', stdout)

                        if dumphash in map(lambda x: x['md5'], item.files):
                            log(wiki, dump, 'verified', config)
                            rmline='rm -rf %s' % dumpdir + '/' + dump
                            if not os.system(rmline):
                                print 'DELETED ' + dumpdir + '/' + dump
                            print '%s was uploaded before, skipping...' % (dump)
                            continue
                        else:
                            print 'ERROR: The online item misses ' + dump
                            log(wiki, dump, 'missing', config)
                            # We'll exit this if and go upload the dump
                else:
                    print '%s was uploaded before, skipping...' % (dump)
                    continue
            else:
                print '%s was not uploaded before' % dump

            time.sleep(0.1)
            wikidate_text = wikidate[0:4]+'-'+wikidate[4:6]+'-'+wikidate[6:8]
            print wiki, wikiname, wikidate, dump

            # Does the item exist already?
            ismissingitem = not item.exists

            # Logo path
            logourl = ''

            if ismissingitem or config.update:
                #get metadata from api.php
                #first sitename and base url
                params = {'action': 'query', 'meta': 'siteinfo', 'format': 'xml'}
                data = urllib.urlencode(params)
                req = urllib2.Request(url=wiki, data=data, headers=headers)
                xml = ''
                try:
                    f = urllib2.urlopen(req, timeout=10)
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
                    f = urllib2.urlopen(req, timeout=10)
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

                raw = ''
                try:
                    f = urllib.urlopen(baseurl, timeout=10)
                    raw = f.read()
                    f.close()
                except:
                    pass

                #or copyright info from #footer in mainpage
                if baseurl and not rightsinfourl and not rightsinfotext:
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
                try:
                    logourl = re.findall(ur'p-logo["\'][^>]*>\s*<a [^>]*background-image:\s*(?:url\()?([^;)"]+)', raw)[0]
                except:
                    pass

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

            if c == 0:
                # Item metadata
                md = {
                    'mediatype': 'web',
                    'collection': config.collection,
                    'title': wikititle,
                    'description': wikidesc,
                    'language': lang,
                    'last-updated-date': wikidate_text,
                    'subject': '; '.join(wikikeys), # Keywords should be separated by ; but it doesn't matter much; the alternative is to set one per field with subject[0], subject[1], ...
                    'licenseurl': wikilicenseurl and urlparse.urljoin(wiki, wikilicenseurl),
                    'rights': wikirights,
                    'originalurl': wikiurl,
                }

            #Upload files and update metadata
            try:
                item.upload(dumpdir + '/' + dump, metadata=md, access_key=accesskey, secret_key=secretkey, verbose=True, queue_derive=False)
                item.modify_metadata(md) # update
                print 'You can find it in https://archive.org/details/wiki-%s' % (wikiname)
                uploadeddumps.append(dump)
                log(wiki, dump, 'ok', config)
                if logourl:
                    logo = StringIO.StringIO(urllib.urlopen(urlparse.urljoin(wiki, logourl), timeout=10).read())
                    logoextension = logourl.split('.')[-1] if logourl.split('.') else 'unknown'
                    logo.name = 'wiki-' + wikiname + '_logo.' + logoextension
                    item.upload(logo, access_key=accesskey, secret_key=secretkey, verbose=True)
            except Exception as e:
                print wiki, dump, 'Error when uploading?'
                print e.message

            c += 1

def main(params=[]):
    parser = argparse.ArgumentParser("""uploader.py

This script takes the filename of a list of wikis as argument and uploads their dumps to archive.org.
The list must be a text file with the wiki's api.php URLs, one per line.
Dumps must be in the same directory and follow the -wikidump.7z/-history.xml.7z format
as produced by launcher.py (explained in https://github.com/WikiTeam/wikiteam/wiki/Tutorial#Publishing_the_dump ).
You need a file named keys.txt with access and secret keys, in two different lines
You also need dumpgenerator.py in the same directory as this script.

Use --help to print this help.""")

    parser.add_argument('-pd', '--prune_directories', action='store_true')
    parser.add_argument('-pw', '--prune_wikidump', action='store_true')
    parser.add_argument('-a', '--admin', action='store_true')
    parser.add_argument('-c', '--collection', default='opensource')
    parser.add_argument('-wd', '--wikidump_dir', default='.')
    parser.add_argument('-u', '--update', action='store_true')
    parser.add_argument('listfile')
    config = parser.parse_args()
    if config.admin:
        config.collection = 'wikiteam'
    uploadeddumps = []
    listfile = config.listfile
    try:
        uploadeddumps = [l.split(';')[1] for l in open('uploader-%s.log' % (listfile), 'r').read().strip().splitlines() if len(l.split(';'))>1]
    except:
        pass
    print '%d dumps uploaded previously' % (len(uploadeddumps))
    wikis = open(listfile, 'r').read().strip().splitlines()

    upload(wikis, config, uploadeddumps)

if __name__ == "__main__":
    main()
