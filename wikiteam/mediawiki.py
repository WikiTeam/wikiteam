#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2011-2016 WikiTeam developers
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

import re

import wikiteam

def mwGetAPI(url=''):
    """ Returns API for a MediaWiki wiki, if available """

    api = ''
    html = wikiteam.getURL(url=url)
    m = re.findall(
        r'(?im)<\s*link\s*rel="EditURI"\s*type="application/rsd\+xml"\s*href="([^>]+?)\?action=rsd"\s*/\s*>',
        html)
    if m:
        api = m[0]
        if api.startswith('//'):  # gentoo wiki and others
            api = url.split('//')[0] + api
    return api

def mwGetIndex(url=''):
    """ Returns Index.php for a MediaWiki wiki, if available """

    api = mwGetAPI(url=url)
    index = ''
    html = wikiteam.getURL(url=url)
    m = re.findall(r'<li id="ca-viewsource"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?', html)
    if m:
        index = m[0]
    else:
        m = re.findall(r'<li id="ca-history"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?', html)
        if m:
            index = m[0]
    if index:
        if index.startswith('/'):
            index = '/'.join(api.split('/')[:-1]) + '/' + index.split('/')[-1]
    else:
        if api:
            if len(re.findall(r'/index\.php5\?', html)) > len(re.findall(r'/index\.php\?', html)):
                index = '/'.join(api.split('/')[:-1]) + '/index.php5'
            else:
                index = '/'.join(api.split('/')[:-1]) + '/index.php'
    return index

if __name__ == "__main__":
    main()
