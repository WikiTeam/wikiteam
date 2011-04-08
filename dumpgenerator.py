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
import time
import urllib
import urllib2

# todo:
# curonly and all history (curonly si puede acumular varias peticiones en un solo GET, ara full history pedir cada pagina una a una)
# usar api o parsear html si no está disponible
# http://www.mediawiki.org/wiki/Manual:Parameters_to_Special:Export
# threads para bajar más rápido? pedir varias páginas a la vez
# Special:Log? uploads, account creations, etc
# download Special:Version to save whch extension it used
# que guarde el index.php (la portada) como index.html para que se vea la licencia del wiki abajo del todo
# fix use api when available

def delay(config={}):
    if config['delay'] > 0:
        print 'Sleeping... %d seconds...' % (config['delay'])
        time.sleep(config['delay'])

def cleanHTML(raw=''):
    if re.search('<!-- bodytext -->', raw): #<!-- bodytext --> <!-- /bodytext --> <!-- start content --> <!-- end content -->
        raw = raw.split('<!-- bodytext -->')[1].split('<!-- /bodytext -->')[0]
    elif re.search('<!-- start content -->', raw):
        raw = raw.split('<!-- start content -->')[1].split('<!-- end content -->')[0]
    else:
        print 'This wiki doesn\'t use marks to split contain'
        sys.exit()
    return raw

def getPageTitles(config={}, start='!'):
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

def getXMLFileDesc(config={}, title=''):
    config['curonly'] = 1 #tricky to get only the most recent desc
    return getXMLPage(config=config, title=title)

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
    req = urllib2.Request(url=config['domain'], data=data, headers=headers)
    try:
        f = urllib2.urlopen(req)
    except:
        try:
            print 'Sever is slow... Waiting some seconds and retrying...'
            time.sleep(10)
            f = urllib2.urlopen(req)
        except:
            print 'An error have occurred while retrieving', title
            print 'Please, resume the dump, --resume'
            sys.exit()
    xml = f.read()

    #if complete history, check if this page history has > limit edits, if so, retrieve all using offset if available
    #else, warning about Special:Export truncating large page histories
    r_timestamp = r'<timestamp>([^<]+)</timestamp>'
    if not config['curonly'] and re.search(r_timestamp, xml): # search for timestamps in xml to avoid analysing empty pages like Special:Allpages and the random one
        while not truncated and params['offset']:
            params['offset'] = re.findall(r_timestamp, xml)[-1] #get the last timestamp from the acum XML
            data = urllib.urlencode(params)
            req2 = urllib2.Request(url=config['domain'], data=data, headers=headers)
            try:
                f2 = urllib2.urlopen(req2)
            except:
                try:
                    print 'Sever is slow... Waiting some seconds and retrying...'
                    time.sleep(10)
                    f2 = urllib2.urlopen(req2)
                except:
                    print 'An error have occurred while retrieving', title
                    print 'Please, resume the dump, --resume'
                    sys.exit()
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

def generateXMLDump(config={}, titles=[], start=''):
    print 'Retrieving the XML for every page from "%s"' % (start and start or 'start')
    header = getXMLHeader(config=config)
    footer = '</mediawiki>\n' #new line at the end
    xmlfilename = '%s-%s-%s.xml' % (domain2prefix(domain=config['domain']), config['date'], config['curonly'] and 'current' or 'history')
    xmlfile = ''
    lock = True
    if start:
        #remove the last chunk of xml dump (it is probably incomplete)
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'r')
        xml = xmlfile.read()
        xmlfile.close()
        xml = xml.split('<title>%s</title>' % (start))[0]
        xml = '\n'.join(xml.split('\n')[:-2]) # [:-1] removing <page>\n tag
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'w')
        xmlfile.write('%s\n' % (xml))
        xmlfile.close()
    else:
        #requested complete xml dump
        lock = False
        xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'w')
        xmlfile.write(header)
        xmlfile.close()
    
    xmlfile = open('%s/%s' % (config['path'], xmlfilename), 'a')
    c = 1
    for title in titles:
        if title == start: #start downloading from start, included
            lock = False
        if lock:
            continue
        delay(config=config)
        if c % 10 == 0:
            print '    Downloaded %d pages' % (c)
        xml = getXMLPage(config=config, title=title)
        xml = cleanXML(xml=xml)
        xmlfile.write(xml)
        c += 1
    xmlfile.write(footer)
    xmlfile.close()
    print 'XML dump saved at...', xmlfilename

def saveTitles(config={}, titles=[]):
    #save titles in a txt for resume if needed
    titlesfilename = '%s-%s-titles.txt' % (domain2prefix(domain=config['domain']), config['date'])
    titlesfile = open('%s/%s' % (config['path'], titlesfilename), 'w')
    titles.append('--END--')
    titlesfile.write('\n'.join(titles))
    titlesfile.close()
    print 'Titles saved at...', titlesfilename

def saveImageFilenamesURL(config={}, images=[]):
    #save list of images and their urls
    imagesfilename = '%s-%s-images.txt' % (domain2prefix(domain=config['domain']), config['date'])
    imagesfile = open('%s/%s' % (config['path'], imagesfilename), 'w')
    imagesfile.write('\n'.join(['%s\t%s\t%s' % (filename, url, uploader) for filename, url, uploader in images]))
    imagesfile.write('\n--END--')
    imagesfile.close()
    print 'Image filenames and URLs saved at...', imagesfilename

def getImageFilenamesURL(config={}, start='!'):
    #fix start is only available if parsing from API, if not, reload all the list from special:imagelist is mandatory
    print 'Retrieving image filenames'
    r_next = r'(?<!&amp;dir=prev)&amp;offset=(?P<offset>\d+)&amp;' # (?<! http://docs.python.org/library/re.html
    images = []
    offset = '29990101000000' #january 1, 2999
    while offset:
        url = '%s?title=Special:Imagelist&limit=5000&offset=%s' % (config['domain'], offset)
        raw = urllib.urlopen(url).read()
        raw = cleanHTML(raw)
        #archiveteam <td class="TablePager_col_img_name"><a href="/index.php?title=File:Yahoovideo.jpg" title="File:Yahoovideo.jpg">Yahoovideo.jpg</a> (<a href="/images/2/2b/Yahoovideo.jpg">file</a>)</td>
        #wikanda <td class="TablePager_col_img_user_text"><a href="/w/index.php?title=Usuario:Fernandocg&amp;action=edit&amp;redlink=1" class="new" title="Usuario:Fernandocg (página no existe)">Fernandocg</a></td>
        m = re.compile(r'(?im)<td class="TablePager_col_img_name"><a href[^>]+title="[^:>]+:(?P<filename>[^>]+)">[^<]+</a>[^<]+<a href="(?P<url>[^>]+/[^>/]+)">[^<]+</a>[^<]+</td>\s*<td class="TablePager_col_img_user_text"><a[^>]+>(?P<uploader>[^<]+)</a></td>').finditer(raw)
        for i in m:
            url = i.group('url')
            if url[0] == '/' or not url.startswith('http://'): #relative URL
                if url[0] == '/': #it is added later
                    url = url[1:]
                domainalone = config['domain'].split('http://')[1].split('/')[0]
                url = 'http://%s/%s' % (domainalone, url)
            filename = re.sub('_', ' ', i.group('filename'))
            filename_ = re.sub(' ', '_', i.group('filename'))
            uploader = re.sub('_', ' ', i.group('uploader'))
            images.append([filename, url, uploader])
            #print filename, url
        
        if re.search(r_next, raw):
            offset = re.findall(r_next, raw)[0]
        else:
            offset = ''
    
    print '    Found %d images' % (len(images))
    images.sort()
    return images

def generateImageDump(config={}, images=[], start=''):
    #slurp all the images
    #save in a .tar?
    #tener en cuenta http://www.mediawiki.org/wiki/Manual:ImportImages.php
    #fix, download .desc ? YEP!
    #fix download the upload log too, for uploaders info and date
    print 'Retrieving images from "%s"' % (start and start or 'start')
    imagepath = '%s/images' % (config['path'])
    if os.path.isdir(imagepath):
        print 'It exists an images directory for this dump' #fix, resume?
    else:
        os.makedirs(imagepath)
    
    c = 0
    lock = True
    if not start:
        lock = False
    for filename, url, uploader in images:
        if filename == start: #start downloading from start, included
            lock = False
        if lock:
            continue
        delay(config=config)
        #saving file
        urllib.urlretrieve(url, '%s/%s' % (imagepath, filename)) 
        #saving description if any
        xmlfiledesc = getXMLFileDesc(config=config, title='Image:%s' % (filename)) 
        f = open('%s/%s.desc' % (imagepath, filename), 'w')
        if re.search(r'<text xml:space="preserve"/>', xmlfiledesc):
            #empty desc
            xmlfiledesc = ''
        elif re.search(r'<text xml:space="preserve">', xmlfiledesc):
            xmlfiledesc = xmlfiledesc.split('<text xml:space="preserve">')[1].split('</text>')[0]
            xmlfiledesc = re.sub('&lt;', '<', xmlfiledesc) # i guess only < > & need coversion http://www.w3schools.com/html/html_entities.asp
            xmlfiledesc = re.sub('&gt;', '>', xmlfiledesc)
            xmlfiledesc = re.sub('&amp;', '&', xmlfiledesc)
        else: #failure when retrieving desc?
            xmlfiledesc = ''
        f.write(xmlfiledesc)
        f.close()
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
    delay(config=config)

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
    
def welcome(config={}):
    print "-"*75
    print """Welcome to DumpGenerator 0.1 by WikiTeam (GPL v3)
More info at: http://code.google.com/p/wikiteam/"""
    print "-"*75

def bye(config={}):
    print "Your dump is in %s" % (config['path'])
    print "If you found any bug, report a new issue here (Gmail account required): http://code.google.com/p/wikiteam/issues/list"
    print "Good luck! Bye!"

def usage():
    print "Write a complete help"

def getParameters():
    config = {
        'curonly': False,
        'date': datetime.datetime.now().strftime('%Y%m%d'),
        'domain': '',
        'images': False,
        'logs': False,
        'xml': False,
        'namespaces': ['all'],
        'path': '',
        'threads': 1, #fix not coded yet
        'delay': 0,
    }
    other = {
        'resume': False,
    }
    #console params
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["h", "help", "path=", "domain=", "images", "logs", "xml", "curonly", "threads=", "resume", "delay=" ])
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
        elif o in ("--delay"):
            config["delay"] = int(a)
        else:
            assert False, "unhandled option"

    #missing mandatory params
    if not config["domain"] or \
       not re.search('/index\.php', config['domain']) or \
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
    
    #add http://
    if not config['domain'].startswith('http://'):
        config['domain'] = 'http://' + config['domain']
    
    #calculating path, if not defined by user with --path=
    config['path'] = './%s-%s-wikidump' % (domain2prefix(domain=config['domain']), config['date'])
    
    return config, other

def main():
    configfilename = 'config.txt'
    config, other = getParameters()
    welcome(config=config)
    
    #notice about wikipedia dumps
    if re.findall(r'(wikipedia|wikisource|wiktionary|wikibooks|wikiversity|wikimedia|wikispecies|wikiquote|wikinews)\.org', config['domain']):
        print 'DO NOT USE THIS SCRIPT TO DOWNLOAD WIKIMEDIA PROJECTS!\nDownload the dumps from http://download.wikimedia.org\nThanks!'
        sys.exit()
    
    print 'Analysing %s' % (config['domain'])
    
    #creating path or resuming if desired
    c = 2
    originalpath = config['path'] # to avoid concat blabla-2, blabla-2-3, and so on...
    while not other['resume'] and os.path.isdir(config['path']): #do not enter if resume is request from begining
        print '\nWarning!: "%s" path exists' % (config['path'])
        reply = raw_input('There is a dump in "%s", probably incomplete.\nIf you choose resume, to avoid conflicts, the parameters you have chosen in the current session will be ignored\nand the parameters available in "%s/%s" will be loaded.\nDo you want to resume ([yes, y], otherwise no)? ' % (config['path'], config['path'], configfilename))
        if reply.lower() in ['yes', 'y']:
            if not os.path.isfile('%s/%s' % (config['path'], configfilename)):
                print 'No config file found. I can\'t resume. Aborting.'
                sys.exit()
            print 'You have selected YES'
            other['resume'] = True
            break
        else:
            print 'You have selected NO'
        config['path'] = '%s-%d' % (originalpath, c)
        print 'Trying "%s"...' % (config['path'])
        c += 1

    if other['resume']:
        print 'Loading config file...'
        config = loadConfig(config=config, configfilename=configfilename)
    else:
        os.mkdir(config['path'])
        saveConfig(config=config, configfilename=configfilename)
    
    titles = []
    images = []
    if other['resume']:
        print 'Resuming previous dump process...'
        if config['xml']:
            #load titles
            lasttitle = ''
            try:
                f = open('%s/%s-%s-titles.txt' % (config['path'], domain2prefix(domain=config['domain']), config['date']), 'r')
                raw = f.read()
                titles = raw.split('\n')
                lasttitle = titles[-1]
                f.close()
            except:
                pass #probably file doesnot exists
            if lasttitle == '--END--':
                #titles list is complete
                print 'Title list was completed in the previous session'
            else:
                #start = last
                #remove complete namespaces and then getPageTitles(config=config, start=start)
                #titles += getPageTitles(config=config, start=last)
                print 'Title list is incomplete. Resuming...'
                #search last
                last = 'lastline'
                titles = titles[:-1] #removing last one, next line append from start, and start is inclusive
                titles += getPageTitles(config=config, start='!') #fix, try resume not reload entirely, change start='!' and develop the feature into getPageTitles()
                saveTitles(config=config, titles=titles)
            #checking xml dump
            f = open('%s/%s-%s-%s.xml' % (config['path'], domain2prefix(domain=config['domain']), config['date'], config['curonly'] and 'current' or 'history'), 'r')
            xml = f.read()
            f.close()
            if re.findall('</mediawiki>', xml):
                #xml dump is complete
                print 'XML dump was completed in the previous session'
            else:
                xmltitles = re.findall(r'<title>([^<]+)</title>', xml)
                lastxmltitle = ''
                if xmltitles:
                    lastxmltitle = xmltitles[-1]
                generateXMLDump(config=config, titles=titles, start=lastxmltitle)
        
        if config['images']:
            #load images
            lastimage = ''
            try:
                f = open('%s/%s-%s-images.txt' % (config['path'], domain2prefix(domain=config['domain']), config['date']), 'r')
                raw = f.read()
                lines = raw.split('\n')
                for l in lines:
                    if re.search(r'\t', l):
                        images.append(l.split('\t'))
                lastimage = lines[-1]
                f.close()
            except:
                pass #probably file doesnot exists
            if lastimage == '--END--':
                print 'Image list was completed in the previous session'
            else:
                print 'Image list is incomplete. Resuming...'
                images = images[:-1] #removing last one, next line append from start, and start is inclusive
                images += getImageFilenamesURL(config=config, start='!') #fix, develop start when using API, if using special:imagelist ignore start and reload all
                saveImageFilenamesURL(config=config, images=images)
            #checking images directory
            listdir = []
            try:
                listdir = os.listdir('%s/images' % (config['path']))
            except:
                pass #probably directory does not exist
            listdir.sort()
            complete = True
            lastfilename = ''
            lastfilename2 = ''
            c = 0
            for filename, url, uploader in images:
                if filename not in listdir:
                    complete = False
                    lastfilename2 = lastfilename
                    lastfilename = filename
                    break
                c +=1
            print '%d images were found in the directory from a previous session' % (c)
            lastfilename2 = lastfilename # we resume from previous image, which may be corrupted by the previous session ctrl-c or abort
            if complete:
                #image dump is complete
                print 'Image dump was completed in the previous session'
            else:
                generateImageDump(config=config, images=images, start=lastfilename)
        
        if config['logs']:
            #fix
            pass
    else:
        print 'Trying generating a new dump into a new directory...'
        if config['xml']:
            titles += getPageTitles(config=config, start='!')
            saveTitles(config=config, titles=titles)
            generateXMLDump(config=config, titles=titles)
        if config['images']:
            images += getImageFilenamesURL(config=config) #fix add start like above
            saveImageFilenamesURL(config=config, images=images)
            generateImageDump(config=config, images=images)
        if config['logs']:
            saveLogs(config=config)
    
    bye(config=config)

if __name__ == "__main__":
    main()
