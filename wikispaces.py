#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (C) 2018 WikiTeam developers
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

# Documentation for users: https://github.com/WikiTeam/wikiteam/wiki
# Documentation for developers: http://wikiteam.readthedocs.com

import csv
import os
import re
import sys
import time
import urllib.request

def saveURL(url='', filename='', path=''):
    wikidomain = url.split('//')[1].split('/')[0]
    filename2 = '%s/%s/%s' % (wikidomain, path, filename)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    try:
        urllib.request.urlretrieve(url, filename2)
    except:
        sleep = 10 # seconds
        maxsleep = 100
        while sleep <= maxsleep:
            try:
                print('Error while retrieving: %s' % (url))
                print('Retry in %s seconds...' % (sleep))
                time.sleep(sleep)
                urllib.request.urlretrieve(url, filename2)
                break
            except:
                sleep = sleep * 2

def downloadPage(wikiurl='', pagename=''):
    pagenameplus = re.sub(' ', '+', pagename)
    pagename_ = urllib.parse.quote(pagename)
    #page current revision
    pageurl = '%s/page/code/%s' % (wikiurl, pagename_)
    filename = '%s.wikitext' % (pagenameplus)
    saveURL(url=pageurl, filename=filename, path='pages')
    #csv with page history
    csvurl = '%s/page/history/%s?utable=WikiTablePageHistoryList&ut_csv=1' % (wikiurl, pagename_)
    csvfilename = '%s.history.csv' % (pagenameplus)
    saveURL(url=csvurl, filename=csvfilename, path='pages')

def downloadFile(wikiurl='', filename=''):
    filenameplus = re.sub(' ', '+', filename)
    filename_ = urllib.parse.quote(filename)
    #file full resolution
    fileurl = '%s/file/view/%s' % (wikiurl, filename_)
    filename = filenameplus
    saveURL(url=fileurl, filename=filename, path='files')
    #csv with file history
    csvurl = '%s/file/detail/%s?utable=WikiTablePageList&ut_csv=1' % (wikiurl, filename_)
    csvfilename = '%s.history.csv' % (filenameplus)
    saveURL(url=csvurl, filename=csvfilename, path='files')

def downloadPagesAndFiles(wikiurl=''):
    print('Downloading Pages and Files from %s' % (wikiurl))
    #csv all pages and files
    csvurl = '%s/space/content?utable=WikiTablePageList&ut_csv=1' % (wikiurl)
    saveURL(url=csvurl, filename='pages-and-files.csv')
    #download every page and file
    with open('pages-and-files.csv', 'r') as csvfile:
        filesc = 0
        pagesc = 0
        rows = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in rows:
            if row[0] == 'file':
                filesc += 1
                filename = row[1]
                print('Downloading file: %s' % (filename))
                downloadFile(wikiurl=wikiurl, filename=filename)
            elif row[0] == 'page':
                pagesc += 1
                pagename = row[1]
                print('Downloading page: %s' % (pagename))
                downloadPage(wikiurl=wikiurl, pagename=pagename)
    print('Downloaded %d pages' % (pagesc))
    print('Downloaded %d files' % (filesc))

def downloadMainPage(wikiurl=''):
    saveURL(url=wikiurl, filename='index.html')

def main():
    if len(sys.argv) < 2:
        sys.exit()
    wikiurl = sys.argv[1]
    if not wikiurl or not '//' in wikiurl:
        print('Please, introduce a wikispaces wiki url.\nExample: https://yourwiki.wikispaces.com')
        sys.exit()
    wikidomain = wikiurl.split('//')[1].split('/')[0]
    print('Creating directories for %s' % (wikidomain))
    if not os.path.exists('%s/files' % (wikidomain)):
        os.makedirs('%s/files' % (wikidomain))
    if not os.path.exists('%s/pages' % (wikidomain)):
        os.makedirs('%s/pages' % (wikidomain))
    downloadPagesAndFiles(wikiurl=wikiurl)
    downloadMainPage(wikiurl=wikiurl)

if __name__ == "__main__":
    main()
