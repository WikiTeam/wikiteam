#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2011-2012 WikiTeam
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

import os
import platform
import random
import re
from Tkinter import *
import ttk
import tkMessageBox
import thread
import time
import urllib
import webbrowser

import dumpgenerator

"""
TODO:

* basic: GUI to download just a wiki

* advanced: batch downloads, upload to Internet Archive or anywhere

"""

wikifarms = {
    'gentoo_wikicom': 'Gentoo Wiki',
    'opensuseorg': 'OpenSuSE',
    'referatacom': 'Referata',
    'shoutwikicom': 'ShoutWiki',
    'Unknown': 'Unknown',
    'wikanda': 'Wikanda',
    'wikifur': 'WikiFur',
    'wikitravelorg': 'WikiTravel',
    'wikkii': 'Wikkii',
}

NAME = 'WikiTeam tools'
VERSION = '0.1'
HOMEPAGE = 'https://code.google.com/p/wikiteam/'
LINUX = platform.system().lower() == 'linux'
PATH = os.path.dirname(__file__)
if PATH: os.chdir(PATH)

class App:
    def __init__(self, master):
        self.master = master
        self.dumps = []
        self.downloadpath = 'downloads'
        
        # interface elements
        #progressbar
        #self.value = 0
        #self.progressbar = ttk.Progressbar(self.master, orient=HORIZONTAL, value=self.value, mode='determinate')
        #self.progressbar.grid(row=0, column=0, columnspan=1, sticky=W+E)
        #self.run()
        
        #description
        self.desc = Label(self.master, text="", anchor=W, font=("Arial", 10))
        self.desc.grid(row=0, column=0, columnspan=1)
        #self.footer = Label(self.master, text="%s (version %s). This program is free software (GPL v3 or higher)" % (NAME, VERSION), anchor=W, justify=LEFT, font=("Arial", 10))
        #self.footer.grid(row=2, column=0, columnspan=1)
        
        #begin tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.grid(row=1, column=0, columnspan=1, sticky=W+E+N+S)
        self.frame1 = ttk.Frame(self.master)
        self.notebook.add(self.frame1, text='Dump generator')
        self.frame2 = ttk.Frame(self.master)
        self.notebook.add(self.frame2, text='Downloader')
        self.frame3 = ttk.Frame(self.master)
        self.notebook.add(self.frame3, text='Uploader')
        
        #dump generator tab (1)
        self.labelframe11 = LabelFrame(self.frame1, text="Single download")
        self.labelframe11.grid(row=0, column=0)
        self.labelframe12 = LabelFrame(self.frame1, text="Batch download")
        self.labelframe12.grid(row=1, column=0)
        #single download labelframe
        self.label11 = Label(self.labelframe11, text="Wiki URL:")
        self.label11.grid(row=0, column=0)
        self.entry11 = Entry(self.labelframe11, width=40)
        self.entry11.grid(row=0, column=1)
        self.entry11.bind('<Return>', (lambda event: self.checkURL()))
        self.optionmenu11var = StringVar(self.labelframe11)
        self.optionmenu11var.set("api.php")
        self.optionmenu11 = OptionMenu(self.labelframe11, self.optionmenu11var, self.optionmenu11var.get(), "index.php")
        self.optionmenu11.grid(row=0, column=2)
        self.button11 = Button(self.labelframe11, text="Check", command=lambda: thread.start_new_thread(self.checkURL, ()), width=5)
        self.button11.grid(row=0, column=3)
        #batch download labelframe
        self.label12 = Label(self.labelframe12, text="Wiki URLs:")
        self.label12.grid(row=0, column=0)
        self.text11 = Text(self.labelframe12, width=70, height=20)
        self.text11.grid(row=0, column=1)
        
        #downloader tab (2)
        self.label25var = StringVar(self.frame2)
        self.label25var.set("Available dumps: 0 (0.0 MB)")
        self.label25 = Label(self.frame2, textvariable=self.label25var, width=27, anchor=W)
        self.label25.grid(row=0, column=0, columnspan=2)
        self.label26var = StringVar(self.frame2)
        self.label26var.set("Downloaded: 0 (0.0 MB)")
        self.label26 = Label(self.frame2, textvariable=self.label26var, background='lightgreen', width=27, anchor=W)
        self.label26.grid(row=0, column=2, columnspan=2)
        self.label27var = StringVar(self.frame2)
        self.label27var.set("Not downloaded: 0 (0.0 MB)")
        self.label27 = Label(self.frame2, textvariable=self.label27var, background='white', width=27, anchor=W)
        self.label27.grid(row=0, column=4, columnspan=2)
        
        self.label21 = Label(self.frame2, text="Filter by wikifarm:", width=15, anchor=W)
        self.label21.grid(row=1, column=0)
        self.optionmenu21var = StringVar(self.frame2)
        self.optionmenu21var.set("all")
        self.optionmenu21 = OptionMenu(self.frame2, self.optionmenu21var, self.optionmenu21var.get(), "Gentoo Wiki", "OpenSuSE", "Referata", "ShoutWiki", "Unknown", "Wikanda", "WikiFur", "WikiTravel", "Wikkii")
        self.optionmenu21.grid(row=1, column=1)
        
        self.label22 = Label(self.frame2, text="Filter by size:", width=15, anchor=W)
        self.label22.grid(row=1, column=2)
        self.optionmenu22var = StringVar(self.frame2)
        self.optionmenu22var.set("all")
        self.optionmenu22 = OptionMenu(self.frame2, self.optionmenu22var, self.optionmenu22var.get(), "KB", "MB", "GB", "TB")
        self.optionmenu22.grid(row=1, column=3)
        
        self.label23 = Label(self.frame2, text="Filter by date:", width=15, anchor=W)
        self.label23.grid(row=1, column=4)
        self.optionmenu23var = StringVar(self.frame2)
        self.optionmenu23var.set("all")
        self.optionmenu23 = OptionMenu(self.frame2, self.optionmenu23var, self.optionmenu23var.get(), "2011", "2012")
        self.optionmenu23.grid(row=1, column=5)
        
        self.label24 = Label(self.frame2, text="Filter by mirror:")
        self.label24.grid(row=1, column=6)
        self.optionmenu24var = StringVar(self.frame2)
        self.optionmenu24var.set("all")
        self.optionmenu24 = OptionMenu(self.frame2, self.optionmenu24var, self.optionmenu24var.get(), "Google Code", "Internet Archive", "ScottDB")
        self.optionmenu24.grid(row=1, column=7)
        
        self.button23 = Button(self.frame2, text="Filter!", command=self.filterAvailableDumps, width=7)
        self.button23.grid(row=1, column=8)
        
        self.treescrollbar = Scrollbar(self.frame2)
        self.treescrollbar.grid(row=2, column=9, sticky=W+E+N+S)
        columns = ('dump', 'wikifarm', 'size', 'date', 'mirror', 'status')
        self.tree = ttk.Treeview(self.frame2, height=20, columns=columns, show='headings', yscrollcommand=self.treescrollbar.set)
        self.treescrollbar.config(command=self.tree.yview)
        self.tree.column('dump', width=495, minwidth=200, anchor='center')
        self.tree.heading('dump', text='Dump')
        self.tree.column('wikifarm', width=100, minwidth=100, anchor='center')
        self.tree.heading('wikifarm', text='Wikifarm')
        self.tree.column('size', width=100, minwidth=100, anchor='center')
        self.tree.heading('size', text='Size')
        self.tree.column('date', width=100, minwidth=100, anchor='center')
        self.tree.heading('date', text='Date')
        self.tree.column('mirror', width=120, minwidth=120, anchor='center')
        self.tree.heading('mirror', text='Mirror')
        self.tree.column('status', width=120, minwidth=120, anchor='center')
        self.tree.heading('status', text='Status')
        self.tree.grid(row=2, column=0, columnspan=9, sticky=W+E+N+S)
        [self.tree.heading(column, text=column, command=lambda: self.treeSortColumn(column=column, reverse=False)) for column in columns]        
        #self.tree.bind("<Double-1>", (lambda: thread.start_new_thread(self.downloadDump, ())))
        self.tree.tag_configure('downloaded', background='lightgreen')
        self.tree.tag_configure('nodownloaded', background='white')
        self.button21 = Button(self.frame2, text="Load available dumps", command=lambda: thread.start_new_thread(self.loadAvailableDumps, ()), width=15)
        self.button21.grid(row=3, column=0)
        self.button23 = Button(self.frame2, text="Download selection", command=lambda: thread.start_new_thread(self.downloadDump, ()), width=15)
        self.button23.grid(row=3, column=4)
        self.button22 = Button(self.frame2, text="Clear list", command=self.deleteAvailableDumps, width=10)
        self.button22.grid(row=3, column=8, columnspan=2)
        
        #uploader tab (3)
        self.label31 = Label(self.frame3, text="todo...")
        self.label31.grid(row=0, column=0)
        #end tabs
        
        #statusbar
        self.status = Label(self.master, text="Welcome to WikiTeam tools. What do you want to do today?", bd=1, background='grey', justify=LEFT, relief=SUNKEN)
        self.status.grid(row=4, column=0, columnspan=10, sticky=W+E)
        
        #begin menu
        menu = Menu(self.master)
        master.config(menu=menu)

        #file menu
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Preferences", command=self.callback)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=askclose)
        
        #help menu
        helpmenu = Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About", command=self.callback)
        helpmenu.add_command(label="Help index", command=self.callback)
        helpmenu.add_command(label="WikiTeam homepage", command=lambda: webbrowser.open_new_tab(HOMEPAGE))
        #end menu
    
    def checkURL(self):
        if re.search(ur"(?im)^https?://[^/]+\.[^/]+/", self.entry11.get()): #well-constructed URL?, one dot at least, aaaaa.com, but bb.aaaaa.com is allowed too
            if self.optionmenu11var.get() == 'api.php':
                self.msg('Please wait... Checking api.php...')
                if dumpgenerator.checkAPI(self.entry11.get()):
                    self.entry11.config(background='lightgreen')
                    self.msg('api.php is correct!', level='ok')
                else:
                    self.entry11.config(background='red')
                    self.msg('api.php is incorrect!', level='error')
            elif self.optionmenu11var.get() == 'index.php':
                self.msg('Please wait... Checking index.php...')
                if dumpgenerator.checkIndexphp(self.entry11.get()):
                    self.entry11.config(background='lightgreen')
                    self.msg('index.php is OK!', level='ok')
                else:
                    self.entry11.config(background='red')
                    self.msg('index.php is incorrect!', level='error')
        else:
            tkMessageBox.showerror("Error", "You have to write a correct api.php or index.php URL.")
    
    def sumSizes(self, sizes):
        total = 0
        for size in sizes:
            if size.endswith('KB'):
                total += float(size.split(' ')[0])
            elif size.endswith('MB'):
                total += float(size.split(' ')[0])*1024
            elif size.endswith('GB'):
                total += float(size.split(' ')[0])*1024*1024
            elif size.endswith('TB'):
                total += float(size.split(' ')[0])*1024*1024*1024
            else:
                total += size
        return total/1024 #MB
    
    def run(self):
        for i in range(10):
            time.sleep(0.1)
            self.value += 10
        
        """
        #get parameters selected
        params = ['--api=http://www.archiveteam.org/api.php', '--xml']

        #launch dump
        dumpgenerator.main(params=params)

        #check dump
        """
    
    def msg(self, msg='', level=''):
        levels = { 'ok': 'lightgreen', 'warning': 'yellow', 'error': 'red' }
        if levels.has_key(level.lower()):
            print '%s: %s' % (level.upper(), msg)
            self.status.config(text=msg, background=levels[level.lower()])
        else:
            print msg
            self.status.config(text=msg, background='grey')
    
    def treeSortColumn(self, column, reverse=False):
        l = [(self.tree.set(i, column), i) for i in self.tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, i) in enumerate(l):
            self.tree.move(i, '', index)
        self.tree.heading(column, command=lambda: self.treeSortColumn(column=column, reverse=not reverse))
    
    def downloadProgress(self, block_count, block_size, total_size):
        try:
            total_mb = total_size/1024/1024.0
            downloaded = block_count *(block_size/1024/1024.0)
            percent = downloaded/(total_mb/100.0)
            if not random.randint(0,10):
                msg = "%.1f MB of %.1f MB downloaded (%.1f%%)" % (downloaded, total_mb, percent <= 100 and percent or 100)
                self.msg(msg, level='ok')
            #sys.stdout.write("%.1f MB of %.1f MB downloaded (%.2f%%)" %(downloaded, total_mb, percent))
            #sys.stdout.flush()
        except:
            pass
    
    def downloadDump(self, event=None):
        items = self.tree.selection()
        if items:
            if not os.path.exists(self.downloadpath):
                os.makedirs(self.downloadpath)
            c = 0
            d = 0
            for item in items:
                filepath = self.downloadpath and self.downloadpath + '/' + self.dumps[int(item)][0] or self.dumps[int(item)][0]
                if os.path.exists(filepath):
                    self.msg('That dump was downloaded before', level='ok')
                    d += 1
                else:
                    self.msg("[%d of %d] Downloading %s from %s" % (c+1, len(items), self.tree.item(item,"text"), self.dumps[int(item)][5]))
                    f = urllib.urlretrieve(self.dumps[int(item)][5], filepath, reporthook=self.downloadProgress)
                    msg='%s size is %s bytes large. Download successful!' % (self.dumps[int(item)][0], os.path.getsize(filepath))
                    self.msg(msg=msg, level='ok')
                    c += 1
                self.dumps[int(item)] = self.dumps[int(item)][:6] + ['True']
            if c + d == len(items):
                self.msg('Downloaded %d of %d%s.' % (c, len(items), d and ' (and %d were previously downloaded)' % (d) or ''), level='ok')
            else:
                self.msg('Problems in %d dumps. Downloaded %d of %d (and %d were previously downloaded).' % (len(items)-(c+d), c, len(items), d), level='error')
        else:
            tkMessageBox.showerror("Error", "You have to select some dumps to download.")
        self.clearAvailableDumps()
        self.showAvailableDumps()
        self.filterAvailableDumps()
    
    def deleteAvailableDumps(self):
        #really delete dump list and clear tree
        self.clearAvailableDumps()
        self.dumps = [] #reset list
    
    def clearAvailableDumps(self):
        #clear tree
        for i in range(len(self.dumps)):
            self.tree.delete(str(i))
    
    def showAvailableDumps(self):
        c = 0
        for filename, wikifarm, size, date, mirror, url, downloaded in self.dumps:
            self.tree.insert('', 'end', str(c), text=filename, values=(filename, wikifarm, size, date, mirror, downloaded and 'Downloaded' or 'Not downloaded'), tags=(downloaded and 'downloaded' or 'nodownloaded',))
            c += 1
        
    def filterAvailableDumps(self):
        self.clearAvailableDumps()
        self.showAvailableDumps()
        sizes = []
        downloadedsizes = []
        nodownloadedsizes = []
        for i in range(len(self.dumps)):
            if (self.optionmenu21var.get() == 'all' and self.optionmenu22var.get() == 'all' and self.optionmenu23var.get() == 'all' and self.optionmenu24var.get() == 'all'):
                sizes.append(self.dumps[i][2])
                if self.dumps[i][6]:
                    downloadedsizes.append(self.dumps[i][2])
                else:
                    nodownloadedsizes.append(self.dumps[i][2])
            elif (self.optionmenu21var.get() != 'all' and not self.optionmenu21var.get() == self.dumps[i][1]) or \
                (self.optionmenu22var.get() != 'all' and not self.optionmenu22var.get() in self.dumps[i][2]) or \
                (self.optionmenu23var.get() != 'all' and not self.optionmenu23var.get() in self.dumps[i][3]) or \
                (self.optionmenu24var.get() != 'all' and not self.optionmenu24var.get() in self.dumps[i][4]):
                self.tree.detach(str(i)) #hide this item
                sizes.append(self.dumps[i][2])
                if self.dumps[i][6]:
                    downloadedsizes.append(self.dumps[i][2])
                else:
                    nodownloadedsizes.append(self.dumps[i][2])
        self.label25var.set("Available dumps: %d (%.1f MB)" % (len(sizes), self.sumSizes(sizes)))
        self.label26var.set("Downloaded: %d (%.1f MB)" % (len(downloadedsizes), self.sumSizes(downloadedsizes)))
        self.label27var.set("Not downloaded: %d (%.1f MB)" % (len(nodownloadedsizes), self.sumSizes(nodownloadedsizes)))
    
    def isDumpDownloaded(self, filename):
        #improve, size check or md5sum?
        if filename:
            filepath = self.downloadpath and self.downloadpath + '/' + filename or filename
            if os.path.exists(filepath):
                return True
        
        """estsize = os.path.getsize(filepath)
                c = 0
                while int(estsize) >= 1024:
                    estsize = estsize/1024.0
                    c += 1
                estsize = '%.1f %s' % (estsize, ['', 'KB', 'MB', 'GB', 'TB'][c])"""
        
        return False
    
    def loadAvailableDumps(self):
        if self.dumps:
            self.deleteAvailableDumps()
        iaregexp = ur'/download/[^/]+/(?P<filename>[^>]+\.7z)">\s*(?P<size>[\d\.]+ (?:KB|MB|GB|TB))\s*</a>'
        self.urls = [
            ['Google Code', 'https://code.google.com/p/wikiteam/downloads/list?num=5000&start=0', ur'(?im)detail\?name=(?P<filename>[^&]+\.7z)&amp;can=2&amp;q=" style="white-space:nowrap">\s*(?P<size>[\d\.]+ (?:KB|MB|GB|TB))\s*</a></td>'],
            ['Internet Archive', 'http://www.archive.org/details/referata.com-20111204', iaregexp],
            ['Internet Archive', 'http://www.archive.org/details/WikiTeamMirror', iaregexp],
            ['ScottDB', 'http://mirrors.sdboyd56.com/WikiTeam/', ur'<a href="(?P<filename>[^>]+\.7z)">(?P<size>[\d\.]+ (?:KB|MB|GB|TB))</a>'],
        ]
        wikifarms_r = re.compile(ur"(%s)" % ('|'.join(wikifarms.keys())))
        c = 0
        for mirror, url, regexp in self.urls:
            print 'Loading data from', mirror, url
            self.msg(msg='Please wait... Loading data from %s %s' % (mirror, url))
            f = urllib.urlopen(url)
            m = re.compile(regexp).finditer(f.read())
            for i in m:
                filename = i.group('filename')
                wikifarm = 'Unknown'
                if re.search(wikifarms_r, filename):
                    wikifarm = re.findall(wikifarms_r, filename)[0]
                wikifarm = wikifarms[wikifarm]
                size = i.group('size')
                date = 'Unknown'
                if re.search(ur"\-(\d{8})[\.-]", filename):
                    date = re.findall(ur"\-(\d{4})(\d{2})(\d{2})[\.-]", filename)[0]
                    date = '%s-%s-%s' % (date[0], date[1], date[2])
                elif re.search(ur"\-(\d{4}\-\d{2}\-\d{2})[\.-]", filename):
                    date = re.findall(ur"\-(\d{4}\-\d{2}\-\d{2})[\.-]", filename)[0]
                downloadurl = ''
                if mirror == 'Google Code':
                    downloadurl = 'https://wikiteam.googlecode.com/files/' + filename
                elif mirror == 'Internet Archive':
                    downloadurl = re.sub(ur'/details/', ur'/download/', url) + '/' + filename
                elif mirror == 'ScottDB':
                    downloadurl = url + '/' + filename
                downloaded = self.isDumpDownloaded(filename)
                self.dumps.append([filename, wikifarm, size, date, mirror, downloadurl, downloaded])
        self.dumps.sort()
        self.showAvailableDumps()
        self.filterAvailableDumps()
        self.msg(msg='Loaded available dumps!', level='ok')
    
    def callback(self):
        self.msg("Feature not implemented for the moment. Contributions are welcome.", level='warning')
    
def askclose():
    if tkMessageBox.askokcancel("Quit", "Do you really wish to exit?"):
        root.destroy()

if __name__ == "__main__":
    root = Tk()
    width = 1050
    height = 560
    # calculate position x, y
    x = (root.winfo_screenwidth()/2) - (width/2) 
    y = (root.winfo_screenheight()/2) - (height/2)
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))
    root.title('%s (version %s)' % (NAME, VERSION))
    root.protocol("WM_DELETE_WINDOW", askclose)
    #logo
    #imagelogo = PhotoImage(file = 'logo.gif')
    #labellogo = Label(root, image=imagelogo)
    #labellogo.grid(row=0, column=0, rowspan=3, sticky=W)
    app = App(root)
    root.mainloop()
