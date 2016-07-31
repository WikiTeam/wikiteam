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

import argparse
import cPickle # what is in python3?
import datetime
import random
import re
import sys
import urllib

if sys.version_info < (3, 0):
    import cookielib
else:
    import http.cookiejar as cookielib

__version__ = "0.3.0"

def avoidWikimediaProjects(config={}):
    """ Skip Wikimedia projects and redirect to the dumps website """

    # notice about wikipedia dumps
    if re.findall(r'(?i)(wikipedia|wikisource|wiktionary|wikibooks|wikiversity|wikimedia|wikispecies|wikiquote|wikinews|wikidata|wikivoyage)\.org', config['wiki']):
        print('PLEASE, DO NOT USE THIS SCRIPT TO DOWNLOAD WIKIMEDIA PROJECTS!')
        print('Download Wikimedia dumps from https://dumps.wikimedia.org')
        """if not other['force']:
            print 'Thanks!'
            sys.exit()"""

def bye():
    """ Print closing message """
    
    message = """
---> Congratulations! Your dump is complete <---
If you found any bug, report a new issue here: https://github.com/WikiTeam/wikiteam/issues
If this is a public wiki, please consider publishing this dump. Do it yourself as explained in https://github.com/WikiTeam/wikiteam/wiki/Tutorial#Publishing_the_dump or contact us at https://github.com/WikiTeam/wikiteam
Good luck! Bye!"""
    print(message)

def createNewDump(config={}):
    if config['wikiengine'] == 'mediawiki':
        import mediawiki
        mwCreateNewDump(config=config)
    elif config['wikiengine'] == 'wikispaces':
        import wikispaces
        wsCreateNewDump(config=config)
    else:
        print("Wikiengine %s not supported. Exiting." % (config['wikiengine']))

def createDumpPath(config={}):
    # creating path or resuming if desired
    c = 2
    # to avoid concat blabla-2, blabla-2-3, and so on...
    originalpath = config['path']
    # do not enter if resume is requested from begining
    while not config['other']['resume'] and os.path.isdir(config['path']):
        print('\nWarning!: "%s" path exists' % (config['path']))
        reply = ''
        while reply.lower() not in ['yes', 'y', 'no', 'n']:
            reply = raw_input(
                'There is a dump in "%s", probably incomplete.\nIf you choose resume, to avoid conflicts, the parameters you have chosen in the current session will be ignored\nand the parameters available in "%s/%s" will be loaded.\nDo you want to resume ([yes, y], [no, n])? ' %
                (config['path'],
                 config['path'],
                    config['other']['configfilename']))
        if reply.lower() in ['yes', 'y']:
            if not os.path.isfile('%s/%s' % (config['path'], config['other']['configfilename'])):
                print('No config file found. I can\'t resume. Aborting.')
                sys.exit()
            print('You have selected: YES')
            config['other']['resume'] = True
            break
        elif reply.lower() in ['no', 'n']:
            print('You have selected: NO')
            config['other']['resume'] = False
        config['path'] = '%s-%d' % (originalpath, c)
        print('Trying to use path "%s"...' % (config['path']))
        c += 1
    return config

def domain2prefix(config={}):
    """ Convert domain name to a valid prefix filename. """

    domain = ''
    if config['wiki']:
        domain = config['wiki']
    domain = domain.lower()
    domain = re.sub(r'(https?://|www\.|/index\.php|/api\.php)', '', domain)
    domain = re.sub(r'/', '_', domain)
    domain = re.sub(r'\.', '', domain)
    domain = re.sub(r'[^A-Za-z0-9]', '_', domain)
    domain = domain.strip('_')
    return domain

def getAPI(url=''):
    """ Returns API for a wiki, if available """
    
    wikiengine = getWikiEngine(url=url)
    api = ''
    if wikiengine == 'mediawiki':
        api = mediawiki.mwGetAPI(url=url)
    
    return api

def getIndex(url=''):
    """ Returns Index.php for a wiki, if available """
    
    wikiengine = getWikiEngine(url=url)
    index = ''
    if wikiengine == 'mediawiki':
        index = mediawiki.mwGetIndex(url=url)
    
    return index

def getParameters(params=[]):
    """ Import parameters into variable """
    
    if not params:
        params = sys.argv
    
    config = {}
    parser = argparse.ArgumentParser(description='Tools for downloading and preserving wikis.')

    # General params
    parser.add_argument(
        '-v', '--version', action='version', version=getVersion())
    parser.add_argument(
        '--cookies', metavar="cookies.txt", help="Path to a cookies.txt file.")
    parser.add_argument(
        '--delay',
        metavar=5,
        default=0,
        type=float,
        help="Adds a delay (in seconds).")
    parser.add_argument(
        '--retries',
        metavar=5,
        default=5,
        help="Maximum number of retries.")
    parser.add_argument('--path', help='Path to store wiki dump at.')
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resumes previous incomplete dump (requires --path).')
    parser.add_argument('--force', action='store_true', help='')
    parser.add_argument(
        '--user', help='Username if authentication is required.')
    parser.add_argument(
        '--pass',
        dest='password',
        help='Password if authentication is required.')

    # URL params
    groupWiki = parser.add_argument_group()
    groupWiki.add_argument(
        'wiki',
        default='',
        nargs='?',
        help="URL to wiki (e.g. http://wiki.domain.org).")
    groupWiki.add_argument(
        '--mw-api',
        help="URL to MediaWiki API (e.g. http://wiki.domain.org/w/api.php).")
    groupWiki.add_argument(
        '--mw-index',
        help="URL to MediaWiki index.php (e.g. http://wiki.domain.org/w/index.php).")

    # Download params
    groupDownload = parser.add_argument_group(
        'Data to download',
        'What info download from the wiki')
    groupDownload.add_argument(
        '--pages',
        action='store_true',
        help="Generates a dump of pages (--pages --curonly for current revisions only).")
    groupDownload.add_argument('--curonly', action='store_true',
                               help='Store only the current version of pages.')
    groupDownload.add_argument(
        '--images', action='store_true', help="Generates an image dump.")
    groupDownload.add_argument(
        '--namespaces',
        metavar="1,2,3",
        help='Comma-separated value of namespaces to include (all by default).')
    groupDownload.add_argument(
        '--exnamespaces',
        metavar="1,2,3",
        help='Comma-separated value of namespaces to exclude.')

    # Meta info params
    groupMeta = parser.add_argument_group(
        'Meta info',
        'What meta info to retrieve from the wiki')
    groupMeta.add_argument(
        '--get-api',
        action='store_true',
        help="Returns wiki API when available.")
    groupMeta.add_argument(
        '--get-index',
        action='store_true',
        help="Returns wiki Index.php when available.")
    groupMeta.add_argument(
        '--get-wiki-engine',
        action='store_true',
        help="Returns wiki engine.")

    args = parser.parse_args()
    #print(args)
    
    # Not wiki? Exit
    if not args.wiki:
        print('ERROR: Provide a URL to a wiki')
        parser.print_help()
        sys.exit(1)
    
    # Don't mix download params and meta info params
    if (args.pages or args.images) and \
            (args.get_wiki_engine):
        print('ERROR: Don\'t mix download params and meta info params')
        parser.print_help()
        sys.exit(1)

    # No download params and no meta info params? Exit
    if (not args.pages and not args.images) and \
            (not args.get_api and not args.get_wiki_engine):
        print('ERROR: Use at least one download param or meta info param')
        parser.print_help()
        sys.exit(1)

    # Execute meta info params
    if args.wiki:
        if args.get_api:
            print(getAPI(url=args.wiki))
            sys.exit()
        if args.get_wiki_engine:
            print(getWikiEngine(url=args.wiki))
            sys.exit()

    # Load cookies
    cj = cookielib.MozillaCookieJar()
    if args.cookies:
        cj.load(args.cookies)
        print('Using cookies from %s' % args.cookies)

    # check user and pass (one requires both)
    if (args.user and not args.password) or (args.password and not args.user):
        print('ERROR: Both --user and --pass are required for authentication.')
        parser.print_help()
        sys.exit(1)
    
    session = None
    if args.user and args.password:
        import requests
        session = requests.Session()
        session.cookies = cj
        session.headers.update({'User-Agent': getUserAgent()})
        session.auth = (args.user, args.password)
        #session.mount(args.mw_api.split('/api.php')[0], HTTPAdapter(max_retries=max_ret)) Mediawiki-centric, be careful

    # check URLs
    for url in [args.mw_api, args.mw_index, args.wiki]:
        if url and (not url.startswith('http://') and not url.startswith('https://')):
            print(url)
            print('ERROR: URLs must start with http:// or https://\n')
            parser.print_help()
            sys.exit(1)
    
    wikiengine = getWikiEngine(args.wiki)
    if wikiengine == 'wikispaces':
        import wikispaces
        pass
    else: # presume is a mediawiki
        import mediawiki
        if not args.mw_api:
            api = mediawiki.mwGetAPI(url=args.wiki)
            if not api:
                print('ERROR: Provide a URL to API')
        if not args.mw_index:
            index = mediawiki.mwGetIndex(url=args.wiki)
            if not index:
                print('ERROR: Provide a URL to Index.php')

    namespaces = ['all']
    exnamespaces = []
    # Process namespace inclusions
    if args.namespaces:
        # fix, why - ?  and... --namespaces= all with a space works?
        if re.search(
                r'[^\d, \-]',
                args.namespaces) and args.namespaces.lower() != 'all':
            print("Invalid namespace values.\nValid format is integer(s) separated by commas")
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
            print("Invalid namespace values.\nValid format is integer(s) separated by commas")
            sys.exit(1)
        else:
            ns = re.sub(' ', '', args.exnamespaces)
            if ns.lower() == 'all':
                print('You cannot exclude all namespaces.')
                sys.exit(1)
            else:
                exnamespaces = [int(i) for i in ns.split(',')]

    # --curonly requires --xml
    if args.curonly and not args.pages:
        print("--curonly requires --pages\n")
        parser.print_help()
        sys.exit(1)

    config = {
        'wiki': args.wiki, 
        'wikicanonical': '', 
        'wikiengine': wikiengine, 
        'curonly': args.curonly, 
        'date': datetime.datetime.now().strftime('%Y%m%d'), 
        'images': args.images, 
        'pages': args.pages, 
        'logs': False, 
        'pages': args.pages, 
        'namespaces': namespaces, 
        'exnamespaces': exnamespaces, 
        'path': args.path and os.path.normpath(args.path) or '', 
        'cookies': args.cookies or '', 
        'delay': args.delay, 
        'retries': int(args.retries), 
         'other': {
            'configfilename': 'config.txt', 
            'resume': args.resume, 
            'filenamelimit': 100,  # do not change
            'force': args.force, 
            'session': session, 
        }
    }

    # calculating path, if not defined by user with --path=
    if not config['path']:
        config['path'] = './%s-%s-wikidump' % (domain2prefix(config=config), config['date'])

    return config

def getURL(url=''):
    html = ''
    try:
        req = urllib.request.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
        html = urllib.request.urlopen(req).read().decode().strip()
    except:
        print("Error while retrieving URL", url)
        sys.exit()
    return html

def getUserAgent():
    """ Return a cool user-agent to hide Python user-agent """
    
    useragents = [
        'Mozilla/5.0', 
    ]
    return random.choice(useragents)

def getVersion():
    return __version__

def getWikiEngine(url=''):
    """ Returns wiki engine of a URL, if known """
    
    wikiengine = 'unknown'
    if url:
        html = getURL(url=url)
    else:
        return wikiengine.lower()
    
    if re.search(
            r'(?im)(<meta name="generator" content="DokuWiki)|dokuwiki__site',
            result):
        wikiengine = 'dokuwiki'
    elif re.search(r'(?im)(alt="Powered by MediaWiki"|<meta name="generator" content="MediaWiki)', result):
        wikiengine = 'mediawiki'
    elif re.search(r'(?im)(>MoinMoin Powered</a>|<option value="LocalSiteMap">)', result):
        wikiengine = 'moinmoin'
    elif re.search(r'(?im)(twikiCurrentTopicLink|twikiCurrentWebHomeLink|twikiLink)', result):
        wikiengine = 'twiki'
    elif re.search(r'(?im)(<!--PageHeaderFmt-->)', result):
        wikiengine = 'pmwiki'
    elif re.search(r'(?im)(<meta name="generator" content="PhpWiki|<meta name="PHPWIKI_VERSION)', result):
        wikiengine = 'phpwiki'
    elif re.search(r'(?im)(<meta name="generator" content="Tiki Wiki|Powered by <a href="http://(www\.)?tiki\.org"| id="tiki-(top|main)")', result):
        wikiengine = 'tikiwiki'
    elif re.search(r'(?im)(foswikiNoJs|<meta name="foswiki\.|foswikiTable|foswikiContentFooter)', result):
        wikiengine = 'foswiki'
    elif re.search(r'(?im)(<meta http-equiv="powered by" content="MojoMojo)', result):
        wikiengine = 'mojomojo'
    elif re.search(r'(?im)(id="xwiki(content|nav_footer|platformversion|docinfo|maincontainer|data)|/resources/js/xwiki/xwiki|XWiki\.webapppath)', result):
        wikiengine = 'xwiki'
    elif re.search(r'(?im)(<meta id="confluence-(base-url|context-path)")', result):
        wikiengine = 'confluence'
    elif re.search(r'(?im)(<meta name="generator" content="Banana Dance)', result):
        wikiengine = 'bananadance'
    elif re.search(r'(?im)(Wheeled by <a class="external-link" href="http://www\.wagn\.org">|<body id="wagn">)', result):
        wikiengine = 'wagn'
    elif re.search(r'(?im)(<meta name="generator" content="MindTouch)', result):
        wikiengine = 'mindtouch'  # formerly DekiWiki
    elif re.search(r'(?im)(<div class="wikiversion">\s*(<p>)?JSPWiki|xmlns:jspwiki="http://www\.jspwiki\.org")', result):
        wikiengine = 'jspwiki'
    elif re.search(r'(?im)(Powered by:?\s*(<br ?/>)?\s*<a href="http://kwiki\.org">|\bKwikiNavigation\b)', result):
        wikiengine = 'kwiki'
    elif re.search(r'(?im)(Powered by <a href="http://www\.anwiki\.com")', result):
        wikiengine = 'anwiki'
    elif re.search(r'(?im)(<meta name="generator" content="Aneuch|is powered by <em>Aneuch</em>|<!-- start of Aneuch markup -->)', result):
        wikiengine = 'aneuch'
    elif re.search(r'(?im)(<meta name="generator" content="bitweaver)', result):
        wikiengine = 'bitweaver'
    elif re.search(r'(?im)(powered by <a href="[^"]*\bzwiki.org(/[^"]*)?">)', result):
        wikiengine = 'zwiki'
    # WakkaWiki forks
    elif re.search(r'(?im)(<meta name="generator" content="WikkaWiki|<a class="ext" href="(http://wikka\.jsnx\.com/|http://wikkawiki\.org/)">)', result):
        wikiengine = 'wikkawiki'  # formerly WikkaWakkaWiki
    elif re.search(r'(?im)(<meta name="generator" content="CoMa Wiki)', result):
        wikiengine = 'comawiki'
    elif re.search(r'(?im)(Fonctionne avec <a href="http://www\.wikini\.net)', result):
        wikiengine = 'wikini'
    elif re.search(r'(?im)(Powered by <a href="[^"]*CitiWiki">CitiWiki</a>)', result):
        wikiengine = 'citiwiki'
    elif re.search(r'(?im)(Powered by <a href="http://wackowiki\.com/|title="WackoWiki")', result):
        wikiengine = 'wackowiki'
    elif re.search(r'(?im)(Powered by <a href="http://www\.wakkawiki\.com)', result):
        # This may not work for heavily modded/themed installations, e.g.
        # http://operawiki.info/
        wikiengine = 'wakkawiki'
    # Custom wikis used by wiki farms
    elif re.search(r'(?im)(var wikispaces_page|<div class="WikispacesContent)', result):
        wikiengine = 'wikispaces'
    elif re.search(r'(?im)(Powered by <a href="http://www\.wikidot\.com">|wikidot-privacy-button-hovertip|javascript:WIKIDOT\.page)', result):
        wikiengine = 'wikidot'
    elif re.search(r'(?im)(IS_WETPAINT_USER|wetpaintLoad|WPC-bodyContentContainer)', result):
        wikiengine = 'wetpaint'
    elif re.search(r'(?im)(<div id="footer-pbwiki">|ws-nav-search|PBinfo *= *{)', result):
        # formerly PBwiki
        wikiengine = 'pbworks'
    # if wikiengine == 'Unknown': print result

    return wikiengine.lower()

def resumePreviousDump(config={}):
    if config['wikiengine'] == 'mediawiki':
        import mediawiki
        mwResumePreviousDump(config=config)
    elif config['wikiengine'] == 'wikispaces':
        import wikispaces
        wsResumePreviousDump(config=config)
    else:
        print("Wikiengine %s not supported. Exiting." % (config['wikiengine']))

def saveConfig(config={}):
    """ Save config file """
    
    # Do not save config['other'] as it has session info and other stuff
    config2 = config
    config2['other'] = {}
    with open('%s/%s' % (config['path'], config['other']['configfilename']), 'w') as outfile:
        print('Saving config file...')
        cPickle.dump(config2, outfile)

def welcome():
    """ Print opening message """
    
    message = """
#########################################################################
# Welcome to WikiTeam's tools v%s (GPL v3)                           #
# More info at: https://github.com/WikiTeam/wikiteam                    #
#########################################################################

#########################################################################
# Copyright (C) 2011-2016 WikiTeam                                      #
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#########################################################################
""" % (getVersion())
    print(message)

def loadConfig(config={}):
    """ Load config file """
    
    try:
        with open('%s/%s' % (config['path'], config['other']['configfilename']), 'r') as infile:
            print('Loading config file...')
            config = cPickle.load(infile)
    except:
        print('ERROR: There is no config file. we can\'t resume. Start a new dump.')
        sys.exit()

    return config

def main(params=[]):
    """ Main function """
    
    config = getParameters(params=params)
    #print(config)
    
    welcome()
    avoidWikimediaProjects(config=config)
    config = createDumpPath(config=config)
    
    if config['other']['resume']:
        config = loadConfig(config=config)
    else:
        os.mkdir(config['path'])
        saveConfig(config=config)

    if config['other']['resume']:
        resumePreviousDump(config=config)
    else:
        createNewDump(config=config)
    
    """move to mw
    saveIndexPHP(config=config, session=other['session'])
    saveSpecialVersion(config=config, session=other['session'])
    saveSiteInfo(config=config, session=other['session'])"""
    bye()

if __name__ == "__main__":
    main()
