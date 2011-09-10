#!/usr/bin/python
# -*- coding: utf8 -*-

# Copyright (C) 2011 WikiTeam
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

import urllib
import sys
import re
import codecs

"""
recibe un argumento: 2005 (baja todo el año), 2005-01 (todo el mes), 2005-01-01 (un solo día), pero siempre organiza en directorios 2005 |_ 2005-01 |_ 2005-01-01, etc

http://www.mediawiki.org/wiki/Manual:Oldimage_table

substr para el X y XY del md5 http://dev.mysql.com/doc/refman/5.0/en/string-functions.html#function_substr

mysql -h commons-p.db.toolserver.org -e "use commonswiki_p;select oi_archive_name, oi_timestamp from oldimage where 1;" > test.txt
"""

def getUserAgent():
    """ Return a cool user-agent to hide Python user-agent """
    useragents = ['Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.0.4) Gecko/20060508 Firefox/1.5.0.4']
    return useragents[0]

class AppURLopener(urllib.FancyURLopener):
    version = getUserAgent()

urllib._urlopener = AppURLopener()

f = open('image.list', 'r')
l = f.read().splitlines()
f.close()

for i in l:
    i=urllib.unquote(i)
    urllib.urlretrieve(i, i.split('/')[-1])
