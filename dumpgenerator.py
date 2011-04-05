#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# Copyright (C) 2011 emijrp
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

import re
import sys
import urllib

# todo:
# curonly and all history (curonly si puede acumular varias peticiones en un solo GET, ara full history pedir cada pagina una a una)
# usar api o parsear html si no está disponible
# http://www.mediawiki.org/wiki/Manual:Parameters_to_Special:Export

def getAllPageTitles(domain='', namespaces=[]):
    #http://en.wikipedia.org/wiki/Special:AllPages
    #http://archiveteam.org/index.php?title=Special:AllPages
    #http://www.wikanda.es/wiki/Especial:Todas
    if not domain:
        print 'Please, use --domain parameter'
        sys.exit()
    
    namespacenames = {0:''} # main is 0, no prefix
    if namespaces:
        raw = urllib.urlopen('%s/index.php?title=Special:Allpages' % (domain)).read()
        m = re.compile(r'<option [^>]*?value="(?P<namespaceid>\d+)"[^>]*?>(?P<namespacename>[^<]+)</option>').finditer(raw) # [^>]*? to include selected="selected"
        if 'all' in namespaces:
            namespaces = []
            for i in m:
                namespaces.append(int(i.group("namespaceid")))
                namespacenames[int(i.group("namespaceid"))] = i.group("namespacename")
        else:
            #check if those namespaces really exist in this wiki
            namespaces2 = []
            for i in m:
                if int(i.group("namespaceid")) in namespaces:
                    namespaces2.append(int(i.group("namespaceid")))
                    namespacenames[int(i.group("namespaceid"))] = i.group("namespacename")
            namespaces = namespaces2
    else:
        namespaces = [0]
    
    namespaces = [i for i in set(namespaces)] #uniques
    titles = []
    for namespace in namespaces:
        raw = urllib.urlopen('%s/index.php?title=Special:Allpages&namespace=%s' % (domain, namespace)).read()
        
        if re.search('<!-- bodytext -->', raw): #<!-- bodytext --> <!-- /bodytext --> <!-- start content --> <!-- end content -->
            raw = raw.split('<!-- bodytext -->')[1].split('<!-- /bodytext -->')[0]
        elif re.search('<!-- start content -->', raw):
            raw = raw.split('<!-- start content -->')[1].split('<!-- end content -->')[0]
        else:
            print 'This wiki doesn\'t use marks to split contain'
        
        m = re.compile(r'title="(?P<title>[^>]+)"').finditer(raw)
        for i in m:
            if not i.group('title').startswith('Special:'):
                titles.append(i.group('title'))
    return titles

def getXML():
    # curl -d "" 'http://en.wikipedia.org/w/index.php?title=Special:Export&pages=Main_Page&offset=1&action=submit'
    # curl -d "" 'http://en.wikipedia.org/w/index.php?title=Special:Export&pages=Main_Page&curonly=1&action=submit'
    pass

if __name__ == '__main__':
    domain = 'http://archiveteam.org'
    curonly = False
    namespaces = ['all']
    
    if re.findall(r'(wikipedia|wikisource|wiktionary|wikibooks|wikiversity|wikimedia|wikispecies|wikiquote|wikinews)\.org', domain):
        print 'DO NOT USE THIS SCRIPT TO DOWNLOAD WIKIMEDIA PROJECTS!\nDownload the dumps from http://download.wikimedia.org\nThanks!'
        sys.exit()
    
    titles = getAllPageTitles(domain=domain, namespaces=namespaces)
    print '\n'.join(titles)
    print '%d titles loaded' % (len(titles))
