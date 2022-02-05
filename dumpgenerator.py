#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# dumpgenerator.py A generator of dumps for wikis
# Copyright (C) 2011-2018 WikiTeam developers
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
    from kitchen.text.converters import getwriter, to_unicode
except ImportError:
    print "Please install the kitchen module."
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
import subprocess
try:
    import requests
except ImportError:
    print "Please install or update the Requests module."
    sys.exit(1)
try:
    import mwclient
except ImportError:
    print "Please install the mwclient module if you want to use --xmlrevisions."
try:
    from lxml import etree
    from lxml.builder import E
except ImportError:
    print "Please install the lxml module if you want to use --xmlrevisions."
import time
import urllib
try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

__VERSION__ = '0.4.0-alpha'  # major, minor, micro: semver.org

class PageMissingError(Exception):
    def __init__(self, title, xml):
        self.title = title
        self.xml = xml
    def __str__(self):
        return "page '%s' not found" % self.title

class ExportAbortedError(Exception):
    def __init__(self, index):
        self.index = index
    def __str__(self):
        return "Export from '%s' did not return anything." % self.index

def getVersion():
    return(__VERSION__)


def truncateFilename(other={}, filename=''):
    """ Truncate filenames when downloading images with large filenames """
    return filename[:other['filenamelimit']] + \
        md5(filename.encode('utf-8')).hexdigest() + '.' + filename.split('.')[-1]


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
        raw = raw.split('<article id="WikiaMainContent" class="WikiaMainContent">')[
            1].split('</article>')[0]
    elif re.search('<body class=', raw):
        raw = raw.split('<body class=')[1].split(
            '<div class="printfooter">')[0]
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
        print "Please use --user and --pass."
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
            url=config['index'], params={'title': 'Special:Allpages'}, timeout=30)
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
        r = session.get(
            url=config['api'],
            params={
                'action': 'query',
                'meta': 'siteinfo',
                'siprop': 'namespaces',
                'format': 'json'},
            timeout=30
        )
        result = getJSON(r)
        delay(config=config, session=session)
        try:
            nsquery = result['query']['namespaces']
        except KeyError:
            print "Error: could not get namespaces from the API request."
            print "HTTP %d" % r.status_code
            print r.text
            return None

        if 'all' in namespaces:
            namespaces = []
            for i in nsquery.keys():
                if int(i) < 0:  # -1: Special, -2: Media, excluding
                    continue
                namespaces.append(int(i))
                namespacenames[int(i)] = nsquery[i]['*']
        else:
            # check if those namespaces really exist in this wiki
            namespaces2 = []
            for i in nsquery.keys():
                bi = i
                i = int(i)
                if i < 0:  # -1: Special, -2: Media, excluding
                    continue
                if i in namespaces:
                    namespaces2.append(i)
                    namespacenames[i] = nsquery[bi]['*']
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
        apiurl = urlparse(config['api'])
        site = mwclient.Site(apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=apiurl.scheme)
        for page in site.allpages(namespace=namespace):
            title = page.name
            titles.append(title)
            c += 1
            yield title

        if len(titles) != len(set(titles)):
            print 'Probably a loop, switching to next namespace'
            titles = list(set(titles))

            delay(config=config, session=session)
        print '    %d titles retrieved in the namespace %d' % (c, namespace)

def getPageTitlesScraper(config={}, session=None):
    """ Scrape the list of page titles from Special:Allpages """
    titles = []
    namespaces, namespacenames = getNamespacesScraper(
        config=config, session=session)
    for namespace in namespaces:
        print '    Retrieving titles in the namespace', namespace
        url = '%s?title=Special:Allpages&namespace=%s' % (
            config['index'], namespace)
        r = session.get(url=url, timeout=30)
        raw = r.text
        raw = cleanHTML(raw)

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

        # Should be enought subpages on Special:Allpages
        deep = 50
        c = 0
        oldfr = ''
        checked_suballpages = []
        rawacum = raw
        while r_suballpages and re.search(r_suballpages, raw) and c < deep:
            # load sub-Allpages
            m = re.compile(r_suballpages).finditer(raw)
            for i in m:
                fr = i.group('from')
                currfr = fr

                if oldfr == currfr:
                    # We are looping, exit the loop
                    pass

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
                    delay(config=config, session=session)
                    r = session.get(url=url, timeout=10)
                    #print 'Fetching URL: ', url
                    raw = r.text
                    raw = cleanHTML(raw)
                    rawacum += raw  # merge it after removed junk
                    print '    Reading', name, len(raw), 'bytes', \
                        len(re.findall(r_suballpages, raw)), 'subpages', \
                        len(re.findall(r_title, raw)), 'pages'

                delay(config=config, session=session)
            oldfr = currfr
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
        try:
            titles = getPageTitlesAPI(config=config, session=session)
        except:
            print "Error: could not get page titles from the API"
            titles = getPageTitlesScraper(config=config, session=session)
    elif 'index' in config and config['index']:
        titles = getPageTitlesScraper(config=config, session=session)

    titlesfilename = '%s-%s-titles.txt' % (
        domain2prefix(config=config), config['date'])
    titlesfile = open('%s/%s' % (config['path'], titlesfilename), 'wt')
    c = 0
    for title in titles:
        titlesfile.write(title.encode('utf-8') + "\n")
        c += 1
    # TODO: Sort to remove dupes? In CZ, Widget:AddThis appears two times:
    # main namespace and widget namespace.
    # We can use sort -u in UNIX, but is it worth it?
    titlesfile.write(u'--END--\n')
    titlesfile.close()
    print 'Titles saved at...', titlesfilename

    print '%d page titles loaded' % (c)
    return titlesfilename

def getImageNames(config={}, session=None):
    """ Get list of image names """

    print 'Retrieving image filenames'
    images = []
    if 'api' in config and config['api']:
        images = getImageNamesAPI(config=config, session=session)
    elif 'index' in config and config['index']:
        images = getImageNamesScraper(config=config, session=session)

    # images = list(set(images)) # it is a list of lists
    images.sort()

    print '%d image names loaded' % (len(images))
    return images


def getXMLHeader(config={}, session=None):
    """ Retrieve a random page to extract XML headers (namespace info, etc) """
    # get the header of a random page, to attach it in the complete XML backup
    # similar to: <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/"
    # xmlns:x....
    randomtitle = 'Main_Page'  # previously AMF5LKE43MNFGHKSDMRTJ
    print config['api']
    xml = ''
    if config['xmlrevisions'] and config['api'] and config['api'].endswith("api.php"):
        try:
            print 'Getting the XML header from the API'
            # Export and exportnowrap exist from MediaWiki 1.15, allpages from 1.18
            r = requests.get(config['api'] + '?action=query&export=1&exportnowrap=1&list=allpages&aplimit=1', timeout=10)
            xml = r.text
            # Otherwise try without exportnowrap, e.g. Wikia returns a blank page on 1.19
            if not re.match(r"\s*<mediawiki", xml):
                r = requests.get(config['api'] + '?action=query&export=1&list=allpages&aplimit=1&format=json', timeout=10)
                try:
                    xml = r.json()['query']['export']['*']
                except KeyError:
                    pass
            if not re.match(r"\s*<mediawiki", xml):
                # Do without a generator, use our usual trick of a random page title
                r = requests.get(config['api'] + '?action=query&export=1&exportnowrap=1&titles=' + randomtitle, timeout=10)
                xml = r.text
            # Again try without exportnowrap
            if not re.match(r"\s*<mediawiki", xml):
                r = requests.get(config['api'] + '?action=query&export=1&format=json&titles=' + randomtitle, timeout=10)
                try:
                    xml = r.json()['query']['export']['*']
                except KeyError:
                    pass
        except requests.exceptions.RetryError:
            pass

    else:
        try:
            xml = "".join([x for x in getXMLPage(config=config, title=randomtitle, verbose=False, session=session)])
        except PageMissingError as pme:
            # The <page> does not exist. Not a problem, if we get the <siteinfo>.
            xml = pme.xml
        # Issue 26: Account for missing "Special" namespace.
        # Hope the canonical special name has not been removed.
        # http://albens73.fr/wiki/api.php?action=query&meta=siteinfo&siprop=namespacealiases
        except ExportAbortedError:
            try:
                if config['api']:
                    print "Trying the local name for the Special namespace instead"
                    r = session.get(
                    url=config['api'],
                    params={
                        'action': 'query',
                        'meta': 'siteinfo',
                        'siprop': 'namespaces',
                        'format': 'json'},
                    timeout=120
                    )
                    config['export'] = json.loads(r.text)['query']['namespaces']['-1']['*'] \
                        + ':Export'
                    xml = "".join([x for x in getXMLPage(config=config, title=randomtitle, verbose=False, session=session)])
            except PageMissingError as pme:
                xml = pme.xml
            except ExportAbortedError:
                pass

    header = xml.split('</mediawiki>')[0]
    if not re.match(r"\s*<mediawiki", xml):
        if config['xmlrevisions']:
            # Try again the old way
            print 'Export test via the API failed. Wiki too old? Trying without xmlrevisions.'
            config['xmlrevisions'] = False
            header, config = getXMLHeader(config=config, session=session)
        else:
            print 'XML export on this wiki is broken, quitting.'
            logerror(u'XML export on this wiki is broken, quitting.')
            sys.exit()
    return header, config


def getXMLFileDesc(config={}, title='', session=None):
    """ Get XML for image description page """
    config['curonly'] = 1  # tricky to get only the most recent desc
    return("".join([x for x in getXMLPage( config=config, title=title, verbose=False, session=session)]))


def getUserAgent():
    """ Return a cool user-agent to hide Python user-agent """
    useragents = [
        # firefox
        #'Mozilla/5.0 (X11; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
        #'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
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
    maxretries = config['retries']  # x retries and skip
    increment = 20  # increment every retry

    while not re.search(r'</mediawiki>', xml):
        if c > 0 and c < maxretries:
            wait = increment * c < maxseconds and increment * \
                c or maxseconds  # incremental until maxseconds
            print '    In attempt %d, XML for "%s" is wrong. Waiting %d seconds and reloading...' %(c, params['pages'], wait)
            time.sleep(wait)
            # reducing server load requesting smallest chunks (if curonly then
            # limit = 1 from mother function)
            if params['limit'] > 1:
                params['limit'] = params['limit'] / 2  # half
        if c >= maxretries:
            print '    We have retried %d times' % (c)
            print '    MediaWiki error for "%s", network error or whatever...' % (params['pages'])
            if config['failfast']:
                print "Exit, it will be for another time"
                sys.exit()
            # If it's not already what we tried: our last chance, preserve only the last revision...
            # config['curonly'] means that the whole dump is configured to save only the last,
            # params['curonly'] should mean that we've already tried this
            # fallback, because it's set by the following if and passed to
            # getXMLPageCore
            if not config['curonly'] and not 'curonly' in params:
                print '    Trying to save only the last revision for this page...'
                params['curonly'] = 1
                logerror(
                    config=config,
                    text=u'Error while retrieving the full history of "%s". Trying to save only the last revision for this page' %
                    (params['pages'])
                )
                return getXMLPageCore(
                    headers=headers,
                    params=params,
                    config=config,
                    session=session
                )
            else:
                print '    Saving in the errors log, and skipping...'
                logerror(
                    config=config,
                    text=u'Error while retrieving the last revision of "%s". Skipping.' %
                    (params['pages']))
                raise ExportAbortedError(config['index'])
                return ''  # empty xml
        # FIXME HANDLE HTTP Errors HERE
        try:
            r = session.post(url=config['index'], params=params, headers=headers, timeout=10)
            handleStatusCode(r)
            xml = fixBOM(r)
        except requests.exceptions.ConnectionError as e:
            print '    Connection error: %s'%(str(e[0]))
            xml = ''
        except requests.exceptions.ReadTimeout as e:
            print '    Read timeout: %s'%(str(e[0]))
            xml = ''       
        c += 1

    return xml


def getXMLPage(config={}, title='', verbose=True, session=None):
    """ Get the full history (or current only) of a page """

    # if server errors occurs while retrieving the full page history, it may return [oldest OK versions] + last version, excluding middle revisions, so it would be partially truncated
    # http://www.mediawiki.org/wiki/Manual_talk:Parameters_to_Special:Export#Parameters_no_longer_in_use.3F

    limit = 1000
    truncated = False
    title_ = title
    title_ = re.sub(' ', '_', title_)
    # do not convert & into %26, title_ = re.sub('&', '%26', title_)
    try:
        params = {'title': config['export'], 'pages': title_, 'action': 'submit'}
    except KeyError:
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
    if xml == "":
        raise ExportAbortedError(config['index'])
    if not "</page>" in xml:
        raise PageMissingError(params['title'], xml)
    else:
        # strip these sha1s sums which keep showing up in the export and
        # which are invalid for the XML schema (they only apply to
        # revisions)
        xml = re.sub(r'\n\s*<sha1>\w+</sha1>\s*\n', r'\n', xml)
        xml = re.sub(r'\n\s*<sha1/>\s*\n', r'\n', xml)

    yield xml.split("</page>")[0]

    # if complete history, check if this page history has > limit edits, if so, retrieve all using offset if available
    # else, warning about Special:Export truncating large page histories
    r_timestamp = r'<timestamp>([^<]+)</timestamp>'

    numberofedits = 0
    numberofedits += len(re.findall(r_timestamp, xml))

    # search for timestamps in xml to avoid analysing empty pages like
    # Special:Allpages and the random one
    if not config['curonly'] and re.search(r_timestamp, xml):
        while not truncated and params['offset']:  # next chunk
            # get the last timestamp from the acum XML
            params['offset'] = re.findall(r_timestamp, xml)[-1]
            try:
                xml2 = getXMLPageCore(
                    params=params, config=config, session=session)
            except MemoryError:
                print "The page's history exceeds our memory, halving limit."
                params['limit'] = params['limit'] / 2
                continue

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
                    try:
                        xml2 = xml2.split("</page>")[0]
                        yield '  <revision>' + ('<revision>'.join(xml2.split('<revision>')[1:]))
                    except MemoryError:
                        print "The page's history exceeds our memory, halving limit."
                        params['limit'] = params['limit'] / 2
                        continue
                    xml = xml2
                    numberofedits += len(re.findall(r_timestamp, xml))
            else:
                params['offset'] = ''  # no more edits in this page history
    yield "</page>\n"

    if verbose:
        if (numberofedits == 1):
           print '    %s, 1 edit' % (title.strip())
        else:
           print '    %s, %d edits' % (title.strip(), numberofedits)


def makeXmlPageFromRaw(xml):
    """ Discard the metadata around a <page> element in <mediawiki> string"""
    root = etree.XML(xml)
    find = etree.XPath("//*[local-name() = 'page']")
    # The tag will inherit the namespace, like:
    # <page xmlns="http://www.mediawiki.org/xml/export-0.10/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    # FIXME: pretty_print doesn't seem to work, only adds a newline
    return etree.tostring(find(root)[0], pretty_print=True)


def cleanXML(xml=''):
    """ Trim redundant info from the XML however it comes """
    # do not touch XML codification, leave AS IS
    if re.search(r'</siteinfo>\n', xml):
        xml = xml.split('</siteinfo>\n')[1]
    if re.search(r'</mediawiki>', xml):
        xml = xml.split('</mediawiki>')[0]
    return xml


def generateXMLDump(config={}, titles=[], start=None, session=None):
    """ Generates a XML dump for a list of titles or from revision IDs """
    # TODO: titles is now unused.

    header, config = getXMLHeader(config=config, session=session)
    footer = '</mediawiki>\n'  # new line at the end
    xmlfilename = '%s-%s-%s.xml' % (domain2prefix(config=config),
                                    config['date'],
                                    config['curonly'] and 'current' or 'history')
    xmlfile = ''
    lock = True

    if config['xmlrevisions']:
        if start:
            print("WARNING: will try to start the download from title: {}".format(start))
            xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'a')
        else:
            print 'Retrieving the XML for every page from the beginning'
            xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'w')
            xmlfile.write(header.encode('utf-8'))
        try:
            r_timestamp = r'<timestamp>([^<]+)</timestamp>'
            for xml in getXMLRevisions(config=config, session=session, start=start):
                numrevs = len(re.findall(r_timestamp, xml))
                # Due to how generators work, it's expected this may be less
                # TODO: get the page title and reuse the usual format "X title, y edits"
                print "        %d more revisions exported" % numrevs
                xml = cleanXML(xml=xml)
                xmlfile.write(xml.encode('utf-8'))
        except AttributeError as e:
            print(e)
            print "This API library version is not working"
            sys.exit()
    else:
        print 'Retrieving the XML for every page from "%s"' % (start and start or 'start')
        if start:
            print "Removing the last chunk of past XML dump: it is probably incomplete."
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
            if not title:
                continue
            if title == start:  # start downloading from start, included
                lock = False
            if lock:
                continue
            delay(config=config, session=session)
            if c % 10 == 0:
                print 'Downloaded %d pages' % (c)
            try:
                for xml in getXMLPage(config=config, title=title, session=session):
                    xml = cleanXML(xml=xml)
                    xmlfile.write(xml.encode('utf-8'))
            except PageMissingError:
                logerror(
                    config=config,
                    text=u'The page "%s" was missing in the wiki (probably deleted)' % title
                )
            # here, XML is a correct <page> </page> chunk or
            # an empty string due to a deleted page (logged in errors log) or
            # an empty string due to an error while retrieving the page from server
            # (logged in errors log)
            c += 1

    xmlfile.write(footer)
    xmlfile.close()
    print 'XML dump saved at...', xmlfilename

def getXMLRevisions(config={}, session=None, allpages=False, start=None):
    # FIXME: actually figure out the various strategies for each MediaWiki version
    apiurl = urlparse(config['api'])
    # FIXME: force the protocol we asked for! Or don't verify SSL if we asked HTTP?
    # https://github.com/WikiTeam/wikiteam/issues/358
    site = mwclient.Site(apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=apiurl.scheme)

    if not 'all' in config['namespaces']:
        namespaces = config['namespaces']
    else:
        namespaces, namespacenames = getNamespacesAPI(config=config, session=session)

    try:
        for namespace in namespaces:
            print("Trying to export all revisions from namespace %s" % namespace)
            # arvgeneratexml exists but was deprecated in 1.26 (while arv is from 1.27?!)
            arvparams = {
                'action': 'query',
                'list': 'allrevisions',
                'arvlimit': 50,
                'arvnamespace': namespace
            }
            if not config['curonly']:
                # We have to build the XML manually...
                # Skip flags, presumably needed to add <minor/> which is in the schema.
                # Also missing: parentid and contentformat.
                arvparams['arvprop'] = 'ids|timestamp|user|userid|size|sha1|contentmodel|comment|content'
                print("Trying to get wikitext from the allrevisions API and to build the XML")
                while True:
                    try:
                        arvrequest = site.api(http_method=config['http_method'], **arvparams)
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 405 and config['http_method'] == "POST":
                            print("POST request to the API failed, retrying with GET")
                            config['http_method'] = "GET"
                            continue
                    except requests.exceptions.ReadTimeout as err:
                        # Hopefully temporary, just wait a bit and continue with the same request.
                        # No point putting a limit to retries, we'd need to abort everything.
                        # TODO: reuse the retry logic of the checkAPI phase? Or force mwclient
                        # to use the retry adapter we use for our own requests session?
                        print("ERROR: {}".format(str(err)))
                        print("Sleeping for 20 seconds")
                        time.sleep(20)
                        continue

                    for page in arvrequest['query']['allrevisions']:
                        yield makeXmlFromPage(page)
                    if 'continue' in arvrequest:
                        arvparams['arvcontinue'] = arvrequest['continue']['arvcontinue']
                    else:
                        # End of continuation. We are done with this namespace.
                        break

            else:
                # FIXME: this is not curonly, just different strategy to do all revisions
                # Just cycle through revision IDs and use the XML as is
                print("Trying to list the revisions and to export them one by one")
                # We only need the revision ID, all the rest will come from the raw export
                arvparams['arvprop'] = 'ids'
                try:
                    arvrequest = site.api(http_method=config['http_method'], **arvparams)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 405 and config['http_method'] == "POST":
                        print("POST request to the API failed, retrying with GET")
                        config['http_method'] = "GET"
                        continue
                exportparams = {
                    'action': 'query',
                    'export': '1',
                }
                # Skip the namespace if it's empty
                if len(arvrequest['query']['allrevisions']) < 1:
                    continue
                # Repeat the arvrequest with new arvparams until done
                while True:
                    # Reset revision IDs from the previous batch from arv
                    revids = []
                    for page in arvrequest['query']['allrevisions']:
                        for revision in page['revisions']:
                            revids.append(str(revision['revid']))
                    print "        %d more revisions listed, until %s" % (len(revids), revids[-1])

                    # We can now get the XML for one revision at a time
                    # FIXME: we can actually get them in batches as we used to
                    # but need to figure out the continuation and avoid that the API
                    # chooses to give us only the latest for each page
                    for revid in revids:
                        exportparams['revids'] = revid
                        try:
                            exportrequest = site.api(http_method=config['http_method'], **exportparams)
                        except requests.exceptions.HTTPError as e:
                            if e.response.status_code == 405 and config['http_method'] == "POST":
                                print("POST request to the API failed, retrying with GET")
                                config['http_method'] = "GET"
                                exportrequest = site.api(http_method=config['http_method'], **exportparams)

                        # This gives us a self-standing <mediawiki> element
                        # but we only need the inner <page>: we can live with
                        # duplication and non-ordering of page titles, but the
                        # repeated header is confusing and would not even be valid
                        xml = exportrequest['query']['export']['*']
                        yield makeXmlPageFromRaw(xml)
                        
                    if 'continue' in arvrequest:
                        # Get the new ones
                        arvparams['arvcontinue'] = arvrequest['continue']['arvcontinue']
                        try:
                            arvrequest = site.api(http_method=config['http_method'], **arvparams)
                        except requests.exceptions.HTTPError as e:
                            if e.response.status_code == 405 and config['http_method'] == "POST":
                                print("POST request to the API failed, retrying with GET")
                                config['http_method'] = "GET"
                                arvrequest = site.api(http_method=config['http_method'], **arvparams)
                        except requests.exceptions.ReadTimeout as err:
                            # As above
                            print("ERROR: {}".format(str(err)))
                            print("Sleeping for 20 seconds")
                            time.sleep(20)
                            # But avoid rewriting the same revisions
                            arvrequest['query']['allrevisions'] = []
                            continue
                    else:
                        # End of continuation. We are done with this namespace.
                        break
                    
    except (KeyError, mwclient.errors.InvalidResponse) as e:
        print(e)
        # TODO: check whether the KeyError was really for a missing arv API
        print "Warning. Could not use allrevisions. Wiki too old?"
        if config['curonly']:
            # The raw XML export in the API gets a title and gives the latest revision.
            # We could also use the allpages API as generator but let's be consistent.
            print("Getting titles to export the latest revision for each")
            c = 0
            for title in readTitles(config, start=start):
                # TODO: respect verbose flag, reuse output from getXMLPage
                print(u'    {}'.format(title))
                # TODO: as we're doing one page and revision at a time, we might
                # as well use xml format and exportnowrap=1 to use the string of,
                # XML as is, but need to check how well the library handles it.
                exportparams = {
                    'action': 'query',
                    'titles': title,
                    'export': '1',
                }
                try:
                    exportrequest = site.api(http_method=config['http_method'], **exportparams)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 405 and config['http_method'] == "POST":
                        print("POST request to the API failed, retrying with GET")
                        config['http_method'] = "GET"
                        exportrequest = site.api(http_method=config['http_method'], **exportparams)

                xml = exportrequest['query']['export']['*']
                c += 1
                if c % 10 == 0:
                    print('Downloaded {} pages'.format(c))
                # Because we got the fancy XML from the JSON format, clean it:
                yield makeXmlPageFromRaw(xml)
        else:
            # This is the closest to what we usually do with Special:Export:
            # take one title at a time and try to get all revisions exported.
            # It differs from the allrevisions method because it actually needs
            # to be input the page titles; otherwise, the requests are similar.
            # The XML needs to be made manually because the export=1 option
            # refuses to return an arbitrary number of revisions (see above).
            print("Getting titles to export all the revisions of each")
            c = 0
            titlelist = []
            # TODO: Decide a suitable number of a batched request. Careful:
            # batched responses may not return all revisions.
            for titlelist in readTitles(config, start=start, batch=False):
                if type(titlelist) is not list:
                    titlelist = [titlelist]
                for title in titlelist:
                    print(u'    {}'.format(title))
                # Try and ask everything. At least on MediaWiki 1.16, uknown props are discarded:
                # "warnings":{"revisions":{"*":"Unrecognized values for parameter 'rvprop': userid, sha1, contentmodel"}}}
                pparams = {
                    'action': 'query',
                    'titles': '|'.join(titlelist),
                    'prop': 'revisions',
                    #'rvlimit': 50,
                    'rvprop': 'ids|timestamp|user|userid|size|sha1|contentmodel|comment|content',
                }
                try:
                    prequest = site.api(http_method=config['http_method'], **pparams)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 405 and config['http_method'] == "POST":
                        print("POST request to the API failed, retrying with GET")
                        config['http_method'] = "GET"
                        exportrequest = site.api(http_method=config['http_method'], **exportparams)
                except mwclient.errors.InvalidResponse:
                    logerror(
                                config=config,
                                text=u'Error: page inaccessible? Could not export page: %s' % ("; ".join(titlelist))
                            )
                    continue

                # Be ready to iterate if there is continuation.
                while True:
                    # Get the revision data returned by the API: prequest is the initial request
                    # or the new one after continuation at the bottom of this while loop.
                    # The array is called "pages" even if there's only one.
                    try:
                        pages = prequest['query']['pages']
                    except KeyError:
                        logerror(
                                config=config,
                                text=u'Error: page inaccessible? Could not export page: %s' % ("; ".join(titlelist))
                            )
                        break
                    # Go through the data we got to build the XML.
                    for pageid in pages:
                        try:
                            xml = makeXmlFromPage(pages[pageid])
                            yield xml
                        except PageMissingError:
                            logerror(
                                config=config,
                                text=u'Error: empty revision from API. Could not export page: %s' % ("; ".join(titlelist))
                            )
                            continue

                    # Get next batch of revisions if there's more.
                    if 'continue' in prequest.keys():
                        print("Getting more revisions for the page")
                        for key, value in prequest['continue']:
                            params[key] = value
                    elif 'query-continue' in prequest.keys():
                        rvstartid = prequest['query-continue']['revisions']['rvstartid']
                        pparams['rvstartid'] = rvstartid
                    else:
                        break

                    try:
                        prequest = site.api(http_method=config['http_method'], **pparams)
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 405 and config['http_method'] == "POST":
                            print("POST request to the API failed, retrying with GET")
                            config['http_method'] = "GET"
                            prequest = site.api(http_method=config['http_method'], **pparams)

                # We're done iterating for this title or titles.
                c += len(titlelist)
                # Reset for the next batch.
                titlelist = []
                if c % 10 == 0:
                    print('Downloaded {} pages'.format(c))


    except mwclient.errors.MwClientError as e:
        print(e)
        print "This mwclient version seems not to work for us. Exiting."
        sys.exit()

def makeXmlFromPage(page):
    """ Output an XML document as a string from a page as in the API JSON """
    try:
        p = E.page(
                E.title(to_unicode(page['title'])),
                E.ns(to_unicode(page['ns'])),
                E.id(to_unicode(page['pageid'])),
        )
        for rev in page['revisions']:
            # Older releases like MediaWiki 1.16 do not return all fields.
            if 'userid' in rev:
                userid = rev['userid']
            else:
                userid = 0
            if 'size' in rev:
                size = rev['size']
            else:
                size = 0
            revision = E.revision(
                E.id(to_unicode(rev['revid'])),
                E.timestamp(rev['timestamp']),
                E.text(to_unicode(rev['*']), space="preserve", bytes=to_unicode(size)),
            )
            # The username may be deleted/suppressed
            if 'user' in rev:
                revision.append(E.contributor(
                        E.username(to_unicode(rev['user'])),
                        E.id(to_unicode(userid)),
                ))
            else:
                revision.append(E.contributor(deleted="deleted"))
            if 'comment' in rev:
                revision.append(E.comment(to_unicode(rev['comment'])))
            if 'contentmodel' in rev:
                revision.append(E.model(rev['contentmodel']))
            # Sometimes a missing parentid is not replaced with a 0 as it should.
            if 'parentid' in rev:
                revision.append(E.parentid(to_unicode(rev['parentid'])))
            # The sha1 may not have been backfilled on older wikis or lack for other reasons (Wikia).
            if 'sha1' in rev:
                revision.append(E.sha1(rev['sha1']))
            p.append(revision)
    except KeyError as e:
        print(e)
        raise PageMissingError(page['title'], e)
    return etree.tostring(p, pretty_print=True, encoding='unicode')

def readTitles(config={}, start=None, batch=False):
    """ Read title list from a file, from the title "start" """

    titlesfilename = '%s-%s-titles.txt' % (
        domain2prefix(config=config), config['date'])
    titlesfile = open('%s/%s' % (config['path'], titlesfilename), 'r')

    titlelist = []
    seeking = False
    if start:
        seeking = True

    with titlesfile as f:
        for line in f:
            title = line.decode("utf-8").strip()
            if title == '--END--':
                break
            elif seeking and title != start:
                continue
            elif seeking and title == start:
                seeking = False

            if not batch:
                yield title
            else:
                titlelist.append(title)
                if len(titlelist) < batch:
                    continue
                else:
                    yield titlelist
                    titlelist = []

def reverse_readline(filename, buf_size=8192, truncate=False):
    """a generator that returns the lines of a file in reverse order"""
    # Original code by srohde, abdus_salam: cc by-sa 3.0
    # http://stackoverflow.com/a/23646049/718903
    with open(filename, 'r+') as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        total_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(total_size, offset + buf_size)
            fh.seek(-offset, os.SEEK_END)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concat the segment to the last line of new chunk
                # instead, yield the segment first 
                if buffer[-1] is not '\n':
                    lines[-1] += segment
                else:
                    if truncate and '</page>' in segment:
                        pages = buffer.split('</page>')
                        fh.seek(-offset+buf_size-len(pages[-1]), os.SEEK_END)
                        fh.truncate
                        raise StopIteration
                    else:
                        yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if truncate and '</page>' in segment:
                    pages = buffer.split('</page>')
                    fh.seek(-offset-len(pages[-1]), os.SEEK_END)
                    fh.truncate
                    raise StopIteration
                else:
                    yield lines[index]
        yield segment

def saveImageNames(config={}, images=[], session=None):
    """ Save image list in a file, including filename, url and uploader """

    imagesfilename = '%s-%s-images.txt' % (
        domain2prefix(config=config), config['date'])
    imagesfile = open('%s/%s' % (config['path'], imagesfilename), 'w')
    imagesfile.write(
        ('\n'.join(
            [
                '%s\t%s\t%s' %
                (filename,
                 url,
                 uploader) for filename,
                url,
                uploader in images]
            ).encode('utf-8')
         )
    )
    imagesfile.write('\n--END--')
    imagesfile.close()

    print 'Image filenames and URLs saved at...', imagesfilename


def curateImageURL(config={}, url=''):
    """ Returns an absolute URL for an image, adding the domain if missing """

    if 'index' in config and config['index']:
        # remove from :// (http or https) until the first / after domain
        domainalone = config['index'].split(
            '://')[0] + '://' + config['index'].split('://')[1].split('/')[0]
    elif 'api' in config and config['api']:
        domainalone = config['api'].split(
            '://')[0] + '://' + config['api'].split('://')[1].split('/')[0]
    else:
        print 'ERROR: no index nor API'
        sys.exit()

    if url.startswith('//'):  # Orain wikifarm returns URLs starting with //
        url = u'%s:%s' % (domainalone.split('://')[0], url)
    # is it a relative URL?
    elif url[0] == '/' or (not url.startswith('http://') and not url.startswith('https://')):
        if url[0] == '/':  # slash is added later
            url = url[1:]
        # concat http(s) + domain + relative url
        url = u'%s/%s' % (domainalone, url)
    url = undoHTMLEntities(text=url)
    # url = urllib.unquote(url) #do not use unquote with url, it break some
    # urls with odd chars
    url = re.sub(' ', '_', url)

    return url


def getImageNamesScraper(config={}, session=None):
    """ Retrieve file list: filename, url, uploader """

    # (?<! http://docs.python.org/library/re.html
    r_next = r'(?<!&amp;dir=prev)&amp;offset=(?P<offset>\d+)&amp;'
    images = []
    offset = '29990101000000'  # january 1, 2999
    limit = 5000
    retries = config['retries']
    while offset:
        # 5000 overload some servers, but it is needed for sites like this with
        # no next links
        # http://www.memoryarchive.org/en/index.php?title=Special:Imagelist&sort=byname&limit=50&wpIlMatch=
        r = session.post(
            url=config['index'],
            params={
                'title': 'Special:Imagelist',
                'limit': limit,
                'offset': offset},
            timeout=30)
        raw = r.text
        delay(config=config, session=session)
        # delicate wiki
        if re.search(
                ur'(?i)(allowed memory size of \d+ bytes exhausted|Call to a member function getURL)',
                raw):
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
            new_offset = re.findall(r_next, raw)[0]
            # Avoid infinite loop
            if new_offset != offset:
                offset = new_offset
                retries += 5  # add more retries if we got a page with offset
            else:
                offset = ''
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
        params = {
            'action': 'query',
            'list': 'allimages',
            'aiprop': 'url|user',
            'aifrom': aifrom,
            'format': 'json',
            'ailimit': 50}
        # FIXME Handle HTTP Errors HERE
        r = session.get(url=config['api'], params=params, timeout=30)
        handleStatusCode(r)
        jsonimages = getJSON(r)
        delay(config=config, session=session)

        if 'query' in jsonimages:
            aifrom = ''
            if 'query-continue' in jsonimages and 'allimages' in jsonimages[
                    'query-continue']:
                if 'aicontinue' in jsonimages['query-continue']['allimages']:
                    aifrom = jsonimages[
                        'query-continue']['allimages']['aicontinue']
                elif 'aifrom' in jsonimages['query-continue']['allimages']:
                    aifrom = jsonimages[
                        'query-continue']['allimages']['aifrom']
            elif 'continue' in jsonimages:
                if 'aicontinue' in jsonimages['continue']:
                    aifrom = jsonimages['continue']['aicontinue']
                elif 'aifrom' in jsonimages['continue']:
                    aifrom = jsonimages['continue']['aifrom']
            # print aifrom

            for image in jsonimages['query']['allimages']:
                url = image['url']
                url = curateImageURL(config=config, url=url)
                # encoding to ascii is needed to work around this horrible bug:
                # http://bugs.python.org/issue8136
                if 'api' in config and ('.wikia.' in config['api'] or '.fandom.com' in config['api']):
                    #to avoid latest?cb=20120816112532 in filenames
                    filename = unicode(urllib.unquote((re.sub('_', ' ', url.split('/')[-3])).encode('ascii', 'ignore')), 'utf-8')
                else:
                    filename = unicode(urllib.unquote((re.sub('_', ' ', url.split('/')[-1])).encode('ascii', 'ignore')), 'utf-8')
                uploader = re.sub('_', ' ', image['user'])
                images.append([filename, url, uploader])
        else:
            oldAPI = True
            break

    if oldAPI:
        gapfrom = '!'
        images = []
        while gapfrom:
            sys.stderr.write('.')  # progress
            # Some old APIs doesn't have allimages query
            # In this case use allpages (in nm=6) as generator for imageinfo
            # Example:
            # http://minlingo.wiki-site.com/api.php?action=query&generator=allpages&gapnamespace=6
            # &gaplimit=500&prop=imageinfo&iiprop=user|url&gapfrom=!
            params = {
                'action': 'query',
                'generator': 'allpages',
                'gapnamespace': 6,
                'gaplimit': 50,
                'gapfrom': gapfrom,
                'prop': 'imageinfo',
                'iiprop': 'user|url',
                'format': 'json'}
            # FIXME Handle HTTP Errors HERE
            r = session.get(url=config['api'], params=params, timeout=30)
            handleStatusCode(r)
            jsonimages = getJSON(r)
            delay(config=config, session=session)

            if 'query' in jsonimages:
                gapfrom = ''
                if 'query-continue' in jsonimages and 'allpages' in jsonimages[
                        'query-continue']:
                    if 'gapfrom' in jsonimages['query-continue']['allpages']:
                        gapfrom = jsonimages[
                            'query-continue']['allpages']['gapfrom']
                # print gapfrom
                # print jsonimages['query']

                for image, props in jsonimages['query']['pages'].items():
                    url = props['imageinfo'][0]['url']
                    url = curateImageURL(config=config, url=url)

                    tmp_filename = ':'.join(props['title'].split(':')[1:])

                    filename = re.sub('_', ' ', tmp_filename)
                    uploader = re.sub('_', ' ', props['imageinfo'][0]['user'])
                    images.append([filename, url, uploader])
            else:
                # if the API doesn't return query data, then we're done
                break

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

        r = session.head(url=url, allow_redirects=True)
        original_url_redirected = len(r.history) > 0

        if original_url_redirected:
            #print 'Site is redirecting us to: ', r.url
            original_url = url
            url = r.url

        r = session.get(url=url, allow_redirects=False)

        # Try to fix a broken HTTP to HTTPS redirect
        if r.status_code ==  404 and  original_url_redirected:
           if original_url.split("://")[0] == "http" and url.split("://")[0] == "https":
              url = 'https://' + original_url.split("://")[1]
              #print 'Maybe a broken http to https redirect, trying ', url
              r = session.get(url=url, allow_redirects=False)

        if r.status_code ==  404:
              logerror(
                  config=config,
                  text=u'File %s at URL %s is missing' % (filename2,url))

        imagefile.write(r.content)
        imagefile.close()
        # saving description if any
        try:
            title = u'Image:%s' % (filename)
            if config['xmlrevisions'] and config['api'] and config['api'].endswith("api.php"):
                r = session.get(config['api'] + u"?action=query&export&exportnowrap&titles=%s" % title)
                xmlfiledesc = r.text
            else:
                xmlfiledesc = getXMLFileDesc(
                    config=config,
                    title=title,
                    session=session)  # use Image: for backwards compatibility
        except PageMissingError:
            xmlfiledesc = ''
            logerror(
                config=config,
                text=u'The page "%s" was missing in the wiki (probably deleted)' % (title.decode('utf-8'))
            )

        f = open('%s/%s.desc' % (imagepath, filename2), 'w')
        # <text xml:space="preserve" bytes="36">Banner featuring SG1, SGA, SGU teams</text>
        if not re.search(r'</page>', xmlfiledesc):
            # failure when retrieving desc? then save it as empty .desc
            xmlfiledesc = ''

        # Fixup the XML
        if xmlfiledesc is not '' and not re.search(r'</mediawiki>', xmlfiledesc):
            xmlfiledesc += '</mediawiki>'

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
    domain = re.sub(r'(https?://|www\.|/index\.php.*|/api\.php.*)', '', domain)
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
    message += "\n"
    message += "# Copyright (C) 2011-%d WikiTeam developers                           #\n" % (datetime.datetime.now().year)
    message += """
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
        '--delay',
        metavar=5,
        default=0,
        type=float,
        help="adds a delay (in seconds)")
    parser.add_argument(
        '--retries',
        metavar=5,
        default=5,
        help="Maximum number of retries for ")
    parser.add_argument('--path', help='path to store wiki dump at')
    parser.add_argument(
        '--resume',
        action='store_true',
        help='resumes previous incomplete dump (requires --path)')
    parser.add_argument('--force', action='store_true', help='')
    parser.add_argument(
        '--user', help='Username if authentication is required.')
    parser.add_argument(
        '--pass',
        dest='password',
        help='Password if authentication is required.')

    # URL params
    groupWikiOrAPIOrIndex = parser.add_argument_group()
    groupWikiOrAPIOrIndex.add_argument(
        'wiki',
        default='',
        nargs='?',
        help="URL to wiki (e.g. http://wiki.domain.org)")
    groupWikiOrAPIOrIndex.add_argument(
        '--api',
        help="URL to API (e.g. http://wiki.domain.org/w/api.php)")
    groupWikiOrAPIOrIndex.add_argument(
        '--index',
        help="URL to index.php (e.g. http://wiki.domain.org/w/index.php)")

    # Download params
    groupDownload = parser.add_argument_group(
        'Data to download',
        'What info download from the wiki')
    groupDownload.add_argument(
        '--xml',
        action='store_true',
        help="generates a full history XML dump (--xml --curonly for current revisions only)")
    groupDownload.add_argument('--curonly', action='store_true',
        help='store only the current version of pages')
    groupDownload.add_argument('--xmlrevisions', action='store_true',
                               help='download all revisions from an API generator. MediaWiki 1.27+ only.')
    groupDownload.add_argument(
        '--images', action='store_true', help="generates an image dump")
    groupDownload.add_argument(
        '--namespaces',
        metavar="1,2,3",
        help='comma-separated value of namespaces to include (all by default)')
    groupDownload.add_argument(
        '--exnamespaces',
        metavar="1,2,3",
        help='comma-separated value of namespaces to exclude')

    # Meta info params
    groupMeta = parser.add_argument_group(
        'Meta info',
        'What meta info to retrieve from the wiki')
    groupMeta.add_argument(
        '--get-wiki-engine',
        action='store_true',
        help="returns the wiki engine")
    groupMeta.add_argument(
        '--failfast',
        action='store_true',
        help="Avoid resuming, discard failing wikis quickly. Useful only for mass downloads.")

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
    try:
        from requests.packages.urllib3.util.retry import Retry
        from requests.adapters import HTTPAdapter
        # Courtesy datashaman https://stackoverflow.com/a/35504626
        __retries__ = Retry(total=5,
                        backoff_factor=2,
                        status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=__retries__))
        session.mount('http://', HTTPAdapter(max_retries=__retries__))
    except:
        # Our urllib3/requests is too old
        pass
    session.cookies = cj
    session.headers.update({'User-Agent': getUserAgent()})
    if args.user and args.password:
        session.auth = (args.user, args.password)

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

    # print api
    # print index
    index2 = None

    if api:
        check, checkedapi = checkRetryAPI(api, args.retries, args.xmlrevisions, session)

    if api and check:
        # Replace the index URL we got from the API check
        index2 = check[1]
        api = checkedapi
        print 'API is OK: ' + checkedapi
    else:
        if index and not args.wiki:
            print 'API not available. Trying with index.php only.'
            args.api = None
        else:
            print 'Error in API. Please, provide a correct path to API'
            sys.exit(1)

    if index and checkIndex(
            index=index,
            cookies=args.cookies,
            session=session):
        print 'index.php is OK'
    else:
        index = index2
        if index and index.startswith('//'):
            index = args.wiki.split('//')[0] + index
        if index and checkIndex(
                index=index,
                cookies=args.cookies,
                session=session):
            print 'index.php is OK'
        else:
            try:
                index = '/'.join(index.split('/')[:-1])
            except AttributeError:
                index = None
            if index and checkIndex(
                    index=index,
                    cookies=args.cookies,
                    session=session):
                print 'index.php is OK'
            else:
                print 'Error in index.php.'
                if not args.xmlrevisions:
                    print 'Please, provide a correct path to index.php or use --xmlrevisions. Terminating.'
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
        if re.search(
                r'[^\d, \-]',
                args.namespaces) and args.namespaces.lower() != 'all':
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
        'failfast': args.failfast,
        'http_method': "POST",
        'index': index,
        'images': args.images,
        'logs': False,
        'xml': args.xml,
        'xmlrevisions': args.xmlrevisions,
        'namespaces': namespaces,
        'exnamespaces': exnamespaces,
        'path': args.path and os.path.normpath(args.path) or '',
        'cookies': args.cookies or '',
        'delay': args.delay,
        'retries': int(args.retries),
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


def checkRetryAPI(api=None, retries=5, apiclient=False, session=None):
    """ Call checkAPI and mwclient if necessary """
    retry = 0
    retrydelay = 20
    check = None
    while retry < retries:
        try:
            check = checkAPI(api, session=session)
            break
        except requests.exceptions.ConnectionError as e:
            print 'Connection error: %s'%(str(e))
            retry += 1
            print "Start retry attempt %d in %d seconds."%(retry+1, retrydelay)
            time.sleep(retrydelay)

    if check and apiclient:
        apiurl = urlparse(api)
        try:
            site = mwclient.Site(apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=apiurl.scheme)
        except KeyError:
            # Probably KeyError: 'query'
            if apiurl.scheme == "https":
                newscheme = "http"
                api = api.replace("https://", "http://")
            else:
                newscheme = "https"
                api = api.replace("http://", "https://")
            print("WARNING: The provided API URL did not work with mwclient. Switched protocol to: {}".format(newscheme))

            try:
                site = mwclient.Site(apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=newscheme)
            except KeyError:
                check = False

    return check, api

def checkAPI(api=None, session=None):
    """ Checking API availability """
    global cj
    # handle redirects
    for i in range(4):
        print 'Checking API...', api
        r = session.get(
            url=api,
            params={
                'action': 'query',
                'meta': 'siteinfo',
                'format': 'json'},
            timeout=30
        )
        if r.status_code == 200:
            break
        elif r.status_code < 400:
            p = r.url
            api = urlunparse([p.scheme, p.netloc, p.path, '', '', ''])
        elif r.status_code > 400:
            print "MediaWiki API URL not found or giving error: HTTP %d" % r.status_code
            return False
    if "MediaWiki API is not enabled for this site." in r.text:
        return False
    try:
        result = getJSON(r)
        index = None
        if result:
            try:
                index = result['query']['general']['server'] + \
                    result['query']['general']['script']
                return ( True, index, api )
            except KeyError:
                print "MediaWiki API seems to work but returned no index URL"
                return (True, None, api)
    except ValueError:
        print repr(r.text)
        print "MediaWiki API returned data we could not parse"
        return False
    return False


def checkIndex(index=None, cookies=None, session=None):
    """ Checking index.php availability """
    r = session.post(url=index, data={'title': 'Special:Version'}, timeout=30)
    if r.status_code >= 400:
        print("ERROR: The wiki returned status code HTTP {}".format(r.status_code))
        return False
    raw = r.text
    print 'Checking index.php...', index
    # Workaround for issue 71
    if re.search(
            r'(Special:Badtitle</a>|class="permissions-errors"|"wgCanonicalSpecialPageName":"Badtitle"|Login Required</h1>)',
            raw) and not cookies:
        print "ERROR: This wiki requires login and we are not authenticated"
        return False
    if re.search(
            r'(page-Index_php|"wgPageName":"Index.php"|"firstHeading"><span dir="auto">Index.php</span>)',
            raw):
        print "Looks like the page called Index.php, not index.php itself"
        return False
    if re.search(
            r'(This wiki is powered by|<h2 id="mw-version-license">|meta name="generator" content="MediaWiki)',
            raw):
        return True
    return False


def removeIP(raw=''):
    """ Remove IP from HTML comments <!-- --> """

    raw = re.sub(r'\d+\.\d+\.\d+\.\d+', '0.0.0.0', raw)
    # http://www.juniper.net/techpubs/software/erx/erx50x/swconfig-routing-vol1/html/ipv6-config5.html
    # weird cases as :: are not included
    raw = re.sub(
        r'(?i)[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}',
        '0:0:0:0:0:0:0:0',
        raw)

    return raw


def getJSON(request):
    """Strip Unicode BOM"""
    if request.text.startswith(u'\ufeff'):
        request.encoding = 'utf-8-sig'
    try:
        return request.json()
    except:
        # Maybe an older API version which did not return correct JSON
        return {}


def fixBOM(request):
    """Strip Unicode BOM"""
    if request.text.startswith(u'\ufeff'):
        request.encoding = 'utf-8-sig'
    return request.text


def checkXMLIntegrity(config={}, titles=[], session=None):
    """ Check XML dump integrity, to detect broken XML chunks """
    return

    print 'Verifying dump...'
    checktitles = 0
    checkpageopen = 0
    checkpageclose = 0
    checkrevisionopen = 0
    checkrevisionclose = 0
    for line in file(
            '%s/%s-%s-%s.xml' %
            (config['path'],
             domain2prefix(
                config=config,
                session=session),
                config['date'],
                config['curonly'] and 'current' or 'history'),
            'r').read().splitlines():
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
        if config['failfast']:
            reply = 'yes'
        while reply.lower() not in ['yes', 'y', 'no', 'n']:
            reply = raw_input('Regenerate a new dump ([yes, y], [no, n])? ')
        if reply.lower() in ['yes', 'y']:
            generateXMLDump(config=config, titles=titles, session=session)
        elif reply.lower() in ['no', 'n']:
            print 'Not generating a new dump.'


def createNewDump(config={}, other={}):
    images = []
    print 'Trying generating a new dump into a new directory...'
    if config['xml']:
        getPageTitles(config=config, session=other['session'])
        titles=readTitles(config)
        generateXMLDump(config=config, titles=titles, session=other['session'])
        checkXMLIntegrity(
            config=config,
            titles=titles,
            session=other['session'])
    if config['images']:
        images += getImageNames(config=config, session=other['session'])
        saveImageNames(config=config, images=images, session=other['session'])
        generateImageDump(
            config=config,
            other=other,
            images=images,
            session=other['session'])
    if config['logs']:
        saveLogs(config=config, session=other['session'])


def resumePreviousDump(config={}, other={}):
    images = []
    print 'Resuming previous dump process...'
    if config['xml']:
        titles=readTitles(config)
        try:
            lasttitles = reverse_readline('%s/%s-%s-titles.txt' %
                ( config['path'],
                domain2prefix( config=config, session=other['session'] ),
                config['date'])
                )
            lasttitle=lasttitles.next()
            if lasttitle == '':
                lasttitle=lasttitles.next()
        except:
            lasttitle = ''  # probably file does not exists
        if lasttitle == '--END--':
            # titles list is complete
            print 'Title list was completed in the previous session'
        else:
            print 'Title list is incomplete. Reloading...'
            # do not resume, reload, to avoid inconsistencies, deleted pages or
            # so
            getPageTitles(config=config, session=other['session'])

        # checking xml dump
        xmliscomplete = False
        lastxmltitle = None
        try:
            f = reverse_readline(
                '%s/%s-%s-%s.xml' %
                (config['path'],
                 domain2prefix(
                    config=config,
                    session=other['session']),
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
                    lastxmltitle = undoHTMLEntities(text=xmltitle.group(1))
                    break
        except:
            pass  # probably file does not exists

        if xmliscomplete:
            print 'XML dump was completed in the previous session'
        elif lastxmltitle:
            # resuming...
            print 'Resuming XML dump from "%s"' % (lastxmltitle)
            titles = readTitles(config, start=lastxmltitle)
            generateXMLDump(
                config=config,
                titles=titles,
                start=lastxmltitle,
                session=other['session'])
        else:
            # corrupt? only has XML header?
            print 'XML is corrupt? Regenerating...'
            titles = readTitles(config)
            generateXMLDump(
                config=config, titles=titles, session=other['session'])

    if config['images']:
        # load images
        lastimage = ''
        try:
            f = open(
                '%s/%s-%s-images.txt' %
                (config['path'],
                 domain2prefix(
                    config=config),
                    config['date']),
                'r')
            raw = unicode(f.read(), 'utf-8').strip()
            lines = raw.split('\n')
            for l in lines:
                if re.search(r'\t', l):
                    images.append(l.split('\t'))
            lastimage = lines[-1]
            f.close()
        except:
            pass  # probably file does not exists
        if lastimage == u'--END--':
            print 'Image list was completed in the previous session'
        else:
            print 'Image list is incomplete. Reloading...'
            # do not resume, reload, to avoid inconsistencies, deleted images or
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
                config=config,
                other=other,
                images=images,
                start=lastfilename2,
                session=other['session'])

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
            url=config['index'], params={'title': 'Special:Version'}, timeout=10)
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
        r = session.post(url=config['index'], params={}, timeout=10)
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
            r = session.get(
                url=config['api'],
                params={
                    'action': 'query',
                    'meta': 'siteinfo',
                    'siprop': 'general|namespaces|statistics|dbrepllag|interwikimap|namespacealiases|specialpagealiases|usergroups|extensions|skins|magicwords|fileextensions|rightsinfo',
                    'sinumberingroup': 1,
                    'format': 'json'},
                timeout=10)
            # MediaWiki 1.11-1.12
            if not 'query' in getJSON(r):
                r = session.get(
                    url=config['api'],
                    params={
                        'action': 'query',
                        'meta': 'siteinfo',
                        'siprop': 'general|namespaces|statistics|dbrepllag|interwikimap',
                        'format': 'json'},
                    timeout=10)
            # MediaWiki 1.8-1.10
            if not 'query' in getJSON(r):
                r = session.get(
                    url=config['api'],
                    params={
                        'action': 'query',
                        'meta': 'siteinfo',
                        'siprop': 'general|namespaces',
                        'format': 'json'},
                    timeout=10)
            result = getJSON(r)
            delay(config=config, session=session)
            with open('%s/siteinfo.json' % (config['path']), 'w') as outfile:
                outfile.write(json.dumps(result, indent=4, sort_keys=True))


def avoidWikimediaProjects(config={}, other={}):
    """ Skip Wikimedia projects and redirect to the dumps website """

    # notice about wikipedia dumps
    url = ''
    if config['api']:
        url = url + config['api']
    if config['index']:
        url = url + config['index']
    if re.findall(
            r'(?i)(wikipedia|wikisource|wiktionary|wikibooks|wikiversity|wikimedia|wikispecies|wikiquote|wikinews|wikidata|wikivoyage)\.org',
            url):
        print 'PLEASE, DO NOT USE THIS SCRIPT TO DOWNLOAD WIKIMEDIA PROJECTS!'
        print 'Download the dumps from http://dumps.wikimedia.org'
        if not other['force']:
            print 'Thanks!'
            sys.exit()


def getWikiEngine(url=''):
    """ Returns the wiki engine of a URL, if known """

    session = requests.Session()
    session.headers.update({'User-Agent': getUserAgent()})
    r = session.post(url=url, timeout=30)
    if r.status_code == 405 or r.text == '':
        r = session.get(url=url, timeout=120)
    result = r.text

    wikiengine = 'Unknown'
    if re.search(
            ur'(?im)(<meta name="generator" content="DokuWiki)|dokuwiki__site',
            result):
        wikiengine = 'DokuWiki'
    elif re.search(ur'(?im)(alt="Powered by MediaWiki"|<meta name="generator" content="MediaWiki)', result):
        wikiengine = 'MediaWiki'
    elif re.search(ur'(?im)(>MoinMoin Powered</a>|<option value="LocalSiteMap">)', result):
        wikiengine = 'MoinMoin'
    elif re.search(ur'(?im)(twikiCurrentTopicLink|twikiCurrentWebHomeLink|twikiLink)', result):
        wikiengine = 'TWiki'
    elif re.search(ur'(?im)(<!--PageHeaderFmt-->)', result):
        wikiengine = 'PmWiki'
    elif re.search(ur'(?im)(<meta name="generator" content="PhpWiki|<meta name="PHPWIKI_VERSION)', result):
        wikiengine = 'PhpWiki'
    elif re.search(ur'(?im)(<meta name="generator" content="Tiki Wiki|Powered by <a href="http://(www\.)?tiki\.org"| id="tiki-(top|main)")', result):
        wikiengine = 'TikiWiki'
    elif re.search(ur'(?im)(foswikiNoJs|<meta name="foswiki\.|foswikiTable|foswikiContentFooter)', result):
        wikiengine = 'FosWiki'
    elif re.search(ur'(?im)(<meta http-equiv="powered by" content="MojoMojo)', result):
        wikiengine = 'MojoMojo'
    elif re.search(ur'(?im)(id="xwiki(content|nav_footer|platformversion|docinfo|maincontainer|data)|/resources/js/xwiki/xwiki|XWiki\.webapppath)', result):
        wikiengine = 'XWiki'
    elif re.search(ur'(?im)(<meta id="confluence-(base-url|context-path)")', result):
        wikiengine = 'Confluence'
    elif re.search(ur'(?im)(<meta name="generator" content="Banana Dance)', result):
        wikiengine = 'Banana Dance'
    elif re.search(ur'(?im)(Wheeled by <a class="external-link" href="http://www\.wagn\.org">|<body id="wagn">)', result):
        wikiengine = 'Wagn'
    elif re.search(ur'(?im)(<meta name="generator" content="MindTouch)', result):
        wikiengine = 'MindTouch'  # formerly DekiWiki
    elif re.search(ur'(?im)(<div class="wikiversion">\s*(<p>)?JSPWiki|xmlns:jspwiki="http://www\.jspwiki\.org")', result):
        wikiengine = 'JSPWiki'
    elif re.search(ur'(?im)(Powered by:?\s*(<br ?/>)?\s*<a href="http://kwiki\.org">|\bKwikiNavigation\b)', result):
        wikiengine = 'Kwiki'
    elif re.search(ur'(?im)(Powered by <a href="http://www\.anwiki\.com")', result):
        wikiengine = 'Anwiki'
    elif re.search(ur'(?im)(<meta name="generator" content="Aneuch|is powered by <em>Aneuch</em>|<!-- start of Aneuch markup -->)', result):
        wikiengine = 'Aneuch'
    elif re.search(ur'(?im)(<meta name="generator" content="bitweaver)', result):
        wikiengine = 'bitweaver'
    elif re.search(ur'(?im)(powered by <a href="[^"]*\bzwiki.org(/[^"]*)?">)', result):
        wikiengine = 'Zwiki'
    # WakkaWiki forks
    elif re.search(ur'(?im)(<meta name="generator" content="WikkaWiki|<a class="ext" href="(http://wikka\.jsnx\.com/|http://wikkawiki\.org/)">)', result):
        wikiengine = 'WikkaWiki'  # formerly WikkaWakkaWiki
    elif re.search(ur'(?im)(<meta name="generator" content="CoMa Wiki)', result):
        wikiengine = 'CoMaWiki'
    elif re.search(ur'(?im)(Fonctionne avec <a href="http://www\.wikini\.net)', result):
        wikiengine = 'WikiNi'
    elif re.search(ur'(?im)(Powered by <a href="[^"]*CitiWiki">CitiWiki</a>)', result):
        wikiengine = 'CitiWiki'
    elif re.search(ur'(?im)(Powered by <a href="http://wackowiki\.com/|title="WackoWiki")', result):
        wikiengine = 'WackoWiki'
    elif re.search(ur'(?im)(Powered by <a href="http://www\.wakkawiki\.com)', result):
        # This may not work for heavily modded/themed installations, e.g.
        # http://operawiki.info/
        wikiengine = 'WakkaWiki'
    # Custom wikis used by wiki farms
    elif re.search(ur'(?im)(var wikispaces_page|<div class="WikispacesContent)', result):
        wikiengine = 'Wikispaces'
    elif re.search(ur'(?im)(Powered by <a href="http://www\.wikidot\.com">|wikidot-privacy-button-hovertip|javascript:WIKIDOT\.page)', result):
        wikiengine = 'Wikidot'
    elif re.search(ur'(?im)(IS_WETPAINT_USER|wetpaintLoad|WPC-bodyContentContainer)', result):
        wikiengine = 'Wetpaint'
    elif re.search(ur'(?im)(<div id="footer-pbwiki">|ws-nav-search|PBinfo *= *{)', result):
        # formerly PBwiki
        wikiengine = 'PBworks'
    # if wikiengine == 'Unknown': print result

    return wikiengine


def mwGetAPIAndIndex(url=''):
    """ Returns the MediaWiki API and Index.php """

    api = ''
    index = ''
    session = requests.Session()
    session.headers.update({'User-Agent': getUserAgent()})
    r = session.post(url=url, timeout=120)
    result = r.text

    # API
    m = re.findall(
        ur'(?im)<\s*link\s*rel="EditURI"\s*type="application/rsd\+xml"\s*href="([^>]+?)\?action=rsd"\s*/\s*>',
        result)
    if m:
        api = m[0]
        if api.startswith('//'):  # gentoo wiki
            api = url.split('//')[0] + api
    else:
        pass  # build API using index and check it

    # Index.php
    m = re.findall(
        ur'<li id="ca-viewsource"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?',
        result)
    if m:
        index = m[0]
    else:
        m = re.findall(
            ur'<li id="ca-history"[^>]*?>\s*(?:<span>)?\s*<a href="([^\?]+?)\?',
            result)
        if m:
            index = m[0]
    if index:
        if index.startswith('/'):
            index = '/'.join(api.split('/')[:-1]) + '/' + index.split('/')[-1]
    else:
        if api:
            if len(
                re.findall(
                    ur'/index\.php5\?',
                    result)) > len(
                re.findall(
                    ur'/index\.php\?',
                    result)):
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
        if config['failfast']:
            retry = 'yes'
        while reply.lower() not in ['yes', 'y', 'no', 'n']:
            reply = raw_input(
                'There is a dump in "%s", probably incomplete.\nIf you choose resume, to avoid conflicts, the parameters you have chosen in the current session will be ignored\nand the parameters available in "%s/%s" will be loaded.\nDo you want to resume ([yes, y], [no, n])? ' %
                (config['path'],
                 config['path'],
                    configfilename))
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
