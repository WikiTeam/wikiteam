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
import requests
import shutil
import time
import unittest
import urllib
import urllib2
from dumpgenerator import delay, getImageFilenamesURL, getImageFilenamesURLAPI, getUserAgent

class TestDumpgenerator(unittest.TestCase):
    #Documentation
    #http://revista.python.org.ar/1/html/unittest.html
    #https://docs.python.org/2/library/unittest.html
    
    def test_delay(self):
        print '#'*73, '\n', 'test_delay', '\n', '#'*73
        for i in [0, 1, 2, 3]:
            print 'Testing delay:', i
            config = {'delay': i}
            t1 = time.time()
            delay(config=config)
            t2 = time.time() - t1
            self.assertTrue(t2 > i and t2 < i + 1)
    
    def test_getImages(self):
        print '#'*73, '\n', 'test_getImages', '\n', '#'*73
        tests = [
            ['http://wiki.annotation.jp/index.php', 'http://wiki.annotation.jp/api.php', u'かずさアノテーション - ソーシャル・ゲノム・アノテーション.jpg'], 
            ['http://archiveteam.org/index.php', 'http://archiveteam.org/api.php', u'Archive-is 2013-07-02 17-05-40.png'],
        ]
        for index, api, filetocheck in tests:
            print '\n'
            #testing with API
            config_api = {'api': api, 'delay': 0}
            req = urllib2.Request(url=api, data=urllib.urlencode({'action': 'query', 'meta': 'siteinfo', 'siprop': 'statistics', 'format': 'json'}), headers={'User-Agent': getUserAgent()})
            f = urllib2.urlopen(req)
            imagecount = int(json.loads(f.read())['query']['statistics']['images'])
            f.close()
    
            print 'Testing', config_api['api']
            print 'Trying to parse', filetocheck, 'with API'
            result_api = getImageFilenamesURLAPI(config=config_api)
            self.assertTrue(len(result_api) == imagecount)
            self.assertTrue(filetocheck in [filename for filename, url, uploader in result_api])
            
            #testing with index
            config_index = {'index': index, 'delay': 0}
            req = urllib2.Request(url=api, data=urllib.urlencode({'action': 'query', 'meta': 'siteinfo', 'siprop': 'statistics', 'format': 'json'}), headers={'User-Agent': getUserAgent()})
            f = urllib2.urlopen(req)
            imagecount = int(json.loads(f.read())['query']['statistics']['images'])
            f.close()
    
            print 'Testing', config_index['index']
            print 'Trying to parse', filetocheck, 'with index'
            result_index = getImageFilenamesURL(config=config_index)
            self.assertTrue(len(result_index) == imagecount)
            self.assertTrue(filetocheck in [filename for filename, url, uploader in result_index])

if __name__ == '__main__':
    #copying dumpgenerator.py to this directory
    shutil.copy2('../dumpgenerator.py', './dumpgenerator.py')
    
    unittest.main()
