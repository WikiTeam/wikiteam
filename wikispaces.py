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
import datetime
import os
import re
import subprocess
import sys
import time
import urllib.request

# Requirements:
# zip command (apt-get install zip)
# ia command (pip install internetarchive)

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
        maxsleep = 60
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
    wikitextfile = '%s/%s/%s' % (wikidomain, path, filename)
    if not os.path.exists(wikitextfile):
        print('Error retrieving wikitext, page is a redirect probably')
        return
    with open(wikitextfile, 'r') as f:
        wikitext = f.read()
    with open(wikitextfile, 'w') as f:
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
    print('Downloading sitemap.xml')
    saveURL(wikidomain=wikidomain, url=wikiurl, filename='sitemap.xml', path='')

def downloadMainPage(wikidomain='', wikiurl=''):
    print('Downloading index.html')
    saveURL(wikidomain=wikidomain, url=wikiurl, filename='index.html', path='')

def downloadLogo(wikidomain='', wikiurl=''):
    index = '%s/index.html' % (wikidomain)
    if os.path.exists(index):
        with open(index, 'r') as f:
            m = re.findall(r'class="WikiLogo WikiElement"><img src="([^<> "]+?)"', f.read())
            if m:
                logourl = m[0]
                logofilename = logourl.split('/')[-1]
                print('Downloading logo')
                saveURL(wikidomain=wikidomain, url=logourl, filename=logofilename, path='')
                return logofilename
    return ''

def main():
    upload = False
    isadmin = False
    if len(sys.argv) < 2:
        print('Please, introduce a wikispaces wiki url or filename.\nExample: https://yourwiki.wikispaces.com or mylistofwikis.txt')
        sys.exit()
    param = sys.argv[1]
    if not param:
        print('Please, introduce a wikispaces wiki url or filename.\nExample: https://yourwiki.wikispaces.com or mylistofwikis.txt')
        sys.exit()
    if len(sys.argv) > 2:
        if '--upload' in sys.argv:
            upload = True
        if '--admin' in sys.argv:
            isadmin = True
    
    wikilist = []
    if '://' in param:
        wikilist.append(param.rstrip('/'))
    else:
        with open(param, 'r') as f:
            wikilist = f.read().strip().splitlines()
            wikilist2 = []
            for wiki in wikilist:
                wikilist2.append(wiki.rstrip('/'))
            wikilist = wikilist2
    
    for wikiurl in wikilist:
        wikidomain = wikiurl.split('://')[1].split('/')[0]
        print('#'*40,'\n Downloading:', wikiurl)
        print('#'*40,'\n')
        dirfiles = '%s/files' % (wikidomain)
        if not os.path.exists(dirfiles):
            print('Creating directory %s' % (dirfiles))
            os.makedirs(dirfiles)
        dirpages = '%s/pages' % (wikidomain)
        if not os.path.exists(dirpages):
            print('Creating directory %s' % (dirpages))
            os.makedirs(dirpages)
        downloadPagesAndFiles(wikidomain=wikidomain, wikiurl=wikiurl)
        sitemapurl = 'https://%s/sitemap.xml' % (wikidomain)
        downloadSitemap(wikidomain=wikidomain, wikiurl=sitemapurl)
        downloadMainPage(wikidomain=wikidomain, wikiurl=wikiurl)
        logofilename = downloadLogo(wikidomain=wikidomain, wikiurl=wikiurl)
        
        if upload:
            print('\nCompressing dump...')
            wikidir = wikidomain
            os.chdir(wikidir)
            print('Changed directory to', os.getcwd())
            wikizip = '%s.zip' % (wikidomain)
            subprocess.call('zip' + ' -r ../%s files/ pages/ index.html pages-and-files.csv sitemap.xml %s' % (wikizip, logofilename), shell=True)
            os.chdir('..')
            print('Changed directory to', os.getcwd())
            
            print('\nUploading to Internet Archive...')
            indexfilename = '%s/index.html' % (wikidir)
            if not os.path.exists(indexfilename):
                print('\nError dump incomplete, skipping upload\n')
                continue
            f = open(indexfilename, 'r')
            indexhtml = f.read()
            f.close()
            itemid = 'wiki-%s' % (wikidomain)
            wikititle = ''
            try:
                wikititle = indexhtml.split('wiki: {')[1].split('}')[0].split("text: '")[1].split("',")[0].strip()
            except:
                wikititle = wikidomain
            if not wikititle:
                wikititle = wikidomain
            itemtitle = 'Wiki - %s' % wikititle
            itemdesc = '<a href=\"%s\">%s</a> dumped with <a href=\"https://github.com/WikiTeam/wikiteam\" rel=\"nofollow\">WikiTeam</a> tools.' % (wikiurl, wikititle)
            itemtags = ['wiki', 'wikiteam', 'wikispaces', wikititle, wikidomain.split('.wikispaces.com')[0], wikidomain]
            itemoriginalurl = wikiurl
            itemlicenseurl = ''
            m = re.findall(r'<a rel="license" href="([^<>]+?)">', indexhtml.split('<div class="WikiLicense')[1].split('</div>')[0])
            if m:
                itemlicenseurl = m[0]
            if not itemlicenseurl:
                itemtags.append('unknowncopyright')
            itemtags_ = ' '.join(["--metadata='subject:%s'" % (tag) for tag in itemtags])
            itemcollection = isadmin and 'wikiteam' or 'opensource'
            itemlang = 'Unknown'
            itemdate = datetime.datetime.now().strftime("%Y-%m-%d")
            itemlogo = logofilename and '%s/%s' % (wikidir, logofilename) or ''                
            subprocess.call('ia' + ' upload %s %s %s --metadata="mediatype:web" --metadata="collection:%s" --metadata="title:%s" --metadata="description:%s" --metadata="language:%s" --metadata="last-updated-date:%s" %s %s' % (itemid, wikizip, itemlogo and itemlogo or '', itemcollection, itemtitle, itemdesc, itemlang, itemdate, itemlicenseurl and '--metadata="licenseurl:%s"' % (itemlicenseurl) or '', itemtags_), shell=True)
            print('You can find it in https://archive.org/details/%s' % (itemid))

if __name__ == "__main__":
    main()
