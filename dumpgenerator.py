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

import cookielib
import cPickle
import datetime
import sys
try:
    import argparse
except ImportError:
    print "Please install the argparse module."
    sys.exit(1)
import json
try:
    from hashlib import md5
except ImportError:             # Python 2.4 compatibility
    from md5 import new as md5
import os
import re
try:
    import requests
except ImportError:
    print "Please install or update the Requests module."
    sys.exit(1)
import time
import urllib

__VERSION__ = '0.3.0-alpha'  # major, minor, micro: semver.org


def getVersion():
    return(__VERSION__)


def truncateFilename(other={}, filename=''):
    """ Truncate filenames when downloading images with large filenames """
    return filename[:other['filenamelimit']] + md5(filename).hexdigest() + '.' + filename.split('.')[-1]


def delay(config={}, session=None):
    """ Add a delay if configured for that """
    if config['delay'] > 0:
        print 'Sleeping... %d seconds...' % (config['delay'])
        time.sleep(config['delay'])


def cleanHTML(raw=''):
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
        print raw[:250]
        print 'This wiki doesn\'t use marks to split content'
        sys.exit()
    return raw


def handleStatusCode(response):
    statuscode = response.status_code
    if statuscode >= 200 and statuscode < 300:
        return

    print "HTTP Error %d." % statuscode
    if statuscode >= 300 and statuscode < 400:
        print "Redirect should happen automatically: please report this as a bug."
        print response.url

    elif statuscode == 400:
        print "Bad Request: The wiki may be malfunctioning."
        print "Please try again later."
        print response.url
        sys.exit(1)

    elif statuscode == 401 or statuscode == 403:
        print "Authentication required."
        print "Please use --userpass."
        print response.url

    elif statuscode == 404:
        print "Not found. Is Special:Export enabled for this wiki?"
        print response.url
        sys.exit(1)

    elif statuscode == 429 or (statuscode >= 500 and statuscode < 600):
        print "Server error, max retries exceeded."
        print "Please resume the dump later."
        print response.url
        sys.exit(1)


def getNamespacesScraper(config={}, session=None):
    """ Hackishly gets the list of namespaces names and ids from the dropdown in the HTML of Special:AllPages """
    """ Function called if no API is available """
    namespaces = config['namespaces']
    namespacenames = {0: ''}  # main is 0, no prefix
    if namespaces:
        r = session.post(
            url=config['index'], data={'title': 'Special:Allpages'})
        raw = r.text
        delay(config=config, session=session)

        # [^>]*? to include selected="selected"
        m = re.compile(
            r'<option [^>]*?value="(?P<namespaceid>\d+)"[^>]*?>(?P<namespacename>[^<]+)</option>').finditer(raw)
        if 'all' in namespaces:
            namespaces = []
            for i in m:
                namespaces.append(int(i.group("namespaceid")))
                namespacenames[int(i.group("namespaceid"))] = i.group(
                    "namespacename")
        else:
            # check if those namespaces really exist in this wiki
            namespaces2 = []
            for i in m:
                if int(i.group("namespaceid")) in namespaces:
                    namespaces2.append(int(i.group("namespaceid")))
                    namespacenames[int(i.group("namespaceid"))] = i.group(
                        "namespacename")
            namespaces = namespaces2
    else:
        namespaces = [0]

    namespaces = list(set(namespaces))  # uniques
    print '%d namespaces found' % (len(namespaces))
    return namespaces, namespacenames


def getNamespacesAPI(config={}, session=None):
    """ Uses the API to get the list of namespaces names and ids """
    namespaces = config['namespaces']
    namespacenames = {0: ''}  # main is 0, no prefix
    if namespaces:
        r = session.post(url=config['api'], data={
                         'action': 'query', 'meta': 'siteinfo', 'siprop': 'namespaces', 'format': 'json'})
        result = json.loads(r.text)
        delay(config=config, session=session)

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
                if int(i) < 0:  # -1: Special, -2: Media, excluding
                    continue
                if int(i) in namespaces:
                    namespaces2.append(int(i))
                    namespacenames[int(i)] = result['query']['namespaces'][i]['*']
            namespaces = namespaces2
    else:
        namespaces = [0]

    namespaces = list(set(namespaces))  # uniques
    print '%d namespaces found' % (len(namespaces))
    return namespaces, namespacenames


def getPageTitlesAPI(config={}, session=None):
    """ Uses the API to get the list of page titles """
    titles = []
    namespaces, namespacenames = getNamespacesAPI(
        config=config, session=session)
    for namespace in namespaces:
        if namespace in config['exnamespaces']:
            print '    Skipping namespace = %d' % (namespace)
            continue

        c = 0
        print '    Retrieving titles in the namespace %d' % (namespace)
        apfrom = '!'
        while apfrom:
            sys.stderr.write('.')  # progress
            params = {'action': 'query', 'list': 'allpages', 'apnamespace': namespace,
                      'apfrom': apfrom.encode('utf-8'), 'format': 'json', 'aplimit': 500}
            r = session.post(url=config['api'], data=params)
            handleStatusCode(r)
            # FIXME Handle HTTP errors here!
            jsontitles = json.loads(r.text)
            apfrom = ''
            if 'query-continue' in jsontitles and 'allpages' in jsontitles['query-continue']:
                if 'apcontinue' in jsontitles['query-continue']['allpages']:
                    apfrom = jsontitles['query-continue']['allpages']['apcontinue']
                elif 'apfrom' in jsontitles['query-continue']['allpages']:
                    apfrom = jsontitles['query-continue']['allpages']['apfrom']
            # print apfrom
            # print jsontitles
            titles += [page['title']
                       for page in jsontitles['query']['allpages']]
            if len(titles) != len(set(titles)):
                # probably we are in a loop, server returning dupe titles, stop
                # it
                print 'Probably a loop, finishing'
                titles = list(set(titles))
                apfrom = ''
            c += len(jsontitles['query']['allpages'])
            delay(config=config, session=session)
        print '    %d titles retrieved in the namespace %d' % (c, namespace)
    return titles


def getPageTitlesScraper(config={}, session=None):
    """  """
    titles = []
    namespaces, namespacenames = getNamespacesScraper(
        config=config, session=session)
    for namespace in namespaces:
        print '    Retrieving titles in the namespace', namespace
        url = '%s?title=Special:Allpages&namespace=%s' % (
            config['index'], namespace)
        r = session.get(url=url)
        raw = r.text
        raw = cleanHTML(raw)

        r_title = r'title="(?P<title>[^>]+)">'
        r_suballpages = ''
        r_suballpages1 = r'&amp;from=(?P<from>[^>]+)&amp;to=(?P<to>[^>]+)">'
        r_suballpages2 = r'Special:Allpages/(?P<from>[^>]+)">'
        if re.search(r_suballpages1, raw):
            r_suballpages = r_suballpages1
        elif re.search(r_suballpages2, raw):
            r_suballpages = r_suballpages2
        else:
            pass  # perhaps no subpages

        # 3 is the current deep of English Wikipedia for Special:Allpages, 3
        # levels
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

                if name not in checked_suballpages:
                    # to avoid reload dupe subpages links
                    checked_suballpages.append(name)
                    delay(config=config, session=session)
                    r2 = session.get(url=url)
                    raw2 = r2.text
                    raw2 = cleanHTML(raw2)
                    rawacum += raw2  # merge it after removed junk
                    print '    Reading', name, len(raw2), 'bytes', len(re.findall(r_suballpages, raw2)), 'subpages', len(re.findall(r_title, raw2)), 'pages'

                delay(config=config, session=session)
            c += 1

        c = 0
        m = re.compile(r_title).finditer(rawacum)
        for i in m:
            t = undoHTMLEntities(text=i.group('title'))
            if not t.startswith('Special:'):
                if t not in titles:
                    titles.append(t)
                    c += 1
        print '    %d titles retrieved in the namespace %d' % (c, namespace)
    return titles


def getPageTitles(config={}, session=None):
    """ Get list of page titles """
    # http://en.wikipedia.org/wiki/Special:AllPages
    # http://archiveteam.org/index.php?title=Special:AllPages
    # http://www.wikanda.es/wiki/Especial:Todas
    print 'Loading page titles from namespaces = %s' % (config['namespaces'] and ','.join([str(i) for i in config['namespaces']]) or 'None')
    print 'Excluding titles from namespaces = %s' % (config['exnamespaces'] and ','.join([str(i) for i in config['exnamespaces']]) or 'None')

    titles = []
    if 'api' in config and config['api']:
        titles = getPageTitlesAPI(config=config, session=session)
    elif 'index' in config and config['index']:
        titles = getPageTitlesScraper(config=config, session=session)

    # removing dupes (e.g. in CZ appears Widget:AddThis two times (main
    # namespace and widget namespace))
    titles = list(set(titles))
    titles.sort()

    print '%d page titles loaded' % (len(titles))
    return titles


def getImageNames(config={}, session=None):
    """ Get list of image names """
    
    print 'Retrieving image filenames'
    images = []
    if 'api' in config and config['api']:
        images = getImageNamesAPI(config=config, session=session)
    elif 'index' in config and config['index']:
        images = getImageNamesScraper(config=config, session=session)

    #images = list(set(images)) # it is a list of lists
    images.sort()

    print '%d image names loaded' % (len(images))
    return images


def getXMLHeader(config={}, session=None):
    """ Retrieve a random page to extract XML headers (namespace info, etc) """
    # get the header of a random page, to attach it in the complete XML backup
    # similar to: <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/"
    # xmlns:x....
    randomtitle = 'Main_Page'  # previously AMF5LKE43MNFGHKSDMRTJ
    xml = getXMLPage(
        config=config, title=randomtitle, verbose=False, session=session)
    header = xml.split('</mediawiki>')[0]
    if not xml:
        print 'XML export on this wiki is broken, quitting.'
        sys.exit()
    return header


def getXMLFileDesc(config={}, title='', session=None):
    """ Get XML for image description page """
    config['curonly'] = 1  # tricky to get only the most recent desc
    return getXMLPage(config=config, title=title, verbose=False, session=session)


def getUserAgent():
    """ Return a cool user-agent to hide Python user-agent """
    useragents = [
        # firefox
        'Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101  Firefox/28.0',
    ]
    return useragents[0]


def logerror(config={}, text=''):
    """ Log error in file """
    if text:
        with open('%s/errors.log' % (config['path']), 'a') as outfile:
            output = u'%s: %s\n' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), text)
            outfile.write(output.encode('utf-8'))


def getXMLPageCore(headers={}, params={}, config={}, session=None):
    """  """
    # returns a XML containing params['limit'] revisions (or current only), ending in </mediawiki>
    # if retrieving params['limit'] revisions fails, returns a current only version
    # if all fail, returns the empty string
    xml = ''
    c = 0
    maxseconds = 100  # max seconds to wait in a single sleeping
    maxretries = 5  # x retries and skip
    increment = 20  # increment every retry
    while not re.search(r'</mediawiki>', xml):
        if c > 0 and c < maxretries:
            wait = increment * c < maxseconds and increment * \
                c or maxseconds  # incremental until maxseconds
            print '    XML for "%s" is wrong. Waiting %d seconds and reloading...' % (params['pages'], wait)
            time.sleep(wait)
            # reducing server load requesting smallest chunks (if curonly then
            # limit = 1 from mother function)
            if params['limit'] > 1:
                params['limit'] = params['limit'] / 2  # half
        if c >= maxretries:
            print '    We have retried %d times' % (c)
            print '    MediaWiki error for "%s", network error or whatever...' % (params['pages'])
            # If it's not already what we tried: our last chance, preserve only the last revision...
            # config['curonly'] means that the whole dump is configured to save nonly the last
            # params['curonly'] should mean that we've already tried this
            # fallback, because it's set by the following if and passed to
            # getXMLPageCore
            if not config['curonly']:
                print '    Trying to save only the last revision for this page...'
                params['curonly'] = 1
                logerror(config=config, text='Error while retrieving the full history of "%s". Trying to save only the last revision for this page' % (
                    params['pages']))
                return getXMLPageCore(headers=headers, params=params, config=config, session=session)
            else:
                print '    Saving in the errors log, and skipping...'
                logerror(config=config, text='Error while retrieving the last revision of "%s". Skipping.' % (
                    params['pages']))
                return ''  # empty xml
        # FIXME HANDLE HTTP Errors HERE
        r = session.post(url=config['index'], data=params, headers=headers)
        handleStatusCode(r)
        xml = r.text
        c += 1

    return xml


def getXMLPage(config={}, title='', verbose=True, session=None):
    """ Get the full history (or current only) of a page """

    # if server errors occurs while retrieving the full page history, it may return [oldest OK versions] + last version, excluding middle revisions, so it would be partialy truncated
    # http://www.mediawiki.org/wiki/Manual_talk:Parameters_to_Special:Export#Parameters_no_longer_in_use.3F

    limit = 1000
    truncated = False
    title_ = title
    title_ = re.sub(' ', '_', title_)
    # do not convert & into %26, title_ = re.sub('&', '%26', title_)
    params = {'title': 'Special:Export', 'pages': title_, 'action': 'submit'}
    if config['curonly']:
        params['curonly'] = 1
        params['limit'] = 1
    else:
        params['offset'] = '1'  # 1 always < 2000s
        params['limit'] = limit
    # in other case, do not set params['templates']
    if 'templates' in config and config['templates']:
        params['templates'] = 1

    xml = getXMLPageCore(params=params, config=config, session=session)

    # if complete history, check if this page history has > limit edits, if so, retrieve all using offset if available
    # else, warning about Special:Export truncating large page histories
    r_timestamp = r'<timestamp>([^<]+)</timestamp>'
    # search for timestamps in xml to avoid analysing empty pages like
    # Special:Allpages and the random one
    if not config['curonly'] and re.search(r_timestamp, xml):
        while not truncated and params['offset']:  # next chunk
            # get the last timestamp from the acum XML
            params['offset'] = re.findall(r_timestamp, xml)[-1]
            xml2 = getXMLPageCore(
                params=params, config=config, session=session)

            # are there more edits in this next XML chunk or no <page></page>?
            if re.findall(r_timestamp, xml2):
                if re.findall(r_timestamp, xml2)[-1] == params['offset']:
                    # again the same XML, this wiki does not support params in
                    # Special:Export, offer complete XML up to X edits (usually
                    # 1000)
                    print 'ATTENTION: This wiki does not allow some parameters in Special:Export, therefore pages with large histories may be truncated'
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
                    xml = xml.split(
                        '</page>')[0] + '    <revision>' + ('<revision>'.join(xml2.split('<revision>')[1:]))
            else:
                params['offset'] = ''  # no more edits in this page history

    if verbose:
        numberofedits = len(re.findall(r_timestamp, xml))
        if (numberofedits == 1):
            print '    %s, 1 edit' % (title.encode('utf-8'))
        else:
            print '    %s, %d edits' % (title.encode('utf-8'), numberofedits)

    return xml


def cleanXML(xml=''):
    """ Trim redundant info """
    # do not touch XML codification, leave AS IS
    if re.search(r'</siteinfo>\n', xml) and re.search(r'</mediawiki>', xml):
        xml = xml.split('</siteinfo>\n')[1]
        xml = xml.split('</mediawiki>')[0]
    return xml


def generateXMLDump(config={}, titles=[], start='', session=None):
    """ Generates a XML dump for a list of titles """

    print 'Retrieving the XML for every page from "%s"' % (start and start or 'start')
    header = getXMLHeader(config=config, session=session)
    footer = '</mediawiki>\n'  # new line at the end
    xmlfilename = '%s-%s-%s.xml' % (domain2prefix(config=config),
                                    config['date'], config['curonly'] and 'current' or 'history')
    xmlfile = ''
    lock = True
    if start:
        # remove the last chunk of xml dump (it is probably incomplete)
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'r')
        xmlfile2 = open('%s/%s2' % (config['path'], xmlfilename), 'w')
        prev = ''
        c = 0
        for l in xmlfile:
            # removing <page>\n until end of file
            # lock to avoid write an empty line at the begining of file
            if c != 0:
                if not re.search(r'<title>%s</title>' % (start), l):
                    xmlfile2.write(prev)
                else:
                    break
            c += 1
            prev = l
        xmlfile.close()
        xmlfile2.close()
        # subst xml with xml2
        # remove previous xml dump
        os.remove('%s/%s' % (config['path'], xmlfilename))
        # move correctly truncated dump to its real name
        os.rename(
            '%s/%s2' % (config['path'], xmlfilename), '%s/%s' % (config['path'], xmlfilename))
    else:
        # requested complete xml dump
        lock = False
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'w')
        xmlfile.write(header.encode('utf-8'))
        xmlfile.close()

    xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'a')
    c = 1
    for title in titles:
        if not title.strip():
            continue
        if title == start:  # start downloading from start, included
            lock = False
        if lock:
            continue
        delay(config=config, session=session)
        if c % 10 == 0:
            print 'Downloaded %d pages' % (c)
        xml = getXMLPage(config=config, title=title, session=session)
        xml = cleanXML(xml=xml)
        if not xml:
            logerror(
                config=config, text=u'The page "%s" was missing in the wiki (probably deleted)' % (title))
        # here, XML is a correct <page> </page> chunk or
        # an empty string due to a deleted page (logged in errors log) or
        # an empty string due to an error while retrieving the page from server
        # (logged in errors log)
        xmlfile.write(xml.encode('utf-8'))
        c += 1
    xmlfile.write(footer)
    xmlfile.close()
    print 'XML dump saved at...', xmlfilename


def saveTitles(config={}, titles=[]):
    """ Save title list in a file """

    titlesfilename = '%s-%s-titles.txt' % (
        domain2prefix(config=config), config['date'])
    titlesfile = open('%s/%s' % (config['path'], titlesfilename), 'w')
    output = u"%s\n--END--" % ('\n'.join(titles))
    titlesfile.write(output.encode('utf-8'))
    titlesfile.close()

    print 'Titles saved at...', titlesfilename


def saveImageNames(config={}, images=[], session=None):
    """ Save image list in a file, including filename, url and uploader """

    imagesfilename = '%s-%s-images.txt' % (
        domain2prefix(config=config), config['date'])
    imagesfile = open('%s/%s' % (config['path'], imagesfilename), 'w')
    imagesfile.write(('\n'.join(['%s\t%s\t%s' % (
        filename, url, uploader) for filename, url, uploader in images]).encode('utf-8')))
    imagesfile.write('\n--END--')
    imagesfile.close()

    print 'Image filenames and URLs saved at...', imagesfilename


def curateImageURL(config={}, url=''):
    """ Returns an absolute URL for an image, adding the domain if missing """
    
    if 'index' in config and config['index']:
        #remove from :// (http or https) until the first / after domain
        domainalone = config['index'].split('://')[0] + '://' + config['index'].split('://')[1].split('/')[0]
    elif 'api' in config and config['api']:
        domainalone = config['api'].split('://')[0] + '://' + config['api'].split('://')[1].split('/')[0]
    else:
        print 'ERROR: no index nor API'
        sys.exit()
        
    if url.startswith('//'): # Orain wikifarm returns URLs starting with //
        url = u'%s:%s' % (domainalone.split('://')[0], url)
    elif url[0] == '/' or (not url.startswith('http://') and not url.startswith('https://')): #is it a relative URL?
        if url[0] == '/': #slash is added later
            url = url[1:]
        url = u'%s/%s' % (domainalone, url) # concat http(s) + domain + relative url
    url = undoHTMLEntities(text=url)
    #url = urllib.unquote(url) #do not use unquote with url, it break some urls with odd chars
    url = re.sub(' ', '_', url)
    
    return url


def getImageNamesScraper(config={}, session=None):
    """ Retrieve file list: filename, url, uploader """

    # (?<! http://docs.python.org/library/re.html
    r_next = r'(?<!&amp;dir=prev)&amp;offset=(?P<offset>\d+)&amp;'
    images = []
    offset = '29990101000000'  # january 1, 2999
    limit = 5000
    retries = 5
    while offset:
        # 5000 overload some servers, but it is needed for sites like this with
        # no next links
        # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
        r = session.post(url=config['index'], data={
                         'title': 'Special:Imagelist', 'limit': limit, 'offset': offset})
        raw = r.text
        delay(config=config, session=session)
        # delicate wiki
        if re.search(ur'(?i)(allowed memory size of \d+ bytes exhausted|Call to a member function getURL)', raw):
            if limit > 10:
                print 'Error: listing %d images in a chunk is not possible, trying tiny chunks' % (limit)
                limit = limit / 10
                continue
            elif retries > 0:  # waste retries, then exit
                retries -= 1
                print 'Retrying...'
                continue
            else:
                print 'No more retries, exit...'
                break

        raw = cleanHTML(raw)
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
        r_images5 = (r'(?im)<td class="TablePager_col_img_name">\s*<a href[^>]*?>(?P<filename>[^>]+)</a>\s*\(<a href="(?P<url>[^>]+)">[^<]*?</a>\s*\)\s*</td>\s*'
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
            url = curateImageURL(config=config, url=url)
            filename = re.sub('_', ' ', i.group('filename'))
            filename = undoHTMLEntities(text=filename)
            filename = urllib.unquote(filename)
            uploader = re.sub('_', ' ', i.group('uploader'))
            uploader = undoHTMLEntities(text=uploader)
            uploader = urllib.unquote(uploader)
            images.append([filename, url, uploader])
            # print filename, url

        if re.search(r_next, raw):
            offset = re.findall(r_next, raw)[0]
            retries += 5  # add more retries if we got a page with offset
        else:
            offset = ''

    if (len(images) == 1):
        print '    Found 1 image'
    else:
        print '    Found %d images' % (len(images))

    images.sort()
    return images


def getImageNamesAPI(config={}, session=None):
    """ Retrieve file list: filename, url, uploader """
    oldAPI = False
    aifrom = '!'
    images = []
    while aifrom:
        sys.stderr.write('.')  # progress
        params = {'action': 'query', 'list': 'allimages', 'aiprop':
                  'url|user', 'aifrom': aifrom, 'format': 'json', 'ailimit': 500}
        # FIXME Handle HTTP Errors HERE
        r = session.post(url=config['api'], data=params)
        handleStatusCode(r)
        jsonimages = json.loads(r.text)
        delay(config=config, session=session)
        
        if 'query' in jsonimages:
            aifrom = ''
            if jsonimages.has_key('query-continue') and jsonimages['query-continue'].has_key('allimages'):
                if jsonimages['query-continue']['allimages'].has_key('aicontinue'):
                    aifrom = jsonimages['query-continue']['allimages']['aicontinue'] 
                elif jsonimages['query-continue']['allimages'].has_key('aifrom'):
                    aifrom = jsonimages['query-continue']['allimages']['aifrom']
            #print aifrom
            
            for image in jsonimages['query']['allimages']:
                url = image['url']
                url = curateImageURL(config=config, url=url)
                # encoding to ascii is needed to work around this horrible bug: http://bugs.python.org/issue8136
                filename = unicode(urllib.unquote((re.sub('_', ' ', url.split('/')[-1])).encode('ascii','ignore')), 'utf-8')
                uploader = re.sub('_', ' ', image['user'])
                images.append([filename, url, uploader])
        else:
            oldAPI = True
            break
    
    if oldAPI:
        gapfrom = '!'
        images = []
        while gapfrom:
            sys.stderr.write('.') #progress
            # Some old APIs doesn't have allimages query
            # In this case use allpages (in nm=6) as generator for imageinfo
            # Example: http://minlingo.wiki-site.com/api.php?action=query&generator=allpages&gapnamespace=6 &gaplimit=500&prop=imageinfo&iiprop=user|url&gapfrom=!
            params = {'action': 'query', 'generator': 'allpages', 'gapnamespace': 6, 'gaplimit': 500, 'gapfrom': gapfrom, 'prop': 'imageinfo', 'iiprop': 'user|url', 'format': 'json'}
            #FIXME Handle HTTP Errors HERE
            r = session.post(url=config['api'], data=params)
            handleStatusCode(r)
            jsonimages = json.loads(r.text)
            delay(config=config, session=session)
            
            if 'query' in jsonimages:
                gapfrom = ''
                if jsonimages.has_key('query-continue') and jsonimages['query-continue'].has_key('allpages'):
                    if jsonimages['query-continue']['allpages'].has_key('gapfrom'):
                        gapfrom = jsonimages['query-continue']['allpages']['gapfrom'] 
                #print gapfrom
                #print jsonimages['query']
                
                for image, props in jsonimages['query']['pages'].items():
                    url = props['imageinfo'][0]['url']
                    url = curateImageURL(config=config, url=url)
                    filename = re.sub('_', ' ', ':'.join(props['title'].split(':')[1:]))
                    uploader = re.sub('_', ' ', props['imageinfo'][0]['user'])
                    images.append([filename, url, uploader])

    if (len(images) == 1):
        print '    Found 1 image'
    else:
        print '    Found %d images' % (len(images))

    return images


def undoHTMLEntities(text=''):
    """ Undo some HTML codes """

    # i guess only < > & " ' need conversion
    # http://www.w3schools.com/html/html_entities.asp
    text = re.sub('&lt;', '<', text)
    text = re.sub('&gt;', '>', text)
    text = re.sub('&amp;', '&', text)
    text = re.sub('&quot;', '"', text)
    text = re.sub('&#039;', '\'', text)

    return text


def generateImageDump(config={}, other={}, images=[], start='', session=None):
    """ Save files and descriptions using a file list """

    # fix use subdirectories md5
    print 'Retrieving images from "%s"' % (start and start or 'start')
    imagepath = '%s/images' % (config['path'])
    if not os.path.isdir(imagepath):
        print 'Creating "%s" directory' % (imagepath)
        os.makedirs(imagepath)

    c = 0
    lock = True
    if not start:
        lock = False
    for filename, url, uploader in images:
        if filename == start:  # start downloading from start (included)
            lock = False
        if lock:
            continue
        delay(config=config, session=session)

        # saving file
        # truncate filename if length > 100 (100 + 32 (md5) = 132 < 143 (crash
        # limit). Later .desc is added to filename, so better 100 as max)
        filename2 = urllib.unquote(filename)
        if len(filename2) > other['filenamelimit']:
            # split last . (extension) and then merge
            filename2 = truncateFilename(other=other, filename=filename2)
            print 'Filename is too long, truncating. Now it is:', filename2
        filename3 = u'%s/%s' % (imagepath, filename2)
        imagefile = open(filename3, 'wb')
        r = requests.get(url=url)
        imagefile.write(r.content)
        imagefile.close()
        # saving description if any
        xmlfiledesc = getXMLFileDesc(config=config, title=u'Image:%s' % (
            filename), session=session)  # use Image: for backwards compatibility
        f = open('%s/%s.desc' % (imagepath, filename2), 'w')
        # <text xml:space="preserve" bytes="36">Banner featuring SG1, SGA, SGU teams</text>
        if not re.search(r'</mediawiki>', xmlfiledesc):
            # failure when retrieving desc? then save it as empty .desc
            xmlfiledesc = ''
        f.write(xmlfiledesc.encode('utf-8'))
        f.close()
        delay(config=config, session=session)
        c += 1
        if c % 10 == 0:
            print '    Downloaded %d images' % (c)

    print 'Downloaded %d images' % (c)


def saveLogs(config={}, session=None):
    """ Save Special:Log """
    # get all logs from Special:Log
    """parse
    <select name='type'>
    <option value="block">Bloqueos de usuarios</option>
    <option value="rights">Cambios de perfil de usuario</option>
    <option value="protect" selected="selected">Protecciones de páginas</option>
    <option value="delete">Registro de borrados</option>
    <option value="newusers">Registro de creación de usuarios</option>
    <option value="merge">Registro de fusiones</option>
    <option value="import">Registro de importaciones</option>
    <option value="patrol">Registro de revisiones</option>
    <option value="move">Registro de traslados</option>
    <option value="upload">Subidas de archivos</option>
    <option value="">Todos los registros</option>
    </select>
    """
    delay(config=config, session=session)


def domain2prefix(config={}, session=None):
    """ Convert domain name to a valid prefix filename. """

    # At this point, both api and index are supposed to be defined
    domain = ''
    if config['api']:
        domain = config['api']
    elif config['index']:
        domain = config['index']

    domain = domain.lower()
    domain = re.sub(r'(https?://|www\.|/index\.php|/api\.php)', '', domain)
    domain = re.sub(r'/', '_', domain)
    domain = re.sub(r'\.', '', domain)
    domain = re.sub(r'[^A-Za-z0-9]', '_', domain)

    return domain


def loadConfig(config={}, configfilename=''):
    """ Load config file """

    try:
        with open('%s/%s' % (config['path'], configfilename), 'r') as infile:
            config = cPickle.load(infile)
    except:
        print 'There is no config file. we can\'t resume. Start a new dump.'
        sys.exit()

    return config


def saveConfig(config={}, configfilename=''):
    """ Save config file """

    with open('%s/%s' % (config['path'], configfilename), 'w') as outfile:
        cPickle.dump(config, outfile)


def welcome():
    message = ''
    """ Opening message """
    message += "#" * 73
    message += """
# Welcome to DumpGenerator %s by WikiTeam (GPL v3)                   #
# More info at: https://github.com/WikiTeam/wikiteam                    #""" % (getVersion())
    message += "\n"
    message += "#" * 73
    message += "\n"
    message += ''
    message += "\n"
    message += "#" * 73
    message += """
# Copyright (C) 2011-2014 WikiTeam                                      #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #"""
    message += "\n"
    message += "#" * 73
    message += "\n"
    message += ''

    return message


def bye():
    """ Closing message """
    print "---> Congratulations! Your dump is complete <---"
    print "If you found any bug, report a new issue here: https://github.com/WikiTeam/wikiteam/issues"
    print "If this is a public wiki, please, consider publishing this dump. Do it yourself as explained in https://github.com/WikiTeam/wikiteam/wiki/Tutorial#Publishing_the_dump or contact us at https://github.com/WikiTeam/wikiteam"
    print "Good luck! Bye!"


def getParameters(params=[]):
    if not params:
        params = sys.argv

    parser = argparse.ArgumentParser(description='')
    
    # General params
    parser.add_argument(
        '-v', '--version', action='version', version=getVersion())
    parser.add_argument(
        '--cookies', metavar="cookies.txt", help="path to a cookies.txt file")
    parser.add_argument(
        '--delay', metavar=5, default=0, type=float, help="adds a delay (in seconds)")
    parser.add_argument(
        '--retries', metavar=5, default=5, help="Maximum number of retries for ")
    parser.add_argument('--path', help='path to store wiki dump at')
    parser.add_argument('--resume', action='store_true',
                        help='resumes previous incomplete dump (requires --path)')
    parser.add_argument('--force', action='store_true', help='')
    parser.add_argument(
        '--user', help='Username if authentication is required.')
    parser.add_argument(
        '--pass', dest='password', help='Password if authentication is required.')

    # URL params
    groupWikiOrAPIOrIndex = parser.add_argument_group()
    groupWikiOrAPIOrIndex.add_argument(
        'wiki', default='', nargs='?', help="URL to wiki (e.g. http://wiki.domain.org)")
    groupWikiOrAPIOrIndex.add_argument('--api', help="URL to API (e.g. http://wiki.domain.org/w/api.php)")
    groupWikiOrAPIOrIndex.add_argument('--index', help="URL to index.php (e.g. http://wiki.domain.org/w/index.php)")
    
    # Download params
    groupDownload = parser.add_argument_group('Data to download', 'What info download from the wiki')
    groupDownload.add_argument(
        '--xml', action='store_true', help="generates a full history XML dump (--xml --curonly for current revisions only)")
    groupDownload.add_argument('--curonly', action='store_true',
                        help='store only the current version of pages')
    groupDownload.add_argument(
        '--images', action='store_true', help="generates an image dump")
    groupDownload.add_argument('--namespaces', metavar="1,2,3",
                        help='comma-separated value of namespaces to include (all by default)')
    groupDownload.add_argument('--exnamespaces', metavar="1,2,3",
                        help='comma-separated value of namespaces to exclude')
    
    # Meta info params
    groupMeta = parser.add_argument_group('Meta info', 'What meta info to retrieve from the wiki')
    groupMeta.add_argument(
        '--get-wiki-engine', action='store_true', help="returns the wiki engine")
    
    args = parser.parse_args()
    # print args
    
    # Don't mix download params and meta info params
    if (args.xml or args.images) and \
        (args.get_wiki_engine):
        print 'ERROR: Don\'t mix download params and meta info params'
        parser.print_help()
        sys.exit(1)
    
    # No download params and no meta info params? Exit
    if (not args.xml and not args.images) and \
        (not args.get_wiki_engine):
        print 'ERROR: Use at least one download param or meta info param'
        parser.print_help()
        sys.exit(1)
    
    # Execute meta info params
    if args.wiki:
        if args.get_wiki_engine:
            print getWikiEngine(url=args.wiki)
            sys.exit()
    
    # Create session
    cj = cookielib.MozillaCookieJar()
    if args.cookies:
        cj.load(args.cookies)
        print 'Using cookies from %s' % args.cookies

    session = requests.Session()
    session.cookies = cj
    session.headers = {'User-Agent': getUserAgent()}
    if args.user and args.password:
        session.auth = (args.user, args.password)
    # session.mount(args.api.split('/api.php')[0], HTTPAdapter(max_retries=max_ret))
    
    # check URLs
    for url in [args.api, args.index, args.wiki]:
        if url and (not url.startswith('http://') and not url.startswith('https://')):
            print url
            print 'ERROR: URLs must start with http:// or https://\n'
            parser.print_help()
            sys.exit(1)
    
    # Get API and index and verify
    api = args.api and args.api or ''
    index = args.index and args.index or ''
    if api == '' or index == '':
        if args.wiki:
            if getWikiEngine(args.wiki) == 'MediaWiki':
                api2, index2 = mwGetAPIAndIndex(args.wiki)
                if not api:
                    api = api2
                if not index:
                    index = index2
            else:
                print 'ERROR: Unsupported wiki. Wiki engines supported are: MediaWiki'
                sys.exit(1)
        else:
            if api == '':
                pass
            elif index == '':
                index = '/'.join(api.split('/')[:-1]) + '/index.php'
    
    #print api
    #print index
    if api and checkAPI(api=api, session=session):
        print 'API is OK'
    else:
        print 'Error in API, please, provide a correct path to API'
        sys.exit(1)
    
    if index and checkIndex(index=index, cookies=args.cookies, session=session):
        print 'index.php is OK'
    else:
        print 'Error in index.php, please, provide a correct path to index.php'
        sys.exit(1)
    
    # check user and pass (one requires both)
    if (args.user and not args.password) or (args.password and not args.user):
        print 'ERROR: Both --user and --pass are required for authentication.'
        parser.print_help()
        sys.exit(1)

    namespaces = ['all']
    exnamespaces = []
    # Process namespace inclusions
    if args.namespaces:
        # fix, why - ?  and... --namespaces= all with a space works?
        if re.search(r'[^\d, \-]', args.namespaces) and args.namespaces.lower() != 'all':
            print "Invalid namespace values.\nValid format is integer(s) separated by commas"
            sys.exit()
        else:
            ns = re.sub(' ', '', args.namespaces)
            if ns.lower() == 'all':
                namespaces = ['all']
            else:
                namespaces = [int(i) for i in ns.split(',')]

    # Process namespace exclusions
    if args.exnamespaces:
        if re.search(r'[^\d, \-]', args.exnamespaces):
            print "Invalid namespace values.\nValid format is integer(s) separated by commas"
            sys.exit(1)
        else:
            ns = re.sub(' ', '', args.exnamespaces)
            if ns.lower() == 'all':
                print 'You cannot exclude all namespaces.'
                sys.exit(1)
            else:
                exnamespaces = [int(i) for i in ns.split(',')]

    # --curonly requires --xml
    if args.curonly and not args.xml:
        print "--curonly requires --xml\n"
        parser.print_help()
        sys.exit(1)

    config = {
        'curonly': args.curonly,
        'date': datetime.datetime.now().strftime('%Y%m%d'),
        'api': api,
        'index': index,
        'images': args.images,
        'logs': False,
        'xml': args.xml,
        'namespaces': namespaces,
        'exnamespaces': exnamespaces,
        'path': args.path or '',
        'cookies': args.cookies or '',
        'delay': args.delay
    }
    other = {
        'resume': args.resume,
        'filenamelimit': 100,  # do not change
        'force': args.force,
        'session': session
    }

    # calculating path, if not defined by user with --path=
    if not config['path']:
        config['path'] = './%s-%s-wikidump' % (domain2prefix(config=config, session=session), config['date'])

    return config, other


def checkAPI(api=None, session=None):
    """ Checking API availability """
    global cj
    r = session.post(
        url=api, data={'action': 'query', 'meta': 'siteinfo', 'format': 'json'})
    resultText = r.text
    print 'Checking API...', api
    if "MediaWiki API is not enabled for this site." in resultText:
        return False
    try:
        result = json.loads(resultText)
        if 'query' in result:
            return True
    except ValueError:
            return False
    return False


def checkIndex(index=None, cookies=None, session=None):
    """ Checking index.php availability """
    r = session.post(url=index, data={'title': 'Special:Version'})
    raw = r.text
    print 'Checking index.php...', index
    # Workaround for issue 71
    if re.search(r'(Special:Badtitle</a>|class="permissions-errors"|"wgCanonicalSpecialPageName":"Badtitle"|Login Required</h1>)', raw) and not cookies:
        print "ERROR: This wiki requires login and we are not authenticated"
        return False
    if re.search(r'(This wiki is powered by|<h2 id="mw-version-license">|meta name="generator" content="MediaWiki)', raw):
        return True
    return False


def removeIP(raw=''):
    """ Remove IP from HTML comments <!-- --> """

    raw = re.sub(r'\d+\.\d+\.\d+\.\d+', '0.0.0.0', raw)
    # http://www.juniper.net/techpubs/software/erx/erx50x/swconfig-routing-vol1/html/ipv6-config5.html
    # weird cases as :: are not included
    raw = re.sub(
        r'(?i)[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}', '0:0:0:0:0:0:0:0', raw)

    return raw


def checkXMLIntegrity(config={}, titles=[], session=None):
    """ Check XML dump integrity, to detect broken XML chunks """
    return

    print 'Verifying dump...'
    checktitles = 0
    checkpageopen = 0
    checkpageclose = 0
    checkrevisionopen = 0
    checkrevisionclose = 0
    for line in file('%s/%s-%s-%s.xml' % (config['path'], domain2prefix(config=config, session=session), config['date'], config['curonly'] and 'current' or 'history'), 'r').read().splitlines():
        if "<revision>" in line:
            checkrevisionopen += 1
        elif "</revision>" in line:
            checkrevisionclose += 1
        elif "<page>" in line:
            checkpageopen += 1
        elif "</page>" in line:
            checkpageclose += 1
        elif "<title>" in line:
            checktitles += 1
        else:
            continue
    if (checktitles == checkpageopen and checktitles == checkpageclose and checkrevisionopen == checkrevisionclose):
        pass
    else:
        print 'XML dump seems to be corrupted.'
        reply = ''
        while reply.lower() not in ['yes', 'y', 'no', 'n']:
            reply = raw_input('Regenerate a new dump ([yes, y], [no, n])? ')
        if reply.lower() in ['yes', 'y']:
            generateXMLDump(config=config, titles=titles, session=session)
        elif reply.lower() in ['no', 'n']:
            print 'Not generating a new dump.'


def createNewDump(config={}, other={}):
    titles = []
    images = []
    print 'Trying generating a new dump into a new directory...'
    if config['xml']:
        titles += getPageTitles(config=config, session=other['session'])
        saveTitles(config=config, titles=titles)
        generateXMLDump(config=config, titles=titles, session=other['session'])
        checkXMLIntegrity(config=config, titles=titles, session=other['session'])
    if config['images']:
        images += getImageNames(config=config, session=other['session'])
        saveImageNames(config=config, images=images, session=other['session'])
        generateImageDump(config=config, other=other, images=images, session=other['session'])
    if config['logs']:
        saveLogs(config=config, session=other['session'])


def resumePreviousDump(config={}, other={}):
    titles = []
    images = []
    print 'Resuming previous dump process...'
    if config['xml']:
        # load titles
        lasttitle = ''
        try:
            f = open('%s/%s-%s-titles.txt' % (config['path'], domain2prefix(
                config=config, session=other['session']), config['date']), 'r')
            raw = unicode(f.read(), 'utf-8')
            titles = raw.split('\n')
            lasttitle = titles[-1]
            if not lasttitle:  # empty line at EOF ?
                lasttitle = titles[-2]
            f.close()
        except:
            pass  # probably file doesnot exists
        if lasttitle == '--END--':
            # titles list is complete
            print 'Title list was completed in the previous session'
        else:
            print 'Title list is incomplete. Reloading...'
            # do not resume, reload, to avoid inconsistences, deleted pages or
            # so
            titles = getPageTitles(config=config, session=other['session'])
            saveTitles(config=config, titles=titles)
        # checking xml dump
        xmliscomplete = False
        lastxmltitle = ''
        try:
            f = open('%s/%s-%s-%s.xml' % (config['path'], domain2prefix(config=config, session=other[
                     'session']), config['date'], config['curonly'] and 'current' or 'history'), 'r')
            for l in f:
                if re.findall('</mediawiki>', l):
                    # xml dump is complete
                    xmliscomplete = True
                    break
                # weird if found more than 1, but maybe
                xmltitles = re.findall(r'<title>([^<]+)</title>', l)
                if xmltitles:
                    lastxmltitle = undoHTMLEntities(text=xmltitles[-1])
            f.close()
        except:
            pass  # probably file doesnot exists
        # removing --END-- before getXMLs
        while titles and titles[-1] in ['', '--END--']:
            titles = titles[:-1]
        if xmliscomplete:
            print 'XML dump was completed in the previous session'
        elif lastxmltitle:
            # resuming...
            print 'Resuming XML dump from "%s"' % (lastxmltitle)
            generateXMLDump(
                config=config, titles=titles, start=lastxmltitle, session=other['session'])
        else:
            # corrupt? only has XML header?
            print 'XML is corrupt? Regenerating...'
            generateXMLDump(
                config=config, titles=titles, session=other['session'])

    if config['images']:
        # load images
        lastimage = ''
        try:
            f = open('%s/%s-%s-images.txt' %
                     (config['path'], domain2prefix(config=config), config['date']), 'r')
            raw = unicode(f.read(), 'utf-8').strip()
            lines = raw.split('\n')
            for l in lines:
                if re.search(r'\t', l):
                    images.append(l.split('\t'))
            lastimage = lines[-1]
            f.close()
        except:
            pass  # probably file doesnot exists
        if lastimage == u'--END--':
            print 'Image list was completed in the previous session'
        else:
            print 'Image list is incomplete. Reloading...'
            # do not resume, reload, to avoid inconsistences, deleted images or
            # so
            images = getImageNames(config=config, session=other['session'])
            saveImageNames(config=config, images=images)
        # checking images directory
        listdir = []
        try:
            listdir = os.listdir('%s/images' % (config['path']))
        except:
            pass  # probably directory does not exist
        listdir.sort()
        complete = True
        lastfilename = ''
        lastfilename2 = ''
        c = 0
        for filename, url, uploader in images:
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
        print '%d images were found in the directory from a previous session' % (c)
        if complete:
            # image dump is complete
            print 'Image dump was completed in the previous session'
        else:
            # we resume from previous image, which may be corrupted (or missing
            # .desc)  by the previous session ctrl-c or abort
            generateImageDump(
                config=config, other=other, images=images, start=lastfilename2, session=other['session'])

    if config['logs']:
        # fix
        pass


def saveSpecialVersion(config={}, session=None):
    """ Save Special:Version as .html, to preserve extensions details """

    if os.path.exists('%s/Special:Version.html' % (config['path'])):
        print 'Special:Version.html exists, do not overwrite'
    else:
        print 'Downloading Special:Version with extensions and other related info'
        r = session.post(
            url=config['index'], data={'title': 'Special:Version'})
        raw = r.text
        delay(config=config, session=session)
        raw = removeIP(raw=raw)
        with open('%s/Special:Version.html' % (config['path']), 'w') as outfile:
            outfile.write(raw.encode('utf-8'))


def saveIndexPHP(config={}, session=None):
    """ Save index.php as .html, to preserve license details available at the botom of the page """

    if os.path.exists('%s/index.html' % (config['path'])):
        print 'index.html exists, do not overwrite'
    else:
        print 'Downloading index.php (Main Page) as index.html'
        r = session.post(url=config['index'], data={})
        raw = r.text
        delay(config=config, session=session)
        raw = removeIP(raw=raw)
        with open('%s/index.html' % (config['path']), 'w') as outfile:
            outfile.write(raw.encode('utf-8'))


def saveSiteInfo(config={}, session=None):
    """ Save a file with site info """

    if config['api']:
        if os.path.exists('%s/siteinfo.json' % (config['path'])):
            print 'siteinfo.json exists, do not overwrite'
        else:
            print 'Downloading site info as siteinfo.json'
            
            # MediaWiki 1.13+
            r = session.post(url=config['api'], data={
                             'action': 'query',
                             'meta': 'siteinfo',
                             'siprop': 'general|namespaces|statistics|dbrepllag|interwikimap|namespacealiases|specialpagealiases|usergroups|extensions|skins|magicwords|fileextensions|rightsinfo',
                             'sinumberingroup': 1,
                             'format': 'json'})
            # MediaWiki 1.11-1.12
            if not 'query' in json.loads(r.text):
                r = session.post(url=config['api'], data={
                                 'action': 'query',
                                 'meta': 'siteinfo',
                                 'siprop': 'general|namespaces|statistics|dbrepllag|interwikimap',
                                 'format': 'json'})
            # MediaWiki 1.8-1.10
            if not 'query' in json.loads(r.text):
                r = session.post(url=config['api'], data={
                                 'action': 'query', 'meta': 'siteinfo', 'siprop': 'general|namespaces', 'format': 'json'})
            result = json.loads(r.text)
            delay(config=config, session=session)
            with open('%s/siteinfo.json' % (config['path']), 'w') as outfile:
                outfile.write(json.dumps(result, indent=4, sort_keys=True))


def avoidWikimediaProjects(config={}, other={}):
    """ Skip Wikimedia projects and redirect to the dumps website """

    # notice about wikipedia dumps
    if re.findall(r'(?i)(wikipedia|wikisource|wiktionary|wikibooks|wikiversity|wikimedia|wikispecies|wikiquote|wikinews|wikidata|wikivoyage)\.org', config['api'] + config['index']):
        print 'PLEASE, DO NOT USE THIS SCRIPT TO DOWNLOAD WIKIMEDIA PROJECTS!'
        print 'Download the dumps from http://dumps.wikimedia.org'
        if not other['force']:
            print 'Thanks!'
            sys.exit()


def getWikiEngine(url=''):
    """ Returns the wiki engine of a URL, if known """

    session = requests.Session()
    session.headers = {'User-Agent': getUserAgent()}
    r = session.post(url=url)
    result = r.text

    wikiengine = 'Unknown'
    if re.search(ur'(?im)(<meta name="generator" content="DokuWiki)', result):
        wikiengine = 'DokuWiki'
    elif re.search(ur'(?im)(alt="Powered by MediaWiki"|<meta name="generator" content="MediaWiki)', result):
        wikiengine = 'MediaWiki'
    elif re.search(ur'(?im)(>MoinMoin Powered</a>)', result):
        wikiengine = 'MoinMoin'

    return wikiengine


def mwGetAPIAndIndex(url=''):
    """ Returns the MediaWiki API and Index.php """
    
    api = ''
    index = ''
    session = requests.Session()
    session.headers = {'User-Agent': getUserAgent()}
    r = session.post(url=url)
    result = r.text
    
    # API
    m = re.findall(ur'(?im)<\s*link\s*rel="EditURI"\s*type="application/rsd\+xml"\s*href="([^>]+?)\?action=rsd"\s*/\s*>', result)
    if m:
        api = m[0]
        if api.startswith('//'): # gentoo wiki
            api = url.split('//')[0] + api
    else:
        pass # build API using index and check it
    
    # Index.php
    m = re.findall(ur'<li id="ca-viewsource"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?', result)
    if m:
        index = m[0]
    else:
        m = re.findall(ur'<li id="ca-history"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?', result)
        if m:
            index = m[0]
    if index:
        if index.startswith('/'):
            index = '/'.join(api.split('/')[:-1]) + '/' + index.split('/')[-1]
    else:
        if api:
            if len(re.findall(ur'/index\.php5\?', result)) > len(re.findall(ur'/index\.php\?', result)):
                index = '/'.join(api.split('/')[:-1]) + '/index.php5'
            else:
                index = '/'.join(api.split('/')[:-1]) + '/index.php'
    
    return api, index
    

def main(params=[]):
    """ Main function """

    configfilename = 'config.txt'
    config, other = getParameters(params=params)
    avoidWikimediaProjects(config=config, other=other)

    print welcome()
    print 'Analysing %s' % (config['api'] and config['api'] or config['index'])

    # creating path or resuming if desired
    c = 2
    # to avoid concat blabla-2, blabla-2-3, and so on...
    originalpath = config['path']
    # do not enter if resume is requested from begining
    while not other['resume'] and os.path.isdir(config['path']):
        print '\nWarning!: "%s" path exists' % (config['path'])
        reply = ''
        while reply.lower() not in ['yes', 'y', 'no', 'n']:
            reply = raw_input('There is a dump in "%s", probably incomplete.\nIf you choose resume, to avoid conflicts, the parameters you have chosen in the current session will be ignored\nand the parameters available in "%s/%s" will be loaded.\nDo you want to resume ([yes, y], [no, n])? ' % (
                config['path'], config['path'], configfilename))
        if reply.lower() in ['yes', 'y']:
            if not os.path.isfile('%s/%s' % (config['path'], configfilename)):
                print 'No config file found. I can\'t resume. Aborting.'
                sys.exit()
            print 'You have selected: YES'
            other['resume'] = True
            break
        elif reply.lower() in ['no', 'n']:
            print 'You have selected: NO'
            other['resume'] = False
        config['path'] = '%s-%d' % (originalpath, c)
        print 'Trying to use path "%s"...' % (config['path'])
        c += 1

    if other['resume']:
        print 'Loading config file...'
        config = loadConfig(config=config, configfilename=configfilename)
    else:
        os.mkdir(config['path'])
        saveConfig(config=config, configfilename=configfilename)

    if other['resume']:
        resumePreviousDump(config=config, other=other)
    else:
        createNewDump(config=config, other=other)

    saveIndexPHP(config=config, session=other['session'])
    saveSpecialVersion(config=config, session=other['session'])
    saveSiteInfo(config=config, session=other['session'])
    bye()

if __name__ == "__main__":
    main()
