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

import shutil
import time
import unittest
from dumpgenerator import delay, getImageFilenamesURL, getImageFilenamesURLAPI

class TestDumpgenerator(unittest.TestCase):
    #Documentation
    #http://revista.python.org.ar/1/html/unittest.html
    #https://docs.python.org/2/library/unittest.html
    
    def test_delay(self):
        # 0 delay
        config = {'delay': 0}
        t1 = time.time()
        delay(config=config)
        t2 = time.time() - t1
        self.assertTrue(t2 > 0 and t2 < 0.001)
        
        # 3 sec delay
        config = {'delay': 3}
        t1 = time.time()
        delay(config=config)
        t2 = time.time() - t1
        self.assertTrue(t2 > 3 and t2 < 3.001)
    
    def test_getImageFilenamesURL(self):
        #Checks if this filename かずさアノテーション_-_ソーシャル・ゲノム・アノテーション.jpg is well parsed from API
        #http://wiki.annotation.jp/images/0/02/%E3%81%8B%E3%81%9A%E3%81%95%E3%82%A2%E3%83%8E%E3%83%86%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3_-_%E3%82%BD%E3%83%BC%E3%82%B7%E3%83%A3%E3%83%AB%E3%83%BB%E3%82%B2%E3%83%8E%E3%83%A0%E3%83%BB%E3%82%A2%E3%83%8E%E3%83%86%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3.jpg
        config = {
            'index': 'http://wiki.annotation.jp/index.php', 
            'delay': 0, 
        }
        japaneseFilename = u'かずさアノテーション - ソーシャル・ゲノム・アノテーション.jpg'
        print 'Checking', config['index']
        print 'Trying to parse', japaneseFilename, 'without API'
        result = getImageFilenamesURL(config=config)
        
        self.assertTrue(len(result) > 250)
        self.assertTrue(japaneseFilename in [filename for filename, url, uploader in result])

    def test_getImageFilenamesURLAPI(self):
        #Checks if this filename かずさアノテーション_-_ソーシャル・ゲノム・アノテーション.jpg is well parsed from API
        #http://wiki.annotation.jp/images/0/02/%E3%81%8B%E3%81%9A%E3%81%95%E3%82%A2%E3%83%8E%E3%83%86%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3_-_%E3%82%BD%E3%83%BC%E3%82%B7%E3%83%A3%E3%83%AB%E3%83%BB%E3%82%B2%E3%83%8E%E3%83%A0%E3%83%BB%E3%82%A2%E3%83%8E%E3%83%86%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3.jpg
        config = {
            'api': 'http://wiki.annotation.jp/api.php', 
            'delay': 0, 
        }
        japaneseFilename = u'かずさアノテーション - ソーシャル・ゲノム・アノテーション.jpg'
        print 'Checking', config['api']
        print 'Trying to parse', japaneseFilename, 'from API'
        result = getImageFilenamesURLAPI(config=config)
        
        self.assertTrue(len(result) > 250)
        self.assertTrue(japaneseFilename in [filename for filename, url, uploader in result])

if __name__ == '__main__':
    #copying dumpgenerator.py to this directory
    shutil.copy2('../dumpgenerator.py', './dumpgenerator.py')
    
    unittest.main()
