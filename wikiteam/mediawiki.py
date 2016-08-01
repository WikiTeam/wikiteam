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
import sys
import urllib

import wikiteam

def mwCreateNewDump(config={}):
    print('Trying generating a new dump into a new directory...')
    if config['xml']:
        titles = mwGetPageTitles(config=config)
        mwSavePageTitles(config=config, images=images)
        mwGeneratePageDump(config=config, titles=titles)
        checkXMLIntegrity(config=config, titles=titles)
    if config['images']:
        images = mwGetImageNames(config=config)
        mwSaveImageNames(config=config, images=images)
        mwGenerateImageDump(config=config, images=images)
    if config['logs']:
        mwSaveLogs(config=config)

def mwGeneratePageDump(config={}, titles=[], start=None):
    """ Generates a XML dump for a list of titles """
    # TODO: titles is now unused.

    print('Retrieving the XML for every page from "%s"' % (start or 'start'))
    header, config = getXMLHeader(config=config)
    footer = '</mediawiki>\n'  # new line at the end
    xmlfilename = '%s-%s-%s.xml' % (wikiteam.domain2prefix(config=config),
                                    config['date'],
                                    config['curonly'] and 'current' or 'history')
    xmlfile = ''
    lock = True
    if start:
        print("Removing the last chunk of past XML dump: it is probably incomplete.")
        for i in reverse_readline('%s/%s' % (config['path'], xmlfilename), truncate=True):
            pass
    else:
        # requested complete xml dump
        lock = False
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'w')
        xmlfile.write(header.encode('utf-8'))
        xmlfile.close()

    xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'a')
    c = 1
    for title in readTitles(config, start):
        if not title.strip():
            continue
        if title == start:  # start downloading from start, included
            lock = False
        if lock:
            continue
        wikiteam.delay(config=config)
        if c % 10 == 0:
            print('Downloaded %d pages' % (c))
        try:
            for xml in getXMLPage(config=config, title=title):
                xml = cleanXML(xml=xml)
                xmlfile.write(xml.encode('utf-8'))
        except PageMissingError:
            logerror(
                config=config,
                text=u'The page "%s" was missing in the wiki (probably deleted)' %
                (title.decode('utf-8'))
            )
        # here, XML is a correct <page> </page> chunk or
        # an empty string due to a deleted page (logged in errors log) or
        # an empty string due to an error while retrieving the page from server
        # (logged in errors log)
        c += 1
    xmlfile.write(footer)
    xmlfile.close()
    print('XML dump saved at...', xmlfilename)

def mwGetAPI(config={}):
    """ Returns API for a MediaWiki wiki, if available """

    api = ''
    html = wikiteam.getURL(url=config['wiki'])
    m = re.findall(
        r'(?im)<\s*link\s*rel="EditURI"\s*type="application/rsd\+xml"\s*href="([^>]+?)\?action=rsd"\s*/\s*>',
        html)
    if m:
        api = m[0]
        if api.startswith('//'):  # gentoo wiki and others
            api = url.split('//')[0] + api
    return api

def mwGetIndex(config={}):
    """ Returns Index.php for a MediaWiki wiki, if available """

    if config['mwapi']:
        mwapi = config['mwapi']
    else:
        mwapi = mwGetAPI(config=config)
    index = ''
    html = wikiteam.getURL(url=config['wiki'])
    m = re.findall(r'<li id="ca-viewsource"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?', html)
    if m:
        index = m[0]
    else:
        m = re.findall(r'<li id="ca-history"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?', html)
        if m:
            index = m[0]
    if index:
        if index.startswith('/'):
            index = '/'.join(mwapi.split('/')[:-1]) + '/' + index.split('/')[-1]
    else:
        if mwapi:
            if len(re.findall(r'/index\.php5\?', html)) > len(re.findall(r'/index\.php\?', html)):
                index = '/'.join(mwapi.split('/')[:-1]) + '/index.php5'
            else:
                index = '/'.join(mwapi.split('/')[:-1]) + '/index.php'
    return index

def mwGetNamespacesAPI(config={}):
    """ Uses the API to get the list of namespaces names and ids """
    namespaces = config['namespaces']
    namespacenames = {0: ''}  # main is 0, no prefix
    if namespaces:
        params = {'action': 'query',
                'meta': 'siteinfo',
                'siprop': 'namespaces',
                'format': 'json'}
        data = urllib.parse.urlencode(params).encode()
        r = wikiteam.getURL(url=config['mwapi'], data=data)
        result = wikiteam.getJSON(r)
        wikiteam.delay(config=config)
        if 'all' in namespaces:
            namespaces = []
            for i in result['query']['namespaces'].keys():
                if int(i) < 0:  # -1: Special, -2: Media, excluding
                    continue
                namespaces.append(int(i))
                namespacenames[int(i)] = result['query']['namespaces'][i]['*']
        else:
            # check if those namespaces really exist in this wiki
            namespaces2 = []
            for i in result['query']['namespaces'].keys():
                bi = i
                i = int(i)
                if i < 0:  # -1: Special, -2: Media, excluding
                    continue
                if i in namespaces:
                    namespaces2.append(i)
                    namespacenames[i] = result['query']['namespaces'][bi]['*']
            namespaces = namespaces2
    else:
        namespaces = [0]

    namespaces = list(set(namespaces))  # uniques
    sys.stderr.write('%d namespaces found\n' % (len(namespaces)))
    return namespaces, namespacenames

def mwGetPageTitles(config={}):
    """ Get list of page titles """
    # http://en.wikipedia.org/wiki/Special:AllPages
    # http://archiveteam.org/index.php?title=Special:AllPages
    # http://www.wikanda.es/wiki/Especial:Todas
    sys.stderr.write('Loading page titles from namespaces = %s\n' % (','.join([str(i) for i in config['namespaces']]) or 'None'))
    sys.stderr.write('Excluding titles from namespaces = %s\n' % (','.join([str(i) for i in config['exnamespaces']]) or 'None'))

    if 'mwapi' in config and config['mwapi']:
        for pagetitle in mwGetPageTitlesAPI(config=config):
            yield pagetitle
    elif 'mwindex' in config and config['mwindex']:
        for pagetitle in mwGetPageTitlesScraper(config=config):
            yield pagetitle

def mwGetPageTitlesAPI(config={}):
    """ Uses the API to get the list of page titles """
    pagetitles = []
    namespaces, namespacenames = mwGetNamespacesAPI(
        config=config)
    for namespace in namespaces:
        if namespace in config['exnamespaces']:
            sys.stderr.write('    Skipping namespace = %d\n' % (namespace))
            continue

        c = 0
        sys.stderr.write('    Retrieving page titles in namespace %d\n' % (namespace))
        apfrom = '!'
        while apfrom:
            sys.stderr.write('.')  # progress
            params = {
                'action': 'query',
                'list': 'allpages',
                'apnamespace': namespace,
                'apfrom': apfrom.encode('utf-8'),
                'format': 'json',
                'aplimit': 500}
            data = urllib.parse.urlencode(params).encode()
            retryCount = 0
            while retryCount < config["retries"]:
                try:
                    r = wikiteam.getURL(url=config['mwapi'], data=data)
                    break
                except ConnectionError as err:
                    print("Connection error: %s" % (str(err),))
                    retryCount += 1
                    time.sleep(20)
            #wikiteam.handleStatusCode(r)
            # FIXME Handle HTTP errors here!
            jsontitles = wikiteam.getJSON(r)
            apfrom = ''
            if 'query-continue' in jsontitles and 'allpages' in jsontitles[
                    'query-continue']:
                if 'apcontinue' in jsontitles['query-continue']['allpages']:
                    apfrom = jsontitles[
                        'query-continue']['allpages']['apcontinue']
                elif 'apfrom' in jsontitles['query-continue']['allpages']:
                    apfrom = jsontitles['query-continue']['allpages']['apfrom']
            elif 'continue' in jsontitles:
                if 'apcontinue' in jsontitles['continue']:
                    apfrom = jsontitles['continue']['apcontinue']
                elif 'apfrom' in jsontitles['continue']:
                    apfrom = jsontitles['continue']['apfrom']
            
            # print apfrom
            # print jsontitles
            allpages = jsontitles['query']['allpages']
            # Hack for old versions of MediaWiki API where result is dict
            if isinstance(allpages, dict):
                allpages = allpages.values()
            for page in allpages:
                yield page['title']
            c += len(allpages)

            if len(pagetitles) != len(set(pagetitles)):
                # probably we are in a loop, server returning dupe titles, stop
                # it
                sys.stderr.write('Probably a loop, finishing\n')
                pagetitles = list(set(pagetitles))
                apfrom = ''

            wikiteam.delay(config=config)
        sys.stderr.write('    %d titles retrieved in namespace %d\n' % (c, namespace))

def main():
    pass

if __name__ == "__main__":
    main()
