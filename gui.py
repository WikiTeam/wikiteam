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
import re
from Tkinter import *
import ttk
import tkMessageBox
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
    '': 'Unknown',
    'opensuseorg': 'OpenSuSE',
    'referatacom': 'Referata',
    'Unknown': 'Unknown',
    'wikitravelorg': 'WikiTravel',
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
        
        # interface elements
        #progressbar
        #self.value = 0
        #self.progressbar = ttk.Progressbar(self.master, orient=HORIZONTAL, value=self.value, mode='determinate')
        #self.progressbar.grid(row=0, column=0, columnspan=1, sticky=W+E)
        #self.run()
        
        #description
        self.desc = Label(self.master, text="Welcome to WikiTeam tools. What do you want to do today? You can:\n1) Generate a new wiki backup, 2) Download available dumps, 3) Upload your dump anywhere.\nThanks for helping to preserve wikis.", anchor=W, font=("Arial", 10))
        self.desc.grid(row=0, column=0, columnspan=1)
        self.footer = Label(self.master, text="%s (version %s). This program is free software (GPL v3 or higher)" % (NAME, VERSION), anchor=W, justify=LEFT, font=("Arial", 10))
        self.footer.grid(row=2, column=0, columnspan=1)
        
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
        
        #downloader tab (2)
        self.label21 = Label(self.frame2, text="Filter by wikifarm:")
        self.label21.grid(row=0, column=0)
        self.optionmenu21var = StringVar(self.frame2)
        self.optionmenu21var.set("all")
        self.optionmenu21 = OptionMenu(self.frame2, self.optionmenu21var, "all", "Referata", "OpenSuSE", "Unknown", "WikiTravel")
        self.optionmenu21.grid(row=0, column=1)
        
        self.label22 = Label(self.frame2, text="Filter by size:")
        self.label22.grid(row=0, column=2)
        self.optionmenu22var = StringVar(self.frame2)
        self.optionmenu22var.set("all")
        self.optionmenu22 = OptionMenu(self.frame2, self.optionmenu22var, "all", "KB", "MB", "GB", "TB")
        self.optionmenu22.grid(row=0, column=3)
        
        self.label23 = Label(self.frame2, text="Filter by date:")
        self.label23.grid(row=0, column=4)
        self.optionmenu23var = StringVar(self.frame2)
        self.optionmenu23var.set("all")
        self.optionmenu23 = OptionMenu(self.frame2, self.optionmenu23var, "all", "2011", "2012")
        self.optionmenu23.grid(row=0, column=5)
        
        self.label24 = Label(self.frame2, text="Filter by mirror:")
        self.label24.grid(row=0, column=6)
        self.optionmenu24var = StringVar(self.frame2)
        self.optionmenu24var.set("all")
        self.optionmenu24 = OptionMenu(self.frame2, self.optionmenu24var, "all", "Google Code", "Internet Archive")
        self.optionmenu24.grid(row=0, column=7)
        
        self.button23 = Button(self.frame2, text="Apply filter", command=self.filterAvailableDumps, width=10)
        self.button23.grid(row=0, column=8)
        
        self.treescrollbar = Scrollbar(self.frame2)
        self.treescrollbar.grid(row=1, column=9, sticky=W+E+N+S)
        self.tree = ttk.Treeview(self.frame2, height=20, columns=('dump', 'wikifarm', 'size', 'date', 'mirror'), show='headings', yscrollcommand=self.treescrollbar.set)
        self.treescrollbar.config(command=self.tree.yview)
        self.tree.column('dump', width=470, minwidth=470, anchor='center')
        self.tree.heading('dump', text='Dump')
        self.tree.column('wikifarm', width=100, minwidth=100, anchor='center')
        self.tree.heading('wikifarm', text='Wikifarm')
        self.tree.column('size', width=100, minwidth=100, anchor='center')
        self.tree.heading('size', text='Size')
        self.tree.column('date', width=100, minwidth=100, anchor='center')
        self.tree.heading('date', text='Date')
        self.tree.column('mirror', width=120, minwidth=120, anchor='center')
        self.tree.heading('mirror', text='Mirror')
        self.tree.grid(row=1, column=0, columnspan=9, sticky=W+E+N+S)
        self.button21 = Button(self.frame2, text="Load available dumps", command=self.loadAvailableDumps, width=15)
        self.button21.grid(row=2, column=0)
        self.button22 = Button(self.frame2, text="Clear list", command=self.deleteAvailableDumps, width=10)
        self.button22.grid(row=2, column=8, columnspan=2)
        
        #uploader tab (3)
        
        #end tabs
        
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
        for filename, wikifarm, size, date, mirror in self.dumps:
            self.tree.insert('', 'end', str(c), text=filename, values=(filename, wikifarm, size, date, mirror))
            c += 1
        
    def filterAvailableDumps(self):
        self.clearAvailableDumps()
        self.showAvailableDumps()
        for i in range(len(self.dumps)):
            if (self.optionmenu21var.get() != 'all' and not self.optionmenu21var.get() == self.dumps[i][1]) or \
                (self.optionmenu22var.get() != 'all' and not self.optionmenu22var.get() in self.dumps[i][2]) or \
                (self.optionmenu23var.get() != 'all' and not self.optionmenu23var.get() in self.dumps[i][3]) or \
                (self.optionmenu24var.get() != 'all' and not self.optionmenu24var.get() in self.dumps[i][4]):
                self.tree.detach(str(i))
    
    def loadAvailableDumps(self):
        if self.dumps:
            self.deleteAvailableDumps()
        iaregexp = ur'/download/[^/]+/(?P<filename>[^>]+\.7z)">\s*(?P<size>[\d\.]+ (?:KB|MB|GB|TB))\s*</a>'
        self.urls = [
            ['Google Code', 'https://code.google.com/p/wikiteam/downloads/list?num=5000&start=0', ur'(?im)detail\?name=(?P<filename>[^&]+\.7z)&amp;can=2&amp;q=" style="white-space:nowrap">\s*(?P<size>[\d\.]+ (?:KB|MB|GB|TB))\s*</a></td>'],
            ['Internet Archive', 'http://www.archive.org/details/referata.com-20111204', iaregexp],
            ['Internet Archive', 'http://www.archive.org/details/WikiTeamMirror', iaregexp],
        ]
        c = 0
        for mirror, url, regexp in self.urls:
            print 'Loading data from', mirror, url
            f = urllib.urlopen(url)
            m = re.compile(regexp).finditer(f.read())
            for i in m:
                filename = i.group('filename')
                wikifarm = 'Unknown'
                if re.search(ur"(opensuseorg|referatacom|wikitravelorg)[_-]", filename):
                    wikifarm = re.findall(ur"(gentoo_wikicom|opensuseorg|referatacom|wikitravelorg)[_-]", filename)[0]
                wikifarm = wikifarms[wikifarm]
                size = i.group('size')
                date = 'Unknown'
                if re.search(ur"\-(\d{8})\-", filename):
                    date = re.findall(ur"\-(\d{4})(\d{2})(\d{2})\-", filename)[0]
                    date = '%s-%s-%s' % (date[0], date[1], date[2])
                self.dumps.append([filename, wikifarm, size, date, mirror])
        self.showAvailableDumps()
        self.filterAvailableDumps()
    
    def callback(self):
        self.setStatus("Feature not implemented for the moment. Contributions are welcome.")
    
def askclose():
    if tkMessageBox.askokcancel("Quit", "Do you really wish to exit?"):
        root.destroy()

if __name__ == "__main__":
    root = Tk()
    width = 930
    height = 600
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
