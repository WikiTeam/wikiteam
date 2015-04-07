#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# dumpgenerator.py A generator of dumps for wikis
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

# To learn more, read the documentation:
#     https://github.com/WikiTeam/wikiteam/wiki

try:
    from BeautifulSoup import BeautifulSoup
except:
    print 'Need BeautifulSoup for current version. In the future it should use regex for scraping.'

import HTMLParser
import urlparse
import requests
import os
import socket
import re
from datetime import datetime
import gzip
import time


def getTitles(url, ns=None):
    """Get titles given a doku.php URL and an (optional) namespace"""
    titles = []
    ajax = urlparse.urljoin(url, 'lib/exe/ajax.php')
    params = {'call': 'index'}
    if ns:
        params['idx'] = ns
    else:
        print 'Finding titles'
    ns = ns or ''
    depth = len(ns.split(':'))
    if ns:
        print '%sLooking in namespace %s' % (' ' * depth, ns)
    r = requests.post(ajax, params)
    if r.status_code != 200 or "AJAX call 'index' unknown!" in r.text:
        return getTitlesOld(url, ns=None)
    soup = BeautifulSoup(r.text)
    for a in soup.findAll('a', href=True):
        if a.has_key('title'):
            title = a['title']
        else:
            query = urlparse.parse_qs(urlparse.urlparse(a['href']).query)
            title = (query['idx' if 'idx' in query else 'id'])[0]
        if a['class'] == 'idx_dir':
            titles += getTitles(url, title)
        else:
            titles.append(title)
    time.sleep(1.5)
    print '%sFound %d title(s) in namespace %s' % (' ' * depth, len(titles), ns or '(all)')
    return titles


def getTitlesOld(url, ns=None, ancient=False):
    """Get titles using the doku.php?do=index"""

    titles = []
    params = {'do': 'index'}

    if ns:
        params['idx'] = ns
    ns = ns or ''
    depth = len(ns.split(':'))

    r = requests.get(url, params=params)
    soup = BeautifulSoup(r.text).findAll('ul', {'class': 'idx'})[0]
    attr = 'text' if ancient else 'title'

    if ns:
        print '%sSearching in namespace %s' % (' ' * depth, ns)

        def match(href):
            if not href:
                return False
            qs = urlparse.urlparse(href).query
            qs = urlparse.parse_qs(qs)
            return 'idx' in qs and qs['idx'][0] in (ns, ':' + ns)
        result = soup.findAll(
            'a', {
                'class': 'idx_dir', 'href': match})[0].findAllPrevious('li')[0].findAll(
            'a', {
                'href': lambda x: x and not match(x)})
    else:
        print 'Finding titles (?do=index)'
        result = soup.findAll('a')

    for a in result:
        query = urlparse.parse_qs(urlparse.urlparse(a['href']).query)
        if a['class'] == 'idx_dir':
            titles += getTitlesOld(url, query['idx'][0])
        else:
            titles.append(query['id'][0])

    print '%sFound %d title(s) in namespace %s' % (' ' * depth, len(titles), ns or '(all)')

    return titles


def getSourceExport(url, title, rev=''):
    """Export the raw source of a page (at a given revision)"""

    r = requests.get(url, params={'id': title, 'rev': rev, 'do': 'export_raw'})
    return r.text


def getSourceEdit(url, title, rev=''):
    """Export the raw source of a page by scraping the edit box content. Yuck."""

    r = requests.get(url, params={'id': title, 'rev': rev, 'do': 'edit'})
    soup = BeautifulSoup(r.text)
    return ''.join(soup.find('textarea', {'name': 'wikitext'}).contents).strip()


def domain2prefix(url):
    """ Convert domain name to a valid prefix filename. """

    domain = url

    domain = domain.lower()
    domain = re.sub(r'(https?://|www\.|/doku\.php)', '', domain)
    domain = re.sub(r'/', '_', domain)
    domain = re.sub(r'\.', '', domain)
    domain = re.sub(r'[^A-Za-z0-9]', '_', domain)

    return domain


def getRevisions(url, title, use_hidden_rev=False, select_revs=False):
    """ Get the revisions of a page. This is nontrivial because different versions of DokuWiki return completely different revision HTML."""

    revs = []
    h = HTMLParser.HTMLParser()
    if select_revs:
        r = requests.get(url, params={'id': title, 'do': 'diff'})
        soup = BeautifulSoup(r.text)
        select = soup.find(
            'select', {
                'class': 'quickselect', 'name': 'rev2[1]'})
        for option in select.findAll('option'):
            text = option.text
            date = ' '.join(text.split(' ')[:2])
            username = len(text.split(' ')) > 2 and text.split(' ')[2]
            summary = ' '.join(text.split(' ')[3:])

            revs.append({'id': option['value'],
                         'user': username,
                         'sum': summary,
                         'date': date})

    i = 0
    continue_index = -1
    cont = True

    while cont:
        r = requests.get(
            url,
            params={
                'id': title,
                'do': 'revisions',
                'first': continue_index})

        soup = BeautifulSoup(r.text)
        lis = soup.findAll(
            'div', {
                'class': 'level1'})[0].findNext('ul').findAll('li')

        for li in lis:
            rev = {}
            rev_hrefs = li.findAll(
                'a', href=lambda href: href and (
                    '&rev=' in href or '?rev=' in href))
            rev['minor'] = ('class', 'minor') in li.attrs

            if rev_hrefs:
                rev['id'] = urlparse.parse_qs(
                    urlparse.urlparse(
                        rev_hrefs[0]['href']).query)['rev'][0]

            sum_span = li.findAll('span', {'class': 'sum'})
            if sum_span and not select_revs:
                sum_span = sum_span[0]
                sum_text = sum_span.text.split(' ')[1:]
                if sum_span.findAll('bdi'):
                    rev['sum'] = h.unescape(sum_span.find('bdi').text).strip()
                else:
                    rev['sum'] = h.unescape(' '.join(sum_text)).strip()
            elif not select_revs:
                print repr(li.text)
                wikilink1 = li.find('a', {'class': 'wikilink1'})
                text_node = wikilink1 and wikilink1.next and wikilink1.next.next or ''
                if text_node.strip:
                    rev['sum'] = h.unescape(text_node).strip(u'\u2013 \n')

            date_span = li.find('span', {'class': 'date'})
            if date_span:
                rev['date'] = date_span.text.strip()
            else:
                rev['date'] = ' '.join(li.text.split(' ')[:2])
                matches = re.findall(
                    r'([0-9./]+ [0-9]{1,2}:[0-9]{1,2})',
                    rev['date'])
                if matches:
                    rev['date'] = matches[0]

            if not (select_revs and len(revs) > i and revs[i]['user']):
                user_span = li.find('span', {'class': 'user'})
                if user_span:
                    rev['user'] = user_span.text
                else:
                    user_matches = re.findall(ur'\xe9e\xe9\xe9(.*)', li.text)
                    if user_matches:
                        rev['user'] = user_matches[0]

            if select_revs and len(revs) > i:
                revs[i].update(rev)
            else:
                revs.append(rev)
            i += 1

        first = soup.findAll('input', {'name': 'first', 'value': True})
        continue_index = first and max(map(lambda x: x['value'], first))
        cont = soup.find('input', {'class': 'button', 'accesskey': 'n'})
        time.sleep(1.5)

    if revs and use_hidden_rev and not select_revs:
        soup2 = BeautifulSoup(requests.get(url, params={'id': title}).text)
        revs[0]['id'] = soup2.find(
            'input', {
                'type': 'hidden', 'name': 'rev', 'value': True})['value']

    return revs


def getFiles(url, ns=''):
    """ Return a list of media filenames of a wiki """
    files = set()
    ajax = urlparse.urljoin(url, 'lib/exe/ajax.php')
    medialist = BeautifulSoup(
        requests.post(
            ajax, {
                'call': 'medialist', 'ns': ns, 'do': 'media'}).text)
    medians = BeautifulSoup(
        requests.post(
            ajax, {
                'call': 'medians', 'ns': ns, 'do': 'media'}).text)
    imagelinks = medialist.findAll(
        'a',
        href=lambda x: x and re.findall(
            '[?&](media|image)=',
            x))
    for a in imagelinks:
        query = urlparse.parse_qs(urlparse.urlparse(a['href']).query)
        key = 'media' if 'media' in query else 'image'
        files.add(query[key][0])
    files = list(files)
    namespacelinks = medians.findAll('a', {'class': 'idx_dir', 'href': True})
    for a in namespacelinks:
        query = urlparse.parse_qs(urlparse.urlparse(a['href']).query)
        files += getFiles(url, query['ns'][0])
    print 'Found %d files in namespace %s' % (len(files), ns or '(all)')
    return files


def dumpContent(url):
    os.mkdir(domain2prefix(url) + '/pages')
    os.mkdir(domain2prefix(url) + '/attic')
    os.mkdir(domain2prefix(url) + '/meta')

    titles = getTitles(url)
    if not len(titles):
        print 'Empty wiki'
        return

    r1 = requests.get(url, params={'id': titles[0], 'do': 'export_raw'})
    r2 = requests.get(url, params={'id': titles[0]})
    r3 = requests.get(url, params={'id': titles[0], 'do': 'diff'})

    getSource = getSourceExport
    if 'html' in r1.headers['content-type']:
        getSource = getSourceEdit

    soup = BeautifulSoup(r2.text)
    hidden_rev = soup.findAll(
        'input', {
            'type': 'hidden', 'name': 'rev', 'value': True})
    use_hidden_rev = hidden_rev and hidden_rev[0]['value']

    soup = BeautifulSoup(r3.text)
    select_revs = soup.findAll(
        'select', {
            'class': 'quickselect', 'name': 'rev2[0]'})

    for title in titles:
        titleparts = title.split(':')
        for i in range(len(titleparts)):
            dir = "/".join(titleparts[:i])
            if not os.path.exists(domain2prefix(url) + '/pages/' + dir):
                os.mkdir(domain2prefix(url) + '/pages/' + dir)
            if not os.path.exists(domain2prefix(url) + '/meta/' + dir):
                os.mkdir(domain2prefix(url) + '/meta/' + dir)
            if not os.path.exists(domain2prefix(url) + '/attic/' + dir):
                os.mkdir(domain2prefix(url) + '/attic/' + dir)
        with open(domain2prefix(url) + '/pages/' + title.replace(':', '/') + '.txt', 'w') as f:
            f.write(getSource(url, title).encode("utf-8"))
        revs = getRevisions(url, title, use_hidden_rev, select_revs)
        for rev in revs[1:]:
            if 'id' in rev and rev['id']:
                with gzip.open(domain2prefix(url) + '/attic/' + title.replace(':', '/') + '.' + rev['id'] + '.txt.gz', 'w') as f:
                    f.write(getSource(url, title, rev['id']).encode("utf-8"))
                time.sleep(1.5)
                print 'Revision %s of %s' % (rev['id'], title)
        with open(domain2prefix(url) + '/meta/' + title.replace(':', '/') + '.changes', 'w') as f:
            # Loop through revisions in reverse.
            for rev in revs[::-1]:
                print rev, title
                sum = 'sum' in rev and rev['sum'].strip() or ''
                id = 0

                ip = '127.0.0.1'
                user = ''
                minor = 'minor' in rev and rev['minor']

                if 'id' in rev and rev['id']:
                    id = rev['id']
                else:
                    # Different date formats in different versions of DokuWiki.
                    # If no ID was found, make one up based on the date (since rev IDs are Unix times)
                    # Maybe this is evil. Not sure.

                    try:
                        date = datetime.strptime(rev['date'], "%Y/%m/%d %H:%M")
                        id = str(int(time.mktime(date.utctimetuple())))
                    except:
                        date = datetime.strptime(rev['date'], "%d.%m.%Y %H:%M")
                        id = str(int(time.mktime(date.utctimetuple())))

                rev['user'] = rev['user'] if 'user' in rev else 'unknown'
                try:
                    # inet_aton throws an exception if its argument is not an IPv4 address
                    socket.inet_aton(rev['user'])
                    ip = rev['user']
                except socket.error:
                    user = rev['user']

                row = '\t'.join([id, ip, 'e' if minor else 'E', title, user, sum])
                row = row.replace('\n', ' ')
                row = row.replace('\r', ' ')

                f.write((row + '\n').encode("utf-8"))


def dumpMedia(url):
    prefix = domain2prefix(url)
    os.mkdir(prefix + '/media')
    os.mkdir(prefix + '/media_attic')
    os.mkdir(prefix + '/media_meta')

    fetch = urlparse.urljoin(url, 'lib/exe/fetch.php')

    files = getFiles(url)
    for title in files:
        titleparts = title.split(':')
        for i in range(len(titleparts)):
            dir = "/".join(titleparts[:i])
            if not os.path.exists(prefix + '/media/' + dir):
                os.mkdir(prefix + '/media/' + dir)
        with open(prefix + '/media/' + title.replace(':', '/'), 'wb') as f:
            f.write(requests.get(fetch, params={'media': title}).content)
        print 'File %s' % title
        time.sleep(1.5)


def dump(url):
    print domain2prefix(url)
    os.mkdir(domain2prefix(url))
    dumpContent(url)
    dumpMedia(url)

dump('http://localhost:9080/dokuwiki-2004-08-22/doku.php')
