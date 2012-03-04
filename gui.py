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

NAME = 'WikiTeam tools'
VERSION = '0.1'
HOMEPAGE = 'https://code.google.com/p/wikiteam/'
LINUX = platform.system().lower() == 'linux'
PATH = os.path.dirname(__file__)
if PATH: os.chdir(PATH)

class App:
    def __init__(self, master):
        self.master = master

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
        
        self.notebook = ttk.Notebook(self.master)
        self.notebook.grid(row=1, column=0, columnspan=1, sticky=W+E+N+S)
        self.frame1 = ttk.Frame(self.master)
        self.notebook.add(self.frame1, text='Dump generator')
        self.frame2 = ttk.Frame(self.master)
        self.notebook.add(self.frame2, text='Downloader')
        self.frame3 = ttk.Frame(self.master)
        self.notebook.add(self.frame3, text='Uploader')
        self.tree = ttk.Treeview(self.frame2, columns=('dump', 'wikifarm', 'size', 'date'), show='headings')
        self.tree.column('dump', width=350, minwidth=350, anchor='center')
        self.tree.heading('dump', text='Dump')
        self.tree.column('wikifarm', width=100, minwidth=100, anchor='center')
        self.tree.heading('wikifarm', text='Wikifarm')
        self.tree.column('size', width=100, minwidth=100, anchor='center')
        self.tree.heading('size', text='Size')
        self.tree.column('date', width=100, minwidth=100, anchor='center')
        self.tree.heading('date', text='Date')
        self.tree.grid(row=0, column=0, columnspan=1, sticky=W+E+N+S)
        
        #create a menu
        menu = Menu(self.master)
        master.config(menu=menu)

        #begin file
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Preferences", command=self.callback)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=askclose)
        
        #help
        helpmenu = Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About", command=self.callback)
        helpmenu.add_command(label="Help index", command=self.callback)
        helpmenu.add_command(label="WikiTeam homepage", command=lambda: webbrowser.open_new_tab(HOMEPAGE))
        
        f = urllib.urlopen('https://code.google.com/p/wikiteam/downloads/list?num=5000&start=0') #http://www.archive.org/details/referata.com-20111204
        m = re.findall(ur"(?im)detail\?name=([^&]+)&amp;can=2&amp;q=\" style=\"white-space:nowrap\">\s*([\d\.]+ (?:KB|MB))\s*</a></td>", f.read())
        dumps = []
        for i in m:
            name = i[0]
            wikifarm = 'Unknown'
            size = i[1]
            date = 'Unknown'
            if re.search(ur"\-(\d{8})\-", name):
                date = re.findall(ur"\-(\d{4})(\d{2})(\d{2})\-", name)[0]
                date = '%s-%s-%s' % (date[0], date[1], date[2])
            if re.search(ur"(opensuseorg|referatacom|wikitravelorg)[_-]", name):
                wikifarm = re.findall(ur"(gentoo_wikicom|opensuseorg|referatacom|wikitravelorg)[_-]", name)[0]
            dumps.append([name, wikifarm, size, date])
        for name, wikifarm, size, date in dumps:
            self.tree.insert('', 'end', text=i, values=(name, wikifarm, size, date))
        
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
    def callback(self):
        self.setStatus("Feature not implemented for the moment. Contributions are welcome.")
    
def askclose():
    if tkMessageBox.askokcancel("Quit", "Do you really wish to exit?"):
        root.destroy()

if __name__ == "__main__":
    root = Tk()
    root.geometry('800x600+200+100')
    root.title('%s (version %s)' % (NAME, VERSION))
    root.protocol("WM_DELETE_WINDOW", askclose)
    #logo
    #imagelogo = PhotoImage(file = 'logo.gif')
    #labellogo = Label(root, image=imagelogo)
    #labellogo.grid(row=0, column=0, rowspan=3, sticky=W)
    app = App(root)
    root.mainloop()
