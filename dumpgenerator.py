#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

# Copyright (C) 2011 emijrp
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

import cPickle
import datetime
import os
import re
import subprocess
import sys
import urllib
import urllib2

# todo:
# 
# resuming feature:
# save all titles in a .txt, to resume when ctrl-c
# re.findall('<title>([^<]+)</title>', xml) to see when it was aborted, and resume from there
# 
# other:
# curonly and all history (curonly si puede acumular varias peticiones en un solo GET, ara full history pedir cada pagina una a una)
# usar api o parsear html si no está disponible
# http://www.mediawiki.org/wiki/Manual:Parameters_to_Special:Export
# threads para bajar más rápido? pedir varias páginas a la vez
# images?
# Special:Log? uploads, account creations, etc
# download Special:Version to save whch extension it used
# que guarde el index.php (la portada) como index.html para que se vea la licencia del wiki abajo del todo
# fix use api when available

def cleanHTML(raw=''):
    if re.search('<!-- bodytext -->', raw): #<!-- bodytext --> <!-- /bodytext --> <!-- start content --> <!-- end content -->
        raw = raw.split('<!-- bodytext -->')[1].split('<!-- /bodytext -->')[0]
    elif re.search('<!-- start content -->', raw):
        raw = raw.split('<!-- start content -->')[1].split('<!-- end content -->')[0]
    else:
        print 'This wiki doesn\'t use marks to split contain'
        sys.exit()
    return raw

def getTitles(domain='', namespaces=[]):
    #Get page titles parsing Special:Allpages or using API (fix)
    #
    #http://en.wikipedia.org/wiki/Special:AllPages
    #http://archiveteam.org/index.php?title=Special:AllPages
    #http://www.wikanda.es/wiki/Especial:Todas
    if not domain:
        print 'Please, use --domain parameter'
        sys.exit()
    
    print 'Loading page titles from namespaces =', ','.join([str(i) for i in namespaces])
    
    #namespace checks and stuff
    #fix get namespaces from a randome Special:Export page, it is better
    namespacenames = {0:''} # main is 0, no prefix
    if namespaces:
        raw = urllib.urlopen('%s?title=Special:Allpages' % (domain)).read()
        m = re.compile(r'<option [^>]*?value="(?P<namespaceid>\d+)"[^>]*?>(?P<namespacename>[^<]+)</option>').finditer(raw) # [^>]*? to include selected="selected"
        if 'all' in namespaces:
            namespaces = []
            for i in m:
                namespaces.append(int(i.group("namespaceid")))
                namespacenames[int(i.group("namespaceid"))] = i.group("namespacename")
        else:
            #check if those namespaces really exist in this wiki
            namespaces2 = []
            for i in m:
                if int(i.group("namespaceid")) in namespaces:
                    namespaces2.append(int(i.group("namespaceid")))
                    namespacenames[int(i.group("namespaceid"))] = i.group("namespacename")
            namespaces = namespaces2
    else:
        namespaces = [0]
    
    #retrieve all titles from Special:Allpages, if the wiki is big, perhaps there are sub-Allpages to explore
    namespaces = [i for i in set(namespaces)] #uniques
    print '%d namespaces have been found' % (len(namespaces))
    
    titles = []
    for namespace in namespaces:
        print '    Retrieving titles in the namespace', namespace
        url = '%s?title=Special:Allpages&namespace=%s' % (domain, namespace)
        raw = urllib.urlopen(url).read()
        raw = cleanHTML(raw)
        
        r_title = r'title="(?P<title>[^>]+)">'
        r_suballpages = r'&amp;from=(?P<from>[^>]+)&amp;to=(?P<to>[^>]+)">'
        deep = 3 # 3 is the current deep of English Wikipedia for Special:Allpages, 3 levels
        c = 0
        checked_suballpages = []
        rawacum = raw
        while re.search(r_suballpages, raw) and c < deep:
            #load sub-Allpages
            m = re.compile(r_suballpages).finditer(raw)
            for i in m:
                fr = i.group('from')
                to = i.group('to')
                name = '%s-%s' % (fr, to)
                if not name in checked_suballpages:
                    checked_suballpages.append(name)
                    url = '%s?title=Special:Allpages&namespace=%s&from=%s&to=%s' % (domain, namespace, fr, to) #do not put urllib.quote in fr or to
                    raw2 = urllib.urlopen(url).read()
                    raw2 = cleanHTML(raw2)
                    rawacum += raw2 #merge it after removed junk
                    print '    Detected sub-Allpages:', name, len(raw2), 'bytes', len(re.findall(r_title, raw2))
            c += 1
        
        m = re.compile(r_title).finditer(rawacum)
        for i in m:
            if not i.group('title').startswith('Special:'):
                if not i.group('title') in titles:
                    titles.append(i.group('title'))
    print '%d page titles loaded' % (len(titles))
    return titles

def getXMLHeader(domain=''):
    #get the header of a random page, to attach it in the complete XML backup
    #similar to: <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/" xmlns:x....
    randomtitle = 'AMF5LKE43MNFGHKSDMRTJ'
    xml = getXMLPage(domain=domain, title=randomtitle)
    header = xml.split('</mediawiki>')[0]
    return header

def getXMLPage(domain='', title='', curonly=False):
    #http://www.mediawiki.org/wiki/Manual_talk:Parameters_to_Special:Export#Parameters_no_longer_in_use.3F
    limit = 1000
    truncated = False
    title_ = re.sub(' ', '_', title)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.0.4) Gecko/20060508 Firefox/1.5.0.4'}
    params = {'title': 'Special:Export', 'pages': title_, 'action': 'submit', }
    if curonly:
        params['curonly'] = 1
    else:
        params['offset'] = '1'
        params['limit'] = limit
    data = urllib.urlencode(params)
    req = urllib2.Request(url=domain, data=data, headers=headers)
    f = urllib2.urlopen(req)
    xml = f.read()

    #if complete history, check if this page history has > limit edits, if so, retrieve all using offset if available
    #else, warning about Special:Export truncating large page histories
    r_timestamp = r'<timestamp>([^<]+)</timestamp>'
    if not curonly and re.search(r_timestamp, xml): # search for timestamps in xml to avoid analysing empty pages like Special:Allpages and the random one
        while not truncated and params['offset']:
            params['offset'] = re.findall(r_timestamp, xml)[-1] #get the last timestamp from the acum XML
            data = urllib.urlencode(params)
            req2 = urllib2.Request(url=domain, data=data, headers=headers)
            f2 = urllib2.urlopen(req2)
            xml2 = f2.read()
            if re.findall(r_timestamp, xml2): #are there more edits in this next XML chunk?
                if re.findall(r_timestamp, xml2)[-1] == params['offset']:
                    #again the same XML, this wiki does not support params in Special:Export, offer complete XML up to X edits (usually 1000)
                    print 'ATTENTION: This wiki does not allow some parameters in Special:Export, so, pages with large histories may be truncated'
                    truncated = True
                    break
                else:
                    #offset is OK in this wiki, merge with the previous chunk of this page history and continue
                    xml = xml.split('</page>')[0]+xml2.split('<page>\n')[1]
            else:
                params['offset'] = '' #no more edits in this page history
            print title, len(re.findall(r_timestamp, xml)), 'edits'
    return xml

def cleanXML(xml=''):
    xml = xml.split('</siteinfo>\n')[1]
    xml = xml.split('</mediawiki>')[0]
    return xml

def generateXMLDump(path='', domain='', titles=[], curonly=False):
    print 'Retrieving the XML for every page'
    header = getXMLHeader(domain=domain)
    footer = '</mediawiki>\n' #new line at the end
    xmlfilename = '%s%s-%s-%s.xml' % (path and '%s/' % (path) or '', domain2prefix(domain=domain), curonly and 'current' or 'history', datetime.datetime.now().strftime('%Y%m%d'))
    xmlfile = open(path and '%s/%s' (path, xmlfilename) or xmlfilename, 'w')
    xmlfile.write(header)
    c = 1
    for title in titles:
        if c % 10 == 0:
            print '    Downloaded %d pages' % (c)
        xml = getXMLPage(domain=domain, title=title, curonly=curonly)
        xml = cleanXML(xml=xml)
        xmlfile.write(xml)
        c += 1
    xmlfile.write(footer)
    xmlfile.close()
    print 'XML dump saved at...', xmlfilename

def saveTitles(path='', titles=[]):
    #save titles in a txt for resume if needed
    titlesfilename = '%s%s-titles-%s.txt' % (path and '%s/' % (path) or '', domain2prefix(domain=domain), datetime.datetime.now().strftime('%Y%m%d'))
    titlesfile = open(titlesfilename, 'w')
    titles.append('--END--')
    titlesfile.write('\n'.join(titles))
    titlesfile.close()
    print 'Titles saved at...', titlesfilename

def generateImageDump(path=''):
    #slurp all the images
    #special:imagelist
    #save in a .tar?
    #tener en cuenta http://www.mediawiki.org/wiki/Manual:ImportImages.php
    print 'Retrieving image filenames'
    r_next = r'(?<!&amp;dir=prev)&amp;offset=(?P<offset>\d+)&amp;' # (?<! http://docs.python.org/library/re.html
    images = []
    offset = '29990101000000' #january 1, 2999
    while offset:
        url = '%s?title=Special:Imagelist&limit=5000&offset=%s' % (domain, offset)
        raw = urllib.urlopen(url).read()
        raw = cleanHTML(raw)
        m = re.compile(r'<a href="(?P<url>[^>]+/./../[^>]+)">[^<]+</a>').finditer(raw)
        for i in m:
            url = i.group('url')
            filename = re.sub('_', ' ', url.split('/')[-1])
            filename_ = re.sub(' ', '_', url.split('/')[-1])
            images.append([filename, url])
        
        if re.search(r_next, raw):
            offset = re.findall(r_next, raw)[0]
        else:
            offset = ''
    
    print '    Found %d images' % (len(images))
    
    imagepath = path and '%s/images' % (path) or 'images'
    if os.path.isdir(imagepath):
        print 'It exists a images directory for this dump' #fix, resume?
    else:
        os.makedirs(imagepath)
    
    c = 0
    for filename, url in images:
        urllib.urlretrieve(url, '%s/%s' % (imagepath, filename))
        c += 1
        if c % 10 == 0:
            print '    Downloaded %d images' % (c)
    print 'Downloaded %d images' % (c)
    
def saveLogs(path=''):
    #get all logs from Special:Log
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

def domain2prefix(domain=''):
    domain = re.sub(r'(http://|www\.|/index\.php)', '', domain)
    domain = re.sub(r'/', '_', domain)
    domain = re.sub(r'\.', '', domain)
    domain = re.sub(r'[^A-Za-z0-9]', '_', domain)
    return domain

def loadConfig(path='', configfilename=''):
    config = {}
    f = open('%s%s' % (path and '%s/' % (path) or '', configfilename), 'r')
    config = cPickle.load(f)
    f.close()
    return config

def saveConfig(path='', configfilename='', config={}):
    f = open('%s%s' % (path and '%s/' % (path) or '', configfilename), 'w')
    cPickle.dump(config, f)
    f.close()

if __name__ == '__main__':
    #read sys.argv
    #options: --domain --images --logs --xml --resume --threads=3
    
    #variables
    #domain = 'http://archiveteam.org/index.php'
    #domain = 'http://bulbapedia.bulbagarden.net/w/index.php'
    #domain = 'http://wikanda.cadizpedia.eu/w/index.php'
    #domain = 'http://en.citizendium.org/index.php'
    #domain = 'http://en.wikipedia.org/w/index.php'
    #domain = 'http://www.editthis.info/CODE_WIKI/'
    #domain = 'http://www.editthis.info/bobobo_WIKI/'
    domain = 'http://osl2.uca.es/wikira/index.php'
    configfilename = 'config.txt'
    config = {
        'curonly': False,
        'domain': domain,
        'images': True,
        'logs': False,
        'namespaces': ['all'],
        'resume': False,
        'threads': 1,
    }
    resume = False
    
    #notice about wikipedia dumps
    if re.findall(r'(wikipedia|wikisource|wiktionary|wikibooks|wikiversity|wikimedia|wikispecies|wikiquote|wikinews)\.org', config['domain']):
        print 'DO NOT USE THIS SCRIPT TO DOWNLOAD WIKIMEDIA PROJECTS!\nDownload the dumps from http://download.wikimedia.org\nThanks!'
        sys.exit()
    
    #creating file path or resuming if desired
    path = '%s-dump-%s' % (domain2prefix(domain=config['domain']), datetime.datetime.now().strftime('%Y%m%d')) #fix, rewrite path when resuming from other day when this feature is available
    path2 = path
    c = 2
    while os.path.isdir(path2):
        print 'Warning!: "%s" directory exists' % (path2)
        reply = raw_input('There is a dump in "%s", probably incomplete.\nIf you choose resume, to avoid conflicts, the parameters you have chosen in the current session will be ignored\nand the parameters available in "%s/%s" will be loaded.\nDo you want to resume ([yes, y], [no, n])? ' % (path2, path2, configfilename))
        if reply.lower() in ['yes', 'y']:
            if os.path.isfile('%s/%s' % (path2, configfilename)):
                print 'Loading config file...'
                config = loadConfig(path=path2, configfilename=configfilename)
            else:
                print 'No config file found. Aborting.'
                sys.exit()
            print 'OK, resuming...'
            resume = True
            break
        else:
            print 'OK, trying generating a new dump into a new directory...'
        path2 = '%s-%d' % (path, c)
        print 'Trying "%s"...' % (path2)
        c += 1
    path = path2
    if not resume:
        os.mkdir(path)
        saveConfig(path=path, configfilename=configfilename, config=config)
    
    #ok, creating dump
    #fix, hacer que se pueda resumir la lista de títulos por donde iba (para wikis grandes)
    titles = []
    if resume:
        #load titles
        #search last
        last = 'lastline'
        if last == '--END--':
            #titles list is complete
            pass
            lastlinexml = 'aaa'
            if lastlinexml == '</mediawiki>\n':
                #xml dump is complete
                pass
                lastimage = 'pepito'
                if lastimage == 'aaaa':
                    #image dump complete
                    pass
                    lastlog = 'aaaa'
                    if lastlog == 'loquesea':
                        #log dump complete
                        pass
                    else:
                        #resume log
                        pass
                else:
                    #resume images
                    pass
            else:
                #resume xml dump
                pass
        else:
            #start = last
            #remove complete namespaces and then getTitles(domainconfig['domain'], namespaces=namespacesmissing, start=start)
            #titles += getTitles(domain=config['domain'], namespaces=config['namespaces'], start=last)
            pass
    else:
        #titles += getTitles(config['domain'], namespaces=config['namespaces'], start='!')
        #saveTitles(path=path, titles=titles)
        #generateXMLDump(path=path, domain=config['domain'], titles=titles, curonly=config['curonly'])
        if config['images']:
            generateImageDump(path=path, )
        if config['logs']:
            saveLogs(path=path, )
