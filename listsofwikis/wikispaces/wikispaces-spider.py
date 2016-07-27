#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016 wikiTeam
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

import csv
import re
import time
import urllib2

def loadUsers():
    users = {}
    f = open('users.txt', 'r')
    for x in f.read().strip().splitlines():
        username = x.split(',')[0]
        numwikis = x.split(',')[1]
        users[username] = numwikis
    f.close()
    return users

def loadWikis():
    wikis = {}
    f = open('wikis.txt', 'r')
    for x in f.read().strip().splitlines():
        wikiname = x.split(',')[0]
        numusers = x.split(',')[1]
        wikis[wikiname] = numusers
    f.close()
    return wikis

def saveUsers(users):
    f = open('users.txt', 'w')
    output = [u'%s,%s' % (x, y) for x, y in users.items()]
    output.sort()
    output = u'\n'.join(output)
    f.write(output.encode('utf-8'))
    f.close()
    
def saveWikis(wikis):
    f = open('wikis.txt', 'w')
    output = [u'%s,%s' % (x, y) for x, y in wikis.items()]
    output.sort()
    output = u'\n'.join(output)
    f.write(output.encode('utf-8'))
    f.close()

def getUsers(wiki):
    wikiurl = 'https://%s.wikispaces.com/wiki/members?utable=WikiTableMemberList&ut_csv=1' % (wiki)
    try:
        wikireq = urllib2.Request(wikiurl, headers={ 'User-Agent': 'Mozilla/5.0' })
        wikicsv = urllib2.urlopen(wikireq)
        reader = csv.reader(wikicsv, delimiter=',', quotechar='"')
        headers = next(reader, None)
        usersfound = {}
        for row in reader:
            usersfound[row[0]] = u'?'
        return usersfound
    except:
        print 'Error reading', wikiurl
        return {}

def getWikis(user):
    wikiurl = 'https://www.wikispaces.com/user/view/%s' % (user)
    try:
        wikireq = urllib2.Request(wikiurl, headers={ 'User-Agent': 'Mozilla/5.0' })
        html = urllib2.urlopen(wikireq).read()
        if 'Wikis: ' in html:
            html = html.split('Wikis: ')[1].split('</div>')[0]
            wikisfound = {}
            for x in re.findall(ur'<a href="https://([^>]+).wikispaces.com/">', html):
                wikisfound[x] = u'?'
            return wikisfound
        return {}
    except:
        print 'Error reading', wikiurl
        return {}

def main():
    users = loadUsers()
    wikis = loadWikis()
    
    usersc = len(users)
    wikisc = len(wikis)
    print 'Loading files'
    print 'Loaded', usersc, 'users'
    print 'Loaded', wikisc, 'wikis'
    
    # find more users
    print 'Scanning wikis for more users'
    for wiki, numusers in wikis.items():
        if numusers != '?': #we have scanned this wiki before, skiping
            continue
        print 'Scanning https://%s.wikispaces.com for users' % (wiki)
        users2 = getUsers(wiki)
        wikis[wiki] = len(users2)
        c = 0
        for x2, y2 in users2.items():
            if x2 not in users.keys():
                users[x2] = u'?'
                c += 1
        print 'Found %s new users' % (c)
        if c > 0:
            saveUsers(users)
            users = loadUsers()
        saveWikis(wikis)
        time.sleep(1)
    wikis = loadWikis()
    
    # find more wikis
    print 'Scanning users for more wikis'
    for user, numwikis in users.items():
        if numwikis != '?': #we have scanned this user before, skiping
            continue
        print 'Scanning https://www.wikispaces.com/user/view/%s for wikis' % (user)
        wikis2 = getWikis(user)
        users[user] = len(wikis2)
        c = 0
        for x2, y2 in wikis2.items():
            if x2 not in wikis.keys():
                wikis[x2] = u'?'
                c += 1
        print 'Found %s new wikis' % (c)
        if c > 0:
            saveWikis(wikis)
            wikis = loadWikis()
        saveUsers(users)
        time.sleep(1)
    users = loadUsers()
    
    print '\nSummary:'
    print 'Found', len(users)-usersc, 'new users'
    print 'Found', len(wikis)-wikisc, 'new wikis'

if __name__ == '__main__':
    main()
