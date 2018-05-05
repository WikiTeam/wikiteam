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

def saveURL(wikidomain='', url='', filename='', path=''):
    filename2 = '%s/%s' % (wikidomain, filename)
    if path:
        filename2 = '%s/%s/%s' % (wikidomain, path, filename)
    #print(wikidomain)
    #print(url)
    #print(filename2)
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

def undoHTMLEntities(text=''):
    """ Undo some HTML codes """

    # i guess only < > & " ' need conversion
    # http://www.w3schools.com/html/html_entities.asp
    text = re.sub('&lt;', '<', text)
    text = re.sub('&gt;', '>', text)
    text = re.sub('&amp;', '&', text)
    text = re.sub('&quot;', '"', text)
    text = re.sub('&#039;', '\'', text)

    return text

def convertHTML2Wikitext(wikidomain='', filename='', path=''):
    wikitext = ''
    with open('%s/%s/%s' % (wikidomain, path, filename), 'r') as f:
        wikitext = f.read()
    with open('%s/%s/%s' % (wikidomain, path, filename), 'w') as f:
        m = re.findall(r'(?im)<div class="WikispacesContent WikispacesBs3">\s*<pre>', wikitext)
        if m:
            try:
                wikitext = wikitext.split(m[0])[1].split('</pre>')[0].strip()
                wikitext = undoHTMLEntities(text=wikitext)
            except:
                wikitext = ''
                print('Error extracting wikitext.')
        else:
            wikitext = ''
            print('Error extracting wikitext.')
        f.write(wikitext)

def downloadPage(wikidomain='', wikiurl='', pagename=''):
    pagenameplus = re.sub(' ', '+', pagename)
    pagename_ = urllib.parse.quote(pagename)
    
    #page current revision (html & wikitext)
    pageurl = '%s/%s' % (wikiurl, pagename_)
    filename = '%s.html' % (pagenameplus)
    saveURL(wikidomain=wikidomain, url=pageurl, filename=filename, path='pages')
    pageurl2 = '%s/page/code/%s' % (wikiurl, pagename_)
    filename2 = '%s.wikitext' % (pagenameplus)
    saveURL(wikidomain=wikidomain, url=pageurl2, filename=filename2, path='pages')
    convertHTML2Wikitext(wikidomain=wikidomain, filename=filename2, path='pages')
    
    #csv with page history
    csvurl = '%s/page/history/%s?utable=WikiTablePageHistoryList&ut_csv=1' % (wikiurl, pagename_)
    csvfilename = '%s.history.csv' % (pagenameplus)
    saveURL(wikidomain=wikidomain, url=csvurl, filename=csvfilename, path='pages')

def downloadFile(wikidomain='', wikiurl='', filename=''):
    filenameplus = re.sub(' ', '+', filename)
    filename_ = urllib.parse.quote(filename)
    
    #file full resolution
    fileurl = '%s/file/view/%s' % (wikiurl, filename_)
    filename = filenameplus
    saveURL(wikidomain=wikidomain, url=fileurl, filename=filename, path='files')
    
    #csv with file history
    csvurl = '%s/file/detail/%s?utable=WikiTablePageList&ut_csv=1' % (wikiurl, filename_)
    csvfilename = '%s.history.csv' % (filenameplus)
    saveURL(wikidomain=wikidomain, url=csvurl, filename=csvfilename, path='files')

def downloadPagesAndFiles(wikidomain='', wikiurl=''):
    print('Downloading Pages and Files from %s' % (wikiurl))
    #csv all pages and files
    csvurl = '%s/space/content?utable=WikiTablePageList&ut_csv=1' % (wikiurl)
    saveURL(wikidomain=wikidomain, url=csvurl, filename='pages-and-files.csv', path='')
    #download every page and file
    with open('%s/pages-and-files.csv' % (wikidomain), 'r') as csvfile:
        filesc = 0
        pagesc = 0
        rows = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in rows:
            if row[0] == 'file':
                filesc += 1
                filename = row[1]
                print('Downloading file: %s' % (filename))
                downloadFile(wikidomain=wikidomain, wikiurl=wikiurl, filename=filename)
            elif row[0] == 'page':
                pagesc += 1
                pagename = row[1]
                print('Downloading page: %s' % (pagename))
                downloadPage(wikidomain=wikidomain, wikiurl=wikiurl, pagename=pagename)
    print('Downloaded %d pages' % (pagesc))
    print('Downloaded %d files' % (filesc))

def downloadSitemap(wikidomain='', wikiurl=''):
    saveURL(wikidomain=wikidomain, url=wikiurl, filename='sitemap.xml', path='')

def downloadMainPage(wikidomain='', wikiurl=''):
    saveURL(wikidomain=wikidomain, url=wikiurl, filename='index.html', path='')

def main():
    if len(sys.argv) < 2:
        print('Please, introduce a wikispaces wiki url.\nExample: https://yourwiki.wikispaces.com')
        sys.exit()
    wikiurl = sys.argv[1]
    wikiurl = wikiurl.rstrip('/')
    if not wikiurl or not '//' in wikiurl:
        print('Please, introduce a wikispaces wiki url.\nExample: https://yourwiki.wikispaces.com')
        sys.exit()
    wikidomain = wikiurl.split('//')[1].split('/')[0]
    print('Creating directories for %s' % (wikidomain))
    if not os.path.exists('%s/files' % (wikidomain)):
        os.makedirs('%s/files' % (wikidomain))
    if not os.path.exists('%s/pages' % (wikidomain)):
        os.makedirs('%s/pages' % (wikidomain))
    downloadPagesAndFiles(wikidomain=wikidomain, wikiurl=wikiurl)
    sitemapurl = 'https://%s/sitemap.xml' % (wikidomain)
    downloadSitemap(wikidomain=wikidomain, wikiurl=sitemapurl)
    downloadMainPage(wikidomain=wikidomain, wikiurl=wikiurl)

if __name__ == "__main__":
    main()
