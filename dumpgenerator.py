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
import getopt
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

def getTitles(config={}):
    #Get page titles parsing Special:Allpages or using API (fix)
    #
    #http://en.wikipedia.org/wiki/Special:AllPages
    #http://archiveteam.org/index.php?title=Special:AllPages
    #http://www.wikanda.es/wiki/Especial:Todas
    print 'Loading page titles from namespaces =', ','.join([str(i) for i in config['namespaces']])
    
    #namespace checks and stuff
    #fix get namespaces from a randome Special:Export page, it is better
    namespacenames = {0:''} # main is 0, no prefix
    namespaces = config['namespaces']
    if namespaces:
        raw = urllib.urlopen('%s?title=Special:Allpages' % (config['domain'])).read()
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
        url = '%s?title=Special:Allpages&namespace=%s' % (config['domain'], namespace)
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
                    url = '%s?title=Special:Allpages&namespace=%s&from=%s&to=%s' % (config['domain'], namespace, fr, to) #do not put urllib.quote in fr or to
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

def getXMLHeader(config={}):
    #get the header of a random page, to attach it in the complete XML backup
    #similar to: <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.3/" xmlns:x....
    randomtitle = 'AMF5LKE43MNFGHKSDMRTJ'
    xml = getXMLPage(config=config, title=randomtitle)
    header = xml.split('</mediawiki>')[0]
    return header

def getXMLPage(config={}, title=''):
    #http://www.mediawiki.org/wiki/Manual_talk:Parameters_to_Special:Export#Parameters_no_longer_in_use.3F
    limit = 1000
    truncated = False
    title_ = re.sub(' ', '_', title)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.0.4) Gecko/20060508 Firefox/1.5.0.4'}
    params = {'title': 'Special:Export', 'pages': title_, 'action': 'submit', }
    if config['curonly']:
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
    if not config['curonly'] and re.search(r_timestamp, xml): # search for timestamps in xml to avoid analysing empty pages like Special:Allpages and the random one
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

def generateXMLDump(config={}, titles=[]):
    print 'Retrieving the XML for every page'
    header = getXMLHeader(domain=config['domain'])
    footer = '</mediawiki>\n' #new line at the end
    xmlfilename = '%s/%s-%s-%s.xml' % (config['path'], domain2prefix(domain=domain), config['curonly'] and 'current' or 'history', datetime.datetime.now().strftime('%Y%m%d'))
    xmlfile = open('%s/%s' (config['path'], xmlfilename), 'w')
    xmlfile.write(header)
    c = 1
    for title in titles:
        if c % 10 == 0:
            print '    Downloaded %d pages' % (c)
        xml = getXMLPage(config={}, title=title)
        xml = cleanXML(xml=xml)
        xmlfile.write(xml)
        c += 1
    xmlfile.write(footer)
    xmlfile.close()
    print 'XML dump saved at...', xmlfilename

def saveTitles(config={}, titles=[]):
    #save titles in a txt for resume if needed
    titlesfilename = '%s/%s-titles-%s.txt' % (config['path'], domain2prefix(domain=domain), datetime.datetime.now().strftime('%Y%m%d'))
    titlesfile = open(titlesfilename, 'w')
    titles.append('--END--')
    titlesfile.write('\n'.join(titles))
    titlesfile.close()
    print 'Titles saved at...', titlesfilename

def generateImageDump(config={}):
    #slurp all the images
    #special:imagelist
    #save in a .tar?
    #tener en cuenta http://www.mediawiki.org/wiki/Manual:ImportImages.php
    print 'Retrieving image filenames'
    r_next = r'(?<!&amp;dir=prev)&amp;offset=(?P<offset>\d+)&amp;' # (?<! http://docs.python.org/library/re.html
    images = []
    offset = '29990101000000' #january 1, 2999
    while offset:
        url = '%s?title=Special:Imagelist&limit=5000&offset=%s' % (config['domain'], offset)
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
    
    imagepath = '%s/images' % (config['path'])
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
    
def saveLogs(config={}):
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

def loadConfig(config={}, configfilename=''):
    f = open('%s/%s' % (config['path'], configfilename), 'r')
    config = cPickle.load(f)
    f.close()
    return config

def saveConfig(config={}, configfilename=''):
    f = open('%s/%s' % (config['path'], configfilename), 'w')
    cPickle.dump(config, f)
    f.close()
    
def welcome():
    print "-"*75
    print """Welcome to DumpGenerator by WikiTeam"""
    print "-"*75

def bye():
    print "Bye!"

def usage():
    print "Write a complete help"

def getParameters():
    #domain = 'http://archiveteam.org/index.php'
    #domain = 'http://bulbapedia.bulbagarden.net/w/index.php'
    #domain = 'http://wikanda.cadizpedia.eu/w/index.php'
    #domain = 'http://en.citizendium.org/index.php'
    #domain = 'http://en.wikipedia.org/w/index.php'
    #domain = 'http://www.editthis.info/CODE_WIKI/'
    #domain = 'http://www.editthis.info/bobobo_WIKI/'
    domain = 'http://osl2.uca.es/wikira/index.php'
    config = {
        'curonly': False,
        'domain': domain,
        'images': False,
        'logs': False,
        'xml': False,
        'namespaces': [0],
        'path': '',
        'threads': 1,
    }
    other = {
        'resume': False,
    }
    #console params
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["h", "help", "path=", "domain=", "images", "logs", "xml", "curonly", "threads=", "resume" ])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("--path"):
            config["path"] = a
            while len(config["path"])>0:
                if config["path"][-1] == '/': #dará problemas con rutas windows?
                    config["path"] = config["path"][:-1]
                else:
                    break
            if not config["path"]:
                config["path"] = '.'
        elif o in ("--domain"):
            config["domain"] = a
        elif o in ("--images"):
            config["images"] = True
        elif o in ("--logs"):
            config["logs"] = True
        elif o in ("--xml"):
            config["xml"] = True
        elif o in ("--curonly"):
            if not config["xml"]:
                print "If you select --curonly, you must use --xml too"
                sys.exit()
            config["curonly"] = True
        elif o in ("--threads"):
            config["threads"] = int(a)
        elif o in ("--resume"):
            other["resume"] = True
        else:
            assert False, "unhandled option"

    #missing mandatory params
    if not config["domain"] or \
       not (config["xml"] or config["images"] or config["logs"]):
        print """Error. You forget mandatory parameters:
    --domain: URL to index.php in the wiki (examples: http://en.wikipedia.org/w/index.php or http://archiveteam.org/index.php)
    
And one of these, or two or three:
    --xml: it generates a XML dump. It retrieves full history of pages located in namespace = 0 (articles)
           If you want more namespaces, use the parameter --namespaces=0,1,2,3... or --namespaces=all
    --images: it generates an image dump
    --logs: it generates a log dump
    
Write --help for help."""
        sys.exit()
        #usage()
    
    #calculating path
    config['path'] = './%s-dump-%s' % (domain2prefix(domain=config['domain']), datetime.datetime.now().strftime('%Y%m%d'))
    
    return config, other

def main():
    welcome()
    configfilename = 'config.txt'
    config, other = getParameters()
    
    #notice about wikipedia dumps
    if re.findall(r'(wikipedia|wikisource|wiktionary|wikibooks|wikiversity|wikimedia|wikispecies|wikiquote|wikinews)\.org', config['domain']):
        print 'DO NOT USE THIS SCRIPT TO DOWNLOAD WIKIMEDIA PROJECTS!\nDownload the dumps from http://download.wikimedia.org\nThanks!'
        sys.exit()
    
    #creating path or resuming if desired
    c = 2
    while os.path.isdir(config['path']):
        print '\nWarning!: "%s" path exists' % (config['path'])
        reply = raw_input('There is a dump in "%s", probably incomplete.\nIf you choose resume, to avoid conflicts, the parameters you have chosen in the current session will be ignored\nand the parameters available in "%s/%s" will be loaded.\nDo you want to resume ([yes, y], otherwise no)? ' % (config['path'], config['path'], configfilename))
        if reply.lower() in ['yes', 'y']:
            if os.path.isfile('%s/%s' % (config['path'], configfilename)):
                print 'Loading config file...'
                config = loadConfig(config=config, configfilename=configfilename)
            else:
                print 'No config file found. Aborting.'
                sys.exit()
            print 'You have selected YES'
            print 'OK, resuming...'
            other['resume'] = True
            break
        else:
            print 'You have selected NO'
            print 'Trying generating a new dump into a new directory...'
        config['path'] = '%s-%d' % (config['path'], c)
        print 'Trying "%s"...' % (config['path'])
        c += 1

    if not other['resume']:
        os.mkdir(config['path'])
        saveConfig(config=config, configfilename=configfilename)
    
    #ok, creating dump
    #fix, hacer que se pueda resumir la lista de títulos por donde iba (para wikis grandes)
    titles = []
    if other['resume']:
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
            #remove complete namespaces and then getTitles(config=config, start=start)
            #titles += getTitles(config=config, start=last)
            pass
    else:
        #titles += getTitles(config=config, start='!')
        #saveTitles(config=config, titles=titles)
        if config['xml']:
            generateXMLDump(config=config, titles=titles)
        if config['images']:
            generateImageDump(config=config)
        if config['logs']:
            saveLogs(config=config)
    
    bye()

if __name__ == "__main__":
    main()
