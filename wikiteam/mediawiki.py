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

import json
import re
import sys
import urllib

import wikiteam

def mwCleanHTML(raw=''):
    """ Extract only the real wiki content and remove rubbish """
    """ This function is ONLY used to retrieve page titles and file names when no API is available """
    """ DO NOT use this function to extract page content """
    
    # different "tags" used by different MediaWiki versions to mark where
    # starts and ends content
    if re.search('<!-- bodytext -->', raw):
        raw = raw.split('<!-- bodytext -->')[1].split('<!-- /bodytext -->')[0]
    elif re.search('<!-- start content -->', raw):
        raw = raw.split(
            '<!-- start content -->')[1].split('<!-- end content -->')[0]
    elif re.search('<!-- Begin Content Area -->', raw):
        raw = raw.split(
            '<!-- Begin Content Area -->')[1].split('<!-- End Content Area -->')[0]
    elif re.search('<!-- content -->', raw):
        raw = raw.split('<!-- content -->')[1].split('<!-- mw_content -->')[0]
    elif re.search('<article id="WikiaMainContent" class="WikiaMainContent">', raw):
        raw = raw.split('<article id="WikiaMainContent" class="WikiaMainContent">')[1].split('</article>')[0]
    elif re.search('<body class=', raw):
        raw = raw.split('<body class=')[1].split('<div class="printfooter">')[0]
    else:
        sys.stderr.write(raw[:250])
        sys.stderr.write('This wiki doesn\'t use marks to split content\n')
        sys.exit()
    return raw

def mwCleanXML(xml=''):
    """ Trim redundant info """
    
    # do not touch XML codification, leave AS IS
    if re.search(r'</siteinfo>\n', xml):
        xml = xml.split('</siteinfo>\n')[1]
    if re.search(r'</mediawiki>', xml):
        xml = xml.split('</mediawiki>')[0]
    return xml

def mwCreateNewDump(config={}):
    sys.stderr.write('Trying generating a new dump into a new directory...')
    if config['pages']:
        pagetitles = mwGetPageTitles(config=config)
        wikiteam.savePageTitles(config=config, pagetitles=pagetitles)
        mwGeneratePageDump(config=config, pagetitles=pagetitles)
        mwCheckXMLIntegrity(config=config, pagetitles=pagetitles)
    if config['images']:
        imagenames = mwGetImageNames(config=config)
        mwSaveImageNames(config=config, imagenames=imagenames)
        mwGenerateImageDump(config=config, imagenames=imagenames)
    if config['logs']:
        mwSaveLogs(config=config)
    mwSaveIndexPHP(config=config)
    mwSaveSpecialVersion(config=config)
    mwSaveSiteInfo(config=config)

def mwCurateImageURL(config={}, url=''):
    """ Returns an absolute URL for an image, adding the domain if missing """

    if 'mwindex' in config and config['mwindex']:
        # remove from :// (http or https) until the first / after domain
        domainalone = config['mwindex'].split(
            '://')[0] + '://' + config['mwindex'].split('://')[1].split('/')[0]
    elif 'mwapi' in config and config['mwapi']:
        domainalone = config['mwapi'].split(
            '://')[0] + '://' + config['mwapi'].split('://')[1].split('/')[0]
    else:
        sys.stderr.write('ERROR: no index nor API')
        sys.exit()

    if url.startswith('//'):  # Orain wikifarm returns URLs starting with //
        url = '%s:%s' % (domainalone.split('://')[0], url)
    # is it a relative URL?
    elif url[0] == '/' or (not url.startswith('http://') and not url.startswith('https://')):
        if url[0] == '/':  # slash is added later
            url = url[1:]
        # concat http(s) + domain + relative url
        url = '%s/%s' % (domainalone, url)
    url = wikiteam.undoHTMLEntities(text=url)
    # url = urllib.unquote(url) #do not use unquote with url, it break some
    # urls with odd chars
    url = re.sub(' ', '_', url)
    
    return url

def mwGeneratePageDump(config={}, pagetitles=None, start=None):
    """ Generates a XML dump for page titles """
    
    sys.stderr.write('Retrieving XML for every page from "%s"' % (start or 'start'))
    header = mwGetXMLHeader(config=config)
    footer = '</mediawiki>\n'  # new line at the end
    xmlfilename = '%s-%s-%s.xml' % (wikiteam.domain2prefix(config=config),
                                    config['date'],
                                    config['curonly'] and 'current' or 'history')
    xmlfile = ''
    lock = True
    if start:
        sys.stderr.write("Removing the last chunk of past XML dump: it is probably incomplete.\n")
        for i in reverse_readline('%s/%s' % (config['path'], xmlfilename), truncate=True):
            pass
    else:
        # requested complete xml dump
        lock = False
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'w')
        xmlfile.write(header)
        xmlfile.close()

    xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'a')
    c = 1
    for pagetitle in mwGetPageTitles(config=config, start=start):
        if not pagetitle.strip():
            continue
        if pagetitle == start:  # start downloading from start, included
            lock = False
        if lock:
            continue
        wikiteam.delay(config=config)
        if c % 10 == 0:
            sys.stderr.write('Downloaded %d pages\n' % (c))
        try:
            for xml in getXMLPage(config=config, title=title):
                xml = cleanXML(xml=xml)
                xmlfile.write(xml)
        except PageMissingError:
            logerror(
                config=config,
                text='The page "%s" was missing in the wiki (probably deleted)' %
                (title))
        # here, XML is a correct <page> </page> chunk or
        # an empty string due to a deleted page (logged in errors log) or
        # an empty string due to an error while retrieving the page from server
        # (logged in errors log)
        c += 1
    xmlfile.write(footer)
    xmlfile.close()
    sys.stderr.write('XML dump saved at... %s\n' % (xmlfilename))

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

def mwGetImageNames(config={}):
    """ Get list of image names """

    sys.stderr.write('Retrieving image filenames\n')
    imagenames = []
    if 'mwapi' in config and config['mwapi']:
        imagenames = mwGetImageNamesAPI(config=config)
    elif 'mwindex' in config and config['mwindex']:
        imagenames = mwGetImageNamesScraper(config=config)
    # imagenames = list(set(imagenames)) # it is a list of lists
    imagenames.sort()
    sys.stderr.write('%d image names loaded\n' % (len(imagenames)))
    return imagenames

def mwGetImageNamesAPI(config={}):
    """ Retrieve file list: filename, url, uploader """
    
    oldAPI = False
    aifrom = '!'
    imagenames = []
    while aifrom:
        sys.stderr.write('.')  # progress
        data = {
            'action': 'query',
            'list': 'allimages',
            'aiprop': 'url|user',
            'aifrom': aifrom,
            'format': 'json',
            'ailimit': 500}
        # FIXME Handle HTTP Errors HERE
        r = wikiteam.getURL(url=config['mwapi'], data=data)
        #handleStatusCode(r)
        jsonimages = wikiteam.getJSON(r)
        wikiteam.delay(config=config)

        if 'query' in jsonimages:
            aifrom = ''
            if 'query-continue' in jsonimages and 'allimages' in jsonimages['query-continue']:
                if 'aicontinue' in jsonimages['query-continue']['allimages']:
                    aifrom = jsonimages['query-continue']['allimages']['aicontinue']
                elif 'aifrom' in jsonimages['query-continue']['allimages']:
                    aifrom = jsonimages['query-continue']['allimages']['aifrom']
            elif 'continue' in jsonimages:
                if 'aicontinue' in jsonimages['continue']:
                    aifrom = jsonimages['continue']['aicontinue']
                elif 'aifrom' in jsonimages['continue']:
                    aifrom = jsonimages['continue']['aifrom']
            # sys.stderr.write(aifrom)

            for image in jsonimages['query']['allimages']:
                url = image['url']
                url = mwCurateImageURL(config=config, url=url)
                # encoding to ascii is needed to work around this horrible bug:
                # http://bugs.python.org/issue8136
                if 'mwapi' in config and '.wikia.com' in config['mwapi']:
                    #to avoid latest?cb=20120816112532 in filenames
                    filename = urllib.parse.unquote(re.sub('_', ' ', url.split('/')[-3])).encode('ascii', 'ignore')
                else:
                    filename = urllib.parse.unquote(re.sub('_', ' ', url.split('/')[-1])).encode('ascii', 'ignore')
                uploader = re.sub('_', ' ', image['user'])
                imagenames.append([filename, url, uploader])
        else:
            oldAPI = True
            break

    if oldAPI:
        gapfrom = '!'
        imagenames = []
        while gapfrom:
            sys.stderr.write('.')  # progress
            # Some old APIs doesn't have allimages query
            # In this case use allpages (in nm=6) as generator for imageinfo
            # Example:
            # http://minlingo.wiki-site.com/api.php?action=query&generator=allpages&gapnamespace=6
            # &gaplimit=500&prop=imageinfo&iiprop=user|url&gapfrom=!
            data = {
                'action': 'query',
                'generator': 'allpages',
                'gapnamespace': 6,
                'gaplimit': 500,
                'gapfrom': gapfrom,
                'prop': 'imageinfo',
                'iiprop': 'user|url',
                'format': 'json'}
            # FIXME Handle HTTP Errors HERE
            r = wikiteam.getURL(url=config['mwapi'], data=data)
            #handleStatusCode(r)
            jsonimages = wikiteam.getJSON(r)
            wikiteam.delay(config=config)

            if 'query' in jsonimages:
                gapfrom = ''
                if 'query-continue' in jsonimages and 'allpages' in jsonimages['query-continue']:
                    if 'gapfrom' in jsonimages['query-continue']['allpages']:
                        gapfrom = jsonimages['query-continue']['allpages']['gapfrom']

                for image, props in jsonimages['query']['pages'].items():
                    url = props['imageinfo'][0]['url']
                    url = mwCurateImageURL(config=config, url=url)
                    tmp_filename = ':'.join(props['title'].split(':')[1:])
                    filename = re.sub('_', ' ', tmp_filename)
                    uploader = re.sub('_', ' ', props['imageinfo'][0]['user'])
                    imagenames.append([filename, url, uploader])
            else:
                # if the API doesn't return query data, then we're done
                break

    if len(imagenames) == 1:
        sys.stderr.write('    Found 1 image')
    else:
        sys.stderr.write('    Found %d images' % (len(imagenames)))

    return imagenames

def mwGetImageNamesScraper(config={}):
    """ Retrieve file list: filename, url, uploader """

    # (?<! http://docs.python.org/library/re.html
    r_next = r'(?<!&amp;dir=prev)&amp;offset=(?P<offset>\d+)&amp;'
    imagenames = []
    offset = '29990101000000'  # january 1, 2999
    limit = 5000
    retries = config['retries']
    while offset:
        # 5000 overload some servers, but it is needed for sites like this with
        # no next links
        # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
        data={
            'title': 'Special:Imagelist',
            'limit': limit,
            'offset': offset}
        raw = wikiteam.getURL(url=config['index'], data=data)
        #handleStatusCode(r)
        wikiteam.delay(config=config)
        # delicate wiki
        if re.search(r'(?i)(allowed memory size of \d+ bytes exhausted|Call to a member function getURL)', raw):
            if limit > 10:
                sys.stderr.write('Error: listing %d images in a chunk is not possible, trying tiny chunks' % (limit))
                limit = limit / 10
                continue
            elif retries > 0:  # waste retries, then exit
                retries -= 1
                sys.stderr.write('Retrying...')
                continue
            else:
                sys.stderr.write('No more retries, exit...')
                break

        raw = mwCleanHTML(raw)
        # archiveteam 1.15.1 <td class="TablePager_col_img_name"><a href="/index.php?title=File:Yahoovideo.jpg" title="File:Yahoovideo.jpg">Yahoovideo.jpg</a> (<a href="/images/2/2b/Yahoovideo.jpg">file</a>)</td>
        # wikanda 1.15.5 <td class="TablePager_col_img_user_text"><a
        # href="/w/index.php?title=Usuario:Fernandocg&amp;action=edit&amp;redlink=1"
        # class="new" title="Usuario:Fernandocg (página no
        # existe)">Fernandocg</a></td>
        r_images1 = r'(?im)<td class="TablePager_col_img_name"><a href[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+/[^>/]+)">[^<]+</a>[^<]+</td>\s*<td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'
        # wikijuegos 1.9.5
        # http://softwarelibre.uca.es/wikijuegos/Especial:Imagelist old
        # mediawiki version
        r_images2 = r'(?im)<td class="TablePager_col_links"><a href[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+/[^>/]+)">[^<]+</a></td>\s*<td class="TablePager_col_img_timestamp">[^<]+</td>\s*<td class="TablePager_col_img_name">[^<]+</td>\s*<td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'
        # gentoowiki 1.18
        r_images3 = r'(?im)<td class="TablePager_col_img_name"><a[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+)">[^<]+</a>[^<]+</td><td class="TablePager_col_thumb"><a[^>]+><img[^>]+></a></td><td class="TablePager_col_img_size">[^<]+</td><td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>'
        # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
        # (<a href="/en/Image:109_0923.JPG" title="Image:109 0923.JPG">desc</a>) <a href="/en/upload/c/cd/109_0923.JPG">109 0923.JPG</a> . . 885,713 bytes . . <a href="/en/User:Bfalconer" title="User:Bfalconer">Bfalconer</a> . . 18:44, 17 November 2005<br />
        r_images4 = r'(?im)<a href=[^>]+ title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+)">[^<]+</a>[^<]+<a[^>]+>(?P<uploader>[^<]+)</a>'
        r_images5 = (
            r'(?im)<td class="TablePager_col_img_name">\s*<a href[^>]*?>(?P<filename>[^>]+)</a>\s*\(<a href="(?P<url>[^>]+)">[^<]*?</a>\s*\)\s*</td>\s*'
            '<td class="TablePager_col_thumb">[^\n\r]*?</td>\s*'
            '<td class="TablePager_col_img_size">[^<]*?</td>\s*'
            '<td class="TablePager_col_img_user_text">\s*(<a href="[^>]*?" title="[^>]*?">)?(?P<uploader>[^<]+?)(</a>)?\s*</td>')

        # Select the regexp that returns more results
        regexps = [r_images1, r_images2, r_images3, r_images4, r_images5]
        count = 0
        i = 0
        regexp_best = 0
        for regexp in regexps:
            if len(re.findall(regexp, raw)) > count:
                count = len(re.findall(regexp, raw))
                regexp_best = i
            i += 1
        m = re.compile(regexps[regexp_best]).finditer(raw)

        # Iter the image results
        for i in m:
            url = i.group('url')
            url = mwCurateImageURL(config=config, url=url)
            filename = re.sub('_', ' ', i.group('filename'))
            filename = wikiteam.undoHTMLEntities(text=filename)
            filename = urllib.unquote(filename)
            uploader = re.sub('_', ' ', i.group('uploader'))
            uploader = wikiteam.undoHTMLEntities(text=uploader)
            uploader = urllib.unquote(uploader)
            imagenames.append([filename, url, uploader])

        if re.search(r_next, raw):
            new_offset = re.findall(r_next, raw)[0]
            # Avoid infinite loop
            if new_offset != offset:
                offset = new_offset
                retries += 5  # add more retries if we got a page with offset
            else:
                offset = ''
        else:
            offset = ''

    if (len(imagenames) == 1):
        sys.stderr.write('    Found 1 image')
    else:
        sys.stderr.write('    Found %d images' % (len(imagenames)))

    imagenames.sort()
    return imagenames

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

def mwGetNamespaces(config={}):
    """ Get list of namespaces """

    sys.stderr.write('Retrieving namespaces\n')
    namespaces = []
    namespacenames = []
    if 'mwapi' in config and config['mwapi']:
        namespaces, namespacenames = mwGetNamespacesAPI(config=config)
    elif 'mwindex' in config and config['mwindex']:
        namespaces, namespacenames = mwGetImageNamesScraper(config=config)
    namespaces.sort()
    sys.stderr.write('%d namespaces loaded\n' % (len(namespaces)))
    return namespaces, namespacenames

def mwGetNamespacesAPI(config={}):
    """ Uses the API to get the list of namespaces names and ids """
    namespaces = config['namespaces']
    namespacenames = {0: ''}  # main is 0, no prefix
    if namespaces:
        data = {'action': 'query',
                'meta': 'siteinfo',
                'siprop': 'namespaces',
                'format': 'json'}
        r = wikiteam.getURL(url=config['mwapi'], data=data)
        result = wikiteam.getJSON(r)
        wikiteam.delay(config=config)
        if 'all' in namespaces:
            namespaces = []
            for i in result['query']['namespaces'].keys():
                if int(i) < 0:  # Skipping -1: Special, -2: Media
                    continue
                namespaces.append(int(i))
                namespacenames[int(i)] = result['query']['namespaces'][i]['*']
        else:
            # check if those namespaces really exist in this wiki
            namespaces2 = []
            for i in result['query']['namespaces'].keys():
                if int(i) < 0:
                    continue
                if int(i) in namespaces:
                    namespaces2.append(int(i))
                    namespacenames[int(i)] = result['query']['namespaces'][i]['*']
            namespaces = namespaces2
    else:
        namespaces = [0]

    namespaces = list(set(namespaces))  # uniques
    sys.stderr.write('%d namespaces found\n' % (len(namespaces)))
    return namespaces, namespacenames

def mwGetNamespacesScraper(config={}):
    """ Hackishly gets the list of namespaces names and ids from the dropdown in the HTML of Special:AllPages """
    """ Function called if no API is available """
    
    namespaces = config['namespaces']
    namespacenames = {0: ''}  # main is 0, no prefix
    if namespaces:
        raw = wikiteam.getURL(url=config['index'], data={'title': 'Special:Allpages'})
        wikiteam.delay(config=config)

        # [^>]*? to include selected="selected"
        m = re.compile(r'<option [^>]*?value="(?P<namespaceid>\d+)"[^>]*?>(?P<namespacename>[^<]+)</option>').finditer(raw)
        if 'all' in namespaces:
            namespaces = []
            for i in m:
                namespaces.append(int(i.group("namespaceid")))
                namespacenames[int(i.group("namespaceid"))] = i.group("namespacename")
        else:
            # check if those namespaces really exist in this wiki
            namespaces2 = []
            for i in m:
                if int(i.group("namespaceid")) in namespaces:
                    namespaces2.append(int(i.group("namespaceid")))
                    namespacenames[int(i.group("namespaceid"))] = i.group("namespacename")
            namespaces = namespaces2
    else:
        namespaces = [0]

    namespaces = list(set(namespaces))  # uniques
    std.stderr.write('%d namespaces found' % (len(namespaces)))
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
            data = {
                'action': 'query',
                'list': 'allpages',
                'apnamespace': namespace,
                'apfrom': apfrom.encode('utf-8'),
                'format': 'json',
                'aplimit': 500}
            retryCount = 0
            while retryCount < config["retries"]:
                try:
                    r = wikiteam.getURL(url=config['mwapi'], data=data)
                    break
                except ConnectionError as err:
                    sys.stderr.write("Connection error: %s\n" % (str(err),))
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
            
            # sys.stderr.write(apfrom)
            # sys.stderr.write(jsontitles)
            allpages = jsontitles['query']['allpages']
            # Hack for old versions of MediaWiki API where result is dict
            if isinstance(allpages, dict):
                allpages = allpages.values()
            for page in allpages:
                yield page['title']
            c += len(allpages)

            if len(pagetitles) != len(set(pagetitles)):
                # Are we in a loop? Server returning dupes, stop it
                sys.stderr.write('Probably a loop, finishing\n')
                apfrom = ''

            wikiteam.delay(config=config)
        sys.stderr.write('    %d titles retrieved in namespace %d\n' % (c, namespace))


def mwGetPageTitlesScraper(config={}):
    """ Scrape list of page titles from Special:Allpages """
    
    pagetitles = []
    namespaces, namespacenames = mwGetNamespacesScraper(
        config=config)
    for namespace in namespaces:
        sys.stderr.write('    Retrieving titles in namespace %s\n' % (namespace))
        url = '%s?title=Special:Allpages&namespace=%s' % (config['index'], namespace)
        raw = wikiteam.getURL(url=url)
        raw = mwCleanHTML(raw)

        r_title = r'title="(?P<title>[^>]+)">'
        r_suballpages = ''
        r_suballpages1 = r'&amp;from=(?P<from>[^>]+)&amp;to=(?P<to>[^>]+)">'
        r_suballpages2 = r'Special:Allpages/(?P<from>[^>]+)">'
        r_suballpages3 = r'&amp;from=(?P<from>[^>]+)" title="[^>]+">'
        if re.search(r_suballpages1, raw):
            r_suballpages = r_suballpages1
        elif re.search(r_suballpages2, raw):
            r_suballpages = r_suballpages2
        elif re.search(r_suballpages3, raw):
            r_suballpages = r_suballpages3
        else:
            pass  # perhaps no subpages

        # 3 is the current deep of English Wikipedia for Special:Allpages
        deep = 3
        c = 0
        checked_suballpages = []
        rawacum = raw
        while r_suballpages and re.search(r_suballpages, raw) and c < deep:
            # load sub-Allpages
            m = re.compile(r_suballpages).finditer(raw)
            for i in m:
                fr = i.group('from')

                if r_suballpages == r_suballpages1:
                    to = i.group('to')
                    name = '%s-%s' % (fr, to)
                    url = '%s?title=Special:Allpages&namespace=%s&from=%s&to=%s' % (
                        config['index'], namespace, fr, to)  # do not put urllib.quote in fr or to
                # fix, esta regexp no carga bien todas? o falla el r_title en
                # este tipo de subpag? (wikiindex)
                elif r_suballpages == r_suballpages2:
                    # clean &amp;namespace=\d, sometimes happens
                    fr = fr.split('&amp;namespace=')[0]
                    name = fr
                    url = '%s?title=Special:Allpages/%s&namespace=%s' % (
                        config['index'], name, namespace)
                elif r_suballpages == r_suballpages3:
                    fr = fr.split('&amp;namespace=')[0]
                    name = fr
                    url = '%s?title=Special:Allpages&from=%s&namespace=%s' % (
                        config['index'], name, namespace)

                if name not in checked_suballpages:
                    # to avoid reload dupe subpages links
                    checked_suballpages.append(name)
                    wikiteam.delay(config=config)
                    raw2 = wikiteam.getURL(url=url)
                    raw2 = mwCleanHTML(raw2)
                    rawacum += raw2  # merge it after removed junk
                    sys.stderr.write('    Reading %s, %s bytes, %d subpages, %d pages' % (name, len(raw2), \
                        len(re.findall(r_suballpages, raw2)), \
                        len(re.findall(r_title, raw2))))

                wikiteam.delay(config=config)
            c += 1

        c = 0
        m = re.compile(r_title).finditer(rawacum)
        for i in m:
            t = wikiteam.undoHTMLEntities(text=i.group('title'))
            if not t.startswith('Special:'):
                if t not in pagetitles:
                    pagetitles.append(t)
                    c += 1
        sys.stderr.write('    %d titles retrieved in the namespace %d\n' % (c, namespace))
    return pagetitles

def mwGetXMLHeader(config={}):
    """ Retrieve a random page to extract XML header (namespace info, etc) """

    pagetitle = 'Main_Page'
    try:
        xml = "".join([x for x in mwGetXMLPage(config=config, pagetitle=pagetitle, verbose=False)])
    except PageMissingError as pme:
        # The <page> does not exist. Not a problem, if we get the <siteinfo>.
        xml = pme.xml
    except ExportAbortedError:
        # Issue 26: Account for missing "Special" namespace.
        # Hope the canonical special name has not been removed.
        # http://albens73.fr/wiki/api.php?action=query&meta=siteinfo&siprop=namespacealiases
        try:
            if config['mwapi']:
                sys.stderr.write("Trying the local name for the Special namespace instead\n")
                xml = "".join([x for x in mwGetXMLPage(config=config, pagetitle=pagetitle, verbose=False)])
        except PageMissingError as pme:
            xml = pme.xml
        except ExportAbortedError:
            pass

    header = xml.split('</mediawiki>')[0]
    if not re.match(r"\s*<mediawiki", xml):
        sys.stderr.write('XML export on this wiki is broken, quitting.\n')
        logerror('XML export on this wiki is broken, quitting.')
        sys.exit()
    return header

def mwGetXMLPage(config={}, pagetitle='', verbose=True):
    """ Get the full history (or current only) of a page """

    # if server errors occurs while retrieving the full page history, it may return [oldest OK versions] + last version, excluding middle revisions, so it would be partialy truncated
    # http://www.mediawiki.org/wiki/Manual_talk:Parameters_to_Special:Export#Parameters_no_longer_in_use.3F

    limit = 1000
    truncated = False
    pagetitle_ = re.sub(' ', '_', pagetitle)
    # do not convert & into %26, pagetitle_ = re.sub('&', '%26', pagetitle_)
    data = {'title': config['mwexport'], 'pages': pagetitle_, 'action': 'submit'}
    if config['curonly']:
        data['curonly'] = 1
        data['limit'] = 1
    else:
        data['offset'] = '1'  # 1 always < 2000s
        data['limit'] = limit
    # in other case, do not set data['templates']
    if 'templates' in config and config['templates']: #fix, what is this option for?
        data['templates'] = 1

    xml = mwGetXMLPageCore(config=config, data=data)
    if not xml:
        raise ExportAbortedError(config['index'])
    if not "</page>" in xml:
        raise PageMissingError(data['title'], xml)
    else:
        # strip these sha1s sums which keep showing up in the export and
        # which are invalid for the XML schema (they only apply to
        # revisions)
        xml = re.sub(r'\n\s*<sha1>\w+</sha1>\s*\n', r'\n', xml)
        xml = re.sub(r'\n\s*<sha1/>\s*\n', r'\n', xml)

    yield xml.split("</page>")[0]

    # if complete history, check if this page history has > limit edits,
    # if so, retrieve all revisions using offset if available
    # else, warning about Special:Export truncating large page histories
    r_timestamp = r'<timestamp>([^<]+)</timestamp>'
    numedits = 0
    numedits += len(re.findall(r_timestamp, xml))

    # search for timestamps in xml to avoid analysing empty pages like
    # Special:Allpages and the random one
    if not config['curonly'] and re.search(r_timestamp, xml):
        while not truncated and data['offset']:  # next chunk
            # get the last timestamp from the acum XML
            # assuming history is sorted chronologically
            data['offset'] = re.findall(r_timestamp, xml)[-1]
            try:
                xml2 = mwGetXMLPageCore(config=config, data=data)
            except MemoryError:
                sys.stderr.write("Page history exceeds our memory, halving limit.\n")
                data['limit'] = data['limit'] / 2
                continue

            # are there more edits in this next XML chunk or no <page></page>?
            if re.findall(r_timestamp, xml2):
                if re.findall(r_timestamp, xml2)[-1] == data['offset']:
                    # again the same XML, this wiki does not support params in
                    # Special:Export, offer complete XML up to X edits (usually
                    # 1000)
                    sys.stderr.write('ATTENTION: This wiki does not allow some parameters in Special:Export, therefore pages with large histories may be truncated\n')
                    truncated = True
                    break
                else:
                    """    </namespaces>
                      </siteinfo>
                      <page>
                        <title>Main Page</title>
                        <id>15580374</id>
                        <restrictions>edit=sysop:move=sysop</restrictions> (?)
                        <revision>
                          <id>418009832</id>
                          <timestamp>2011-03-09T19:57:06Z</timestamp>
                          <contributor>
                    """
                    # offset is OK in this wiki, merge with the previous chunk
                    # of this page history and continue
                    try:
                        xml2 = xml2.split("</page>")[0]
                        yield '  <revision>' + ('<revision>'.join(xml2.split('<revision>')[1:]))
                    except MemoryError:
                        sys.stderr.write("Page's history exceeds our memory, halving limit.\n")
                        data['limit'] = data['limit'] / 2
                        continue
                    xml = xml2
                    numedits += len(re.findall(r_timestamp, xml))
            else:
                data['offset'] = ''  # no more edits in this page history
    yield "</page>\n"

    if verbose:
        if numedits == 1:
           sys.stderr.write('    %s, 1 edit\n' % (pagetitle))
        else:
           sys.stderr.write('    %s, %d edits\n' % (pagetitle, numedits))

def mwGetXMLPageCore(config={}, data={}):
    """ Returns a XML containing data['limit'] revisions (or current only), ending in </mediawiki>
        if retrieving data['limit'] revisions fails, returns current only version
        if all fail, returns empty string
    """
    
    xml = ''
    cretries = 0
    maxseconds = 100  # max seconds to wait in a single sleeping
    maxretries = config['retries']  # x retries and exit
    increment = 20  # increment seconds every retry

    while not re.search(r'</mediawiki>', xml):
        if cretries > 0 and cretries < maxretries:
            wait = increment * cretries < maxseconds and increment * \
                cretries or maxseconds  # incremental until maxseconds
            sys.stderr.write('    In attempt %d, XML for "%s" is wrong. Waiting %d seconds and reloading...\n' % (c, data['pages'], wait))
            time.sleep(wait)
            # reducing server load requesting smallest chunks (if curonly then
            # limit = 1 from mother function)
            if data['limit'] > 1:
                data['limit'] = data['limit'] / 2  # half
        if cretries >= maxretries:
            sys.stderr.write('    We have retried %d times\n' % (cretries))
            sys.stderr.write('    MediaWiki error for "%s", probably network error...' % (data['pages']))
            # If it's not already what we tried: our last chance, preserve only the last revision...
            # config['curonly'] means that the whole dump is configured to save only the last,
            # data['curonly'] should mean that we've already tried this
            # fallback, because it's set by the following if and passed to
            # mwGetXMLPageCore
            if not config['curonly'] and not 'curonly' in data:
                sys.stderr.write('    Trying to save only the last revision for this page...\n')
                data['curonly'] = 1
                logerror(
                    config=config,
                    text='Error while retrieving the full history of "%s". Trying to save only the last revision for this page' %
                    (data['pages'])
                )
                return mwGetXMLPageCore(config=config, data=data)
            else:
                sys.stderr.write('    Saving in error log, skipping...\n')
                logerror(
                    config=config,
                    text='Error while retrieving last revision of "%s". Skipping.\n' %
                    (data['pages']))
                raise ExportAbortedError(config['index'])
                return ''  # empty xml
        # FIXME HANDLE HTTP Errors HERE
        try:
            r = wikiteam.getURL(url=config['index'], data=data)
            #handleStatusCode(r)
            #r = fixBOM(r)
            xml = fixBOM(r)
        except:
            sys.stderr.write('    Connection error\n')
            xml = ''
        cretries += 1

    return xml

def mwReadPageTitles(config={}, start=None):
    """ Read title list from a file, from the title "start" """

    titlesfilename = '%s-%s-titles.txt' % (
        domain2prefix(config=config), config['date'])
    titlesfile = open('%s/%s' % (config['path'], titlesfilename), 'r')

    seeking = False
    if start:
        seeking = True

    with titlesfile as f:
        for line in f:
            if line.strip() == '--END--':
                break
            elif seeking and line.strip() != start:
                continue
            elif seeking and line.strip() == start:
                seeking = False
                yield line.strip()
            else:
                yield line.strip()

def mwRemoveIP(raw=''):
    """ Remove IP from HTML comments <!-- --> """

    raw = re.sub(r'\d+\.\d+\.\d+\.\d+', '0.0.0.0', raw)
    # http://www.juniper.net/techpubs/software/erx/erx50x/swconfig-routing-vol1/html/ipv6-config5.html
    # weird cases as :: are not included
    raw = re.sub(
        r'(?i)[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}',
        '0:0:0:0:0:0:0:0',
        raw)

    return raw

def mwResumePreviousDump(config={}):
    imagenames = []
    sys.stderr.write('Resuming previous dump process...')
    if config['xml']:
        pagetitles = mwReadPageTitles(config=config)
        try:
            lasttitles = wikiteam.reverseReadline('%s/%s-%s-titles.txt' % (config['path'], domain2prefix(config=config), config['date']))
            lasttitle=lasttitles.next()
            if lasttitle == '':
                lasttitle=lasttitles.next()
        except:
            pass  # probably file does not exists
        if lasttitle == '--END--':
            # titles list is complete
            sys.stderr.write('Title list was completed in the previous session')
        else:
            sys.stderr.write('Title list is incomplete. Reloading...')
            # do not resume, reload, to avoid inconsistences, deleted pages or
            # so
            pagetitles = mwGetPageTitles(config=config, start=lastxmltitle)
            wikiteam.savePageTitles(config=config, pagetitles=pagetitles)

        # checking xml dump
        xmliscomplete = False
        lastxmltitle = None
        try:
            f = wikiteam.reverseReadline(
                '%s/%s-%s-%s.xml' %
                (config['path'],
                 domain2prefix(
                    config=config),
                    config['date'],
                    config['curonly'] and 'current' or 'history'),
                )
            for l in f:
                if l == '</mediawiki>':
                    # xml dump is complete
                    xmliscomplete = True
                    break

                xmltitle = re.search(r'<title>([^<]+)</title>', l)
                if xmltitle:
                    lastxmltitle = wikiteam.undoHTMLEntities(text=xmltitle.group(1))
                    break
        except:
            pass  # probably file does not exists

        if xmliscomplete:
            sys.stderr.write('XML dump was completed in the previous session')
        elif lastxmltitle:
            # resuming...
            sys.stderr.write('Resuming XML dump from "%s"' % (lastxmltitle))
            pagetitles = mwReadPageTitles(config=config, start=lastxmltitle)
            mwGenerateXMLDump(
                config=config,
                pagetitles=pagetitles,
                start=lastxmltitle)
        else:
            # corrupt? only has XML header?
            sys.stderr.write('XML is corrupt? Regenerating...')
            pagetitles = mwReadPageTitles(config=config)
            mwGenerateXMLDump(config=config, pagetitles=pagetitles)

    if config['images']:
        # load images
        lastimage = ''
        try:
            f = open('%s/%s-%s-images.txt' % (config['path'], domain2prefix(config=config), config['date']), 'r')
            raw = f.read().strip()
            lines = raw.split('\n')
            for l in lines:
                if re.search(r'\t', l):
                    imagenames.append(l.split('\t'))
            lastimage = lines[-1]
            f.close()
        except:
            pass  # probably file doesnot exists
        if lastimage == '--END--':
            sys.stderr.write('Image list was completed in the previous session')
        else:
            sys.stderr.write('Image list is incomplete. Reloading...')
            # do not resume, reload, to avoid inconsistences, deleted images or
            # so
            imagenames = mwGetImageNames(config=config)
            saveImageNames(config=config, imagenames=imagenames)
        # checking images directory
        listdir = []
        try:
            listdir = [n.decode('utf-8') for n in os.listdir('%s/images' % (config['path']))]
        except:
            pass  # probably directory does not exist
        listdir.sort()
        complete = True
        lastfilename = ''
        lastfilename2 = ''
        c = 0
        for filename, url, uploader in imagenames:
            lastfilename2 = lastfilename
            # return always the complete filename, not the truncated
            lastfilename = filename
            filename2 = filename
            if len(filename2) > other['filenamelimit']:
                filename2 = truncateFilename(other=other, filename=filename2)
            if filename2 not in listdir:
                complete = False
                break
            c += 1
        sys.stderr.write('%d images were found in the directory from a previous session' % (c))
        if complete:
            # image dump is complete
            sys.stderr.write('Image dump was completed in the previous session')
        else:
            # we resume from previous image, which may be corrupted (or missing
            # .desc)  by the previous session ctrl-c or abort
            mwGenerateImageDump(config=config, imagenames=imagenames, start=lastfilename2)

    if config['logs']:
        # fix
        pass

    mwSaveIndexPHP(config=config)
    mwSaveSpecialVersion(config=config)
    mwSaveSiteInfo(config=config)

def mwSaveIndexPHP(config={}):
    """ Save index.php as .html, to preserve license details available at the botom of the page """

    if os.path.exists('%s/index.html' % (config['path'])):
        sys.stderr.write('index.html exists, do not overwrite')
    else:
        sys.stderr.write('Downloading index.php (Main Page) as index.html')
        raw = wikiteam.getURL(url=config['index'], data={})
        wikiteam.delay(config=config)
        raw = mwRemoveIP(raw=raw)
        with open('%s/index.html' % (config['path']), 'w') as outfile:
            outfile.write(raw)

def mwSaveSiteInfo(config={}):
    """ Save a file with site info """

    if config['api']:
        if os.path.exists('%s/siteinfo.json' % (config['path'])):
            sys.stderr.write('siteinfo.json exists, do not overwrite')
        else:
            sys.stderr.write('Downloading site info as siteinfo.json')

            # MediaWiki 1.13+
            raw = wikiteam.getURL(url=config['api'], data={
                'action': 'query',
                'meta': 'siteinfo',
                'siprop': 'general|namespaces|statistics|dbrepllag|interwikimap|namespacealiases|specialpagealiases|usergroups|extensions|skins|magicwords|fileextensions|rightsinfo',
                'sinumberingroup': 1,
                'format': 'json'})
            wikiteam.delay(config=config)
            # MediaWiki 1.11-1.12
            if not 'query' in wikiteam.getJSON(raw):
                raw = wikiteam.getURL(url=config['api'], data={
                    'action': 'query',
                    'meta': 'siteinfo',
                    'siprop': 'general|namespaces|statistics|dbrepllag|interwikimap',
                    'format': 'json'})
            # MediaWiki 1.8-1.10
            if not 'query' in wikiteam.getJSON(raw):
                raw = wikiteam.getURL(url=config['api'], data={
                    'action': 'query',
                    'meta': 'siteinfo',
                    'siprop': 'general|namespaces',
                    'format': 'json'})
            result = wikiteam.getJSON(raw)
            wikiteam.delay(config=config)
            with open('%s/siteinfo.json' % (config['path']), 'w') as outfile:
                outfile.write(json.dumps(result, indent=4, sort_keys=True))

def mwSaveSpecialVersion(config={}):
    """ Save Special:Version as .html, to preserve extensions details """

    if os.path.exists('%s/Special:Version.html' % (config['path'])):
        sys.stderr.write('Special:Version.html exists, do not overwrite')
    else:
        sys.stderr.write('Downloading Special:Version with extensions and other related info')
        raw = wikiteam.getURL(url=config['index'], data={'title': 'Special:Version'})
        wikiteam.delay(config=config)
        raw = mwRemoveIP(raw=raw)
        with open('%s/Special:Version.html' % (config['path']), 'w') as outfile:
            outfile.write(raw)

def main():
    pass

if __name__ == "__main__":
    main()
