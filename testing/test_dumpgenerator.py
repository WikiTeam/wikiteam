#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (C) 2011-2014 WikiTeam developers
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

import json
try:
    from hashlib import md5
except ImportError:             # Python 2.4 compatibility
    from md5 import new as md5
import requests
import shutil
import time
import unittest
import urllib
import urllib2
from dumpgenerator import delay, getImageNames, getPageTitles, getUserAgent, getWikiEngine

class TestDumpgenerator(unittest.TestCase):
    # Documentation
    # http://revista.python.org.ar/1/html/unittest.html
    # https://docs.python.org/2/library/unittest.html
    
    # Ideas:
    # - Check one wiki per wikifarm at least (page titles & images, with/out API)
    
    def test_delay(self):
        """ This test checks several delays """
        
        print '#'*73, '\n', 'test_delay', '\n', '#'*73
        for i in [0, 1, 2, 3]:
            print 'Testing delay:', i
            config = {'delay': i}
            t1 = time.time()
            delay(config=config)
            t2 = time.time() - t1
            self.assertTrue(t2 > i and t2 < i + 1)
    
    def test_getImages(self):
        """ This test download the image list using API and index.php """
        """ Compare both lists in length and file by file """
        """ Check the presence of some special files, like odd chars filenames """
        """ The tested wikis are from different wikifarms and some alone """
        
        print '#'*73, '\n', 'test_getImages', '\n', '#'*73
        tests = [
            # Alone wikis
            #['http://wiki.annotation.jp/index.php', 'http://wiki.annotation.jp/api.php', u'かずさアノテーション - ソーシャル・ゲノム・アノテーション.jpg'], 
            ['http://archiveteam.org/index.php', 'http://archiveteam.org/api.php', u'Archive-is 2013-07-02 17-05-40.png'], 
            ['http://skilledtests.com/wiki/index.php5', 'http://skilledtests.com/wiki/api.php', u'Benham\'s disc (animated).gif'], 
            
            # Editthis wikifarm
            # It has a page view limit
            
            # Gamepedia wikifarm
            ['http://dawngate.gamepedia.com/index.php', 'http://dawngate.gamepedia.com/api.php', u'Spell Vanquish.png'], 
            
            # Gentoo wikifarm
            ['http://wiki.gentoo.org/index.php', 'http://wiki.gentoo.org/api.php', u'Openclonk screenshot1.png'], 
            
            # Neoseeker wikifarm
            ['http://digimon.neoseeker.com/w/index.php', 'http://digimon.neoseeker.com/w/api.php', u'Ogremon card.png'], 
            
            # Orain wikifarm
            ['http://mc.orain.org/w/index.php', 'http://mc.orain.org/w/api.php', u'Mojang logo.svg'],
            
            # Referata wikifarm
            ['http://wikipapers.referata.com/w/index.php', 'http://wikipapers.referata.com/w/api.php', u'Avbot logo.png'],
            
            # ShoutWiki wikifarm
            ['http://commandos.shoutwiki.com/w/index.php', 'http://commandos.shoutwiki.com/w/api.php', u'Night of the Wolves loading.png'], 
            
            # Wiki-site wikifarm
            ['http://minlingo.wiki-site.com/index.php', 'http://minlingo.wiki-site.com/api.php', u'一 (書方灋ᅗᅩ).png'], 
            
            # Wikkii wikifarm
            # It seems offline
        ]
        session = requests.Session()
        session.headers = {'User-Agent': getUserAgent()}
        for index, api, filetocheck in tests:
            print '\n'
            # Testing with API
            config_api = {'api': api, 'delay': 0}
            req = urllib2.Request(url=api, data=urllib.urlencode({'action': 'query', 'meta': 'siteinfo', 'siprop': 'statistics', 'format': 'json'}), headers={'User-Agent': getUserAgent()})
            f = urllib2.urlopen(req)
            imagecount = int(json.loads(f.read())['query']['statistics']['images'])
            f.close()
    
            print 'Testing', config_api['api']
            print 'Trying to parse', filetocheck, 'with API'
            result_api = getImageNames(config=config_api, session=session)
            self.assertEqual(len(result_api), imagecount)
            self.assertTrue(filetocheck in [filename for filename, url, uploader in result_api])
            
            # Testing with index
            config_index = {'index': index, 'delay': 0}
            req = urllib2.Request(url=api, data=urllib.urlencode({'action': 'query', 'meta': 'siteinfo', 'siprop': 'statistics', 'format': 'json'}), headers={'User-Agent': getUserAgent()})
            f = urllib2.urlopen(req)
            imagecount = int(json.loads(f.read())['query']['statistics']['images'])
            f.close()
    
            print 'Testing', config_index['index']
            print 'Trying to parse', filetocheck, 'with index'
            result_index = getImageNames(config=config_index, session=session)
            #print 111, set([filename for filename, url, uploader in result_api]) - set([filename for filename, url, uploader in result_index])
            self.assertEqual(len(result_index), imagecount)
            self.assertTrue(filetocheck in [filename for filename, url, uploader in result_index])
            
            # Compare every image in both lists, with/without API
            c = 0
            for filename_api, url_api, uploader_api in result_api:
                self.assertEqual(filename_api, result_index[c][0], u'{0} and {1} are different'.format(filename_api, result_index[c][0]))
                self.assertEqual(url_api, result_index[c][1], u'{0} and {1} are different'.format(url_api, result_index[c][1]))
                self.assertEqual(uploader_api, result_index[c][2], u'{0} and {1} are different'.format(uploader_api, result_index[c][2]))
                c += 1
    
    def test_getPageTitles(self):
        """ This test download the title list using API and index.php """
        """ Compare both lists in length and title by title """
        """ Check the presence of some special titles, like odd chars """
        """ The tested wikis are from different wikifarms and some alone """
        
        print '#'*73, '\n', 'test_getPageTitles', '\n', '#'*73
        tests = [
            # Alone wikis
            ['http://archiveteam.org/index.php', 'http://archiveteam.org/api.php', u'April Fools\' Day'], 
            ['http://skilledtests.com/wiki/index.php5', 'http://skilledtests.com/wiki/api.php', u'Conway\'s Game of Life'], 
            
            # Gentoo wikifarm
            ['http://wiki.gentoo.org/index.php', 'http://wiki.gentoo.org/api.php', u'/usr move'], 
        ]
        
        session = requests.Session()
        session.headers = {'User-Agent': getUserAgent()}
        for index, api, pagetocheck in tests:
            print '\n'
            # Testing with API
            config_api = {'api': api, 'delay': 0, 'namespaces': ['all'], 'exnamespaces': []}
            print 'Testing', config_api['api']
            print 'Trying to parse', pagetocheck, 'with API'
            result_api = getPageTitles(config=config_api, session=session)
            self.assertTrue(pagetocheck in result_api)
            
            # Testing with index
            config_index = {'index': index, 'delay': 0, 'namespaces': ['all'], 'exnamespaces': []}
            print 'Testing', config_index['index']
            print 'Trying to parse', pagetocheck, 'with index'
            result_index = getPageTitles(config=config_index, session=session)
            self.assertTrue(pagetocheck in result_index)
            self.assertEqual(len(result_api), len(result_index))
            
            # Compare every page in both lists, with/without API
            c = 0
            for pagename_api in result_api:
                self.assertEqual(pagename_api, result_index[c], u'{0} and {1} are different'.format(pagename_api, result_index[c]))
                c += 1
            
    def test_getWikiEngine(self):
        tests = [
            ['https://www.dokuwiki.org', 'DokuWiki'],
            #['http://wiki.openwrt.org', 'DokuWiki'],
            ['http://skilledtests.com/wiki/', 'MediaWiki'],
            ['http://moinmo.in', 'MoinMoin'],
            ['https://wiki.debian.org', 'MoinMoin'],
        ]
        for wiki, engine in tests:
            print 'Testing', wiki
            self.assertTrue(getWikiEngine(wiki) == engine)

if __name__ == '__main__':
    #copying dumpgenerator.py to this directory
    #shutil.copy2('../dumpgenerator.py', './dumpgenerator.py')

    unittest.main()
