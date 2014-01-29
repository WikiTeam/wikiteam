# -*- coding: utf-8 -*-

# Copyright (C) 2013 Hydriz Scholz
# Copyright (C) 2014 WikiTeam
#
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
# You should have received a copy of the GNU General Public License along
# with this program. If not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA, or visit
# <http://www.gnu.org/copyleft/gpl.html>

#######################################################################
# dumpgenerator.py is a script to generate backups of MediaWiki wikis #
# To learn more, read the documentation:							  #
#		http://code.google.com/p/wikiteam/wiki/NewTutorial 			  #
#######################################################################

# For developers:
# * All functions and classes are displayed in alphabetical order for easier accessibility.
# * Script exit codes reference:
#  * 0 - Script ran well without problems
#  * 1 - Script failed due to user's incorrect use
#  * 2 - Script failed due to destination server issue
# * For testing purposes, add the --debug parameter and edit DumpGenerator.debug() accordingly.

######
# TODO LIST
# 0. Download index.html and Special:Version.html
# 1. Index.php support.
# 2. Special:Log pages support
# 3. GUI (Question and Answer if no parameters are given)
# 4. Resuming of dump
# 5. Place the images in various folders so as to avoid hitting the limit of number of files in a directory
# 6. Speed up the script. A run with --xml --images on test.wikidata.org came up with 9 min 23 sec on 2.0 and 3 min 58 sec on 1.0

# WHAT IS WORKING
# 1. XML dumping
# 2. Complete dumping using API (except for --logs)
# 3. Automatic updating
# 4. Dumping of XML based on a list of titles
# 5. Integrity check for XML dump

import datetime
import getopt
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib
import urllib2
import xml.etree.ElementTree as ElementTree

class DumpGenerator:
	"""
	The main class that powers and operates everything else
	"""
	def __init__(self):
		"""
		Main constructor class for DumpGenerator, registers important variables too.
		"""
		self.Version = "2.0"
		self.revision = "1"
		# Provide a cool user-agent to hide the fact that this is a script
		self.UserAgent = "Mozilla/5.0 (X11; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0"
		self.useAPI = False
		self.useIndex = False
		self.prefix = ""
		self.domain = ""
		self.tasklist = []
		self.configfile = "config.json"
		self.configoptions = {
			"date": "",
			"useAPI": False,
			"useIndex": False,
			"urltoapi": "",
			"urltoindex": "",
			"images": False,
			"logs": False,
			"xml": False,
			"curonly": False,
			"exnamespaces": "",
			"titlesonly": False
		}

		# Basic metadata
		self.date = datetime.datetime.now().strftime('%Y%m%d')

		# Important URLs
		self.urltoapi = ""
		self.urltoindex = ""

		# Type of dump to generate
		self.images = False
		self.logs = False
		self.xml = False

		# Resuming of previous dump
		self.resume = False
		self.path = ""

		# Additional information for XML
		self.curonly = False
		self.exnamespaces = ""
		self.titlesonly = False
		self.titles = ""

		# Others
		self.cookies = ""
		self.delay = 0
		self.debugmode = False
		self.nolog = False
		self.autonomous = False

		# Short options: string (no commas), long options: array
		# More information about these options are at self.help()
		self.shortoptions = "hv"
		self.longoptions = [ "help", "api=", "index=", "curonly", "images", "logs", "xml", "auto", "delay=", "cookies=", "exnamespaces=", "resume", "path=", "debug", "nolog", "titlesonly", "titles=" ]

	def bye(self):
		"""
		Bid farewell to the user at the very end of the script when everything 
		has been successful.

		Returns: Goodbye message.
		"""
		message = """---> Congratulations! Your dump is complete <---
If you have suggestions, file a new issue here (Google account required): http://code.google.com/p/wikiteam/issues/list
If this is a public wiki, do consider publishing this dump so others can benefit from it. Follow the steps as explained in http://code.google.com/p/wikiteam/wiki/NewTutorial#Publishing_the_dump or contact us at http://code.google.com/p/wikiteam.
Thank you for using DumpGenerator %s by WikiTeam, good bye!""" % ( self.Version )
		return message

	def checkAPI(self):
		"""
		Checks the validity of the api.php.
		"""
		query = {
			"meta": "siteinfo",
			"siprop": "general" }
		sitestats = json.loads( RequestAPI.query( query ) )
		try:
			if ( sitestats[ "query" ][ "general" ][ "server" ] in self.urltoapi ):
				return True
		except:
			try:
				if ( sitestats[ "error" ][ "code" ] == "readapidenied" ) and ( self.cookies == "" ):
					Output.warn( "The wiki is private and we do not have proper authentication information!" )
					return False
			except:
				Output.warn( "This api.php seems weird or is not valid." )
				return False

	def checkIndex(self):
		"""
		Checks the validity of the index.php.
		"""
		# TODO: Screen scraping is involved here, need backward compact for older version of MediaWiki.
		parameters = { "title": "Special:Version" }
		request = RequestIndex.query( parameters )
		# Since we are at Special:Version, we should not be getting Special:BadTitle unless we are not logged in
		if ( re.search( r'(Special:Badtitle</a>)', request ) ) and ( self.cookies == "" ):
			Output.error( "The wiki is private and we do not have proper authentication information!" )
			sys.exit(1)

		# Check for some tags within the Special:Version page, must be language-independent
		if ( re.search( r'(<h2 id="mw-version-license">|meta name="generator" content="MediaWiki)', request ) ):
			return True

	def debug(self):
		"""
		A temporary debug mode for testing purposes.
		REMOVE WHEN COMPLETE!
		"""
		print "DEBUG MODE ON"
		print "Date: %s" % (self.date)
		print "URL to api.php: %s" % (self.urltoapi)
		print "URL to index.php: %s" % (self.urltoindex)
		print "Current revision only: %s" % (self.curonly)
		print "Image dump: %s" % (self.images)
		print "Log dump: %s" % (self.logs)
		print "XML dump: %s" % (self.xml)
		print "Resume: %s" % (self.resume)
		print "Path for resuming: %s" % (self.path)
		print "Delay: %s" % (self.delay)
		print "Cookies file: %s" % (self.cookies)
		print "Excluded namespaces: %s" % (self.exnamespaces)
		print "Debug mode on: %s" % (self.debugmode)
		self.tasklist = sorted( self.tasklist )
		for task in self.tasklist:
			if ( task == "axml" ):
				DumpXML.run()
			elif ( task == "bimages" ):
				DumpImages.run()
			elif ( task == "clogs" ):
				DumpLogs.run()
		sys.exit(0)

	def downloadHtmlPages(self):
		"""
		Downloads the HTML pages such as the main page and Special:Version.
		"""
		# Download the main page
		Output.message( "Downloading index.php (Main Page) as index.html." )
		query = {}
		index = RequestIndex.query( query )
		index = RequestIndex.removeIP( index )
		if ( os.path.exists( "Special:Version.html" ) ):
			os.remove( "index.html" )
		else:
			pass
		for line in index:
			Output.appendToFile( "index.html", line )

		# Download Special:Version or its respective localized version
		Output.message( "Downloading Special:Version with extensions and other related info." )
		query = { "title": "Special:Version" }
		SpecialVersion = RequestIndex.query( query )
		SpecialVersion = RequestIndex.removeIP( SpecialVersion )
		if ( os.path.exists( "Special:Version.html" ) ):
			os.remove( "Special:Version.html" )
		else:
			pass
		for line in SpecialVersion:
			Output.appendToFile( "Special:Version.html", line )

	def fixHTMLEntities(self, text):
		"""
		Convert some HTML entities to their regular characters.
		"""
		text = re.sub('&lt;', '<', text)
		text = re.sub('&gt;', '>', text)
		text = re.sub('&amp;', '&', text)
		text = re.sub('&quot;', '"', text)
		text = re.sub('&#039;', '\'', text)
		return text

	def help(self):
		"""
		Provides vital help information to the user. This function 
		directly uses the "print" function because it is harmless and 
		what needs to be logged has already been done so.

		Returns: Help message text
		"""
		message = """DumpGenerator %s, a script to generate backups of MediaWiki wikis.
For more information, please see: http://code.google.com/p/wikiteam/wiki/NewTutorial

Startup:
  -h, --help         Displays this help information and exits.
  -v, --version	     Displays the version of this script, with additional credits.

Wiki information:
  --api=URL          The URL to the wiki's api.php, not to be used with --index.
  --index=URL        The URL to the wiki's index.php, not to be used with --api.

Options:
  --xml	             Creates an XML dump.
  --images           Creates an image dump.
  --logs             Creates a dump of all log pages (not yet supported).

XML dump (only if --xml is used):
  --curonly          Download only the current revision.
  --exnamespaces     The unique system number(s) for namespaces to exclude, separated by commas.
  --titlesonly       Download only the page titles without the actual content.
  --titles           Path to a file containing list of titles, requires "--END--" to be on the last line.

Other:
  --auto             Enable auto pilot mode (select options that ensures that the script creates a new dump).
  --resume           Resume an incomplete dump (requires --path to be given).
  --path=PATH        Path to the incomplete dump.
  --delay=SECONDS    Adds a delay (in seconds) between requests.
  --cookies=PATH     Path to a Mozilla cookies.txt file for authentication cookies.
  --nolog            Disable logging to dumpgenerator.log (does not affect output in terminal).

Report any issues to our issue tracker: https://code.google.com/p/wikiteam.""" % (self.Version)
		return message

	def loadConfig(self):
		"""
		Load a config file from a partially-made dump.
		"""
		config = json.loads( self.configfile )
		self.date = config[ "date" ]
		self.useAPI = config[ "useAPI" ]
		self.useIndex = config[ "useIndex" ]
		self.urltoapi = config[ "urltoapi" ]
		self.urltoindex = config[ "urltoindex" ]
		self.images = config[ "images" ]
		self.logs = config[ "logs" ]
		self.xml = config[ "xml" ]
		self.curonly = config[ "curonly" ]
		self.exnamespaces = config[ "exnamespaces" ]
		self.titlesonly = config[ "titlesonly" ]

		if ( self.images == True ):
			self.tasklist.append( "bimage" )
		if ( self.logs == True ):
			self.tasklist.append( "clogs" )
		if ( self.xml == True ):
			self.tasklist.append( "axml" )

		if ( self.useAPI == True ):
			domain = self.urltoapi
		elif ( self.useIndex == True ):
			domain = self.urltoindex

	def makePrefix(self, domain):
		"""
		Converts a domain to a prefix.

		Inputs:
		 - domain: The domain to change, may contain api.php or index.php as suffix.

		Returns:
		 - string with slashes and stray characters changed to underscores, suffix 
		   removed and URL protocol removed.
		"""
		domain = domain.lower()
		# Remove unnecessary prefixes and suffixes
		domain = re.sub(r'(https?://|www\.|/index\.php|/api\.php)', '', domain)
		# Substitute directory slashes with underscores
		domain = re.sub(r'/', '_', domain)
		# Convert any stray character that is not in the alphabet to underscores
		domain = re.sub(r'[^-.A-Za-z0-9]', '_', domain)
		return domain

	def makeNiceURL(self, domain):
		"""
		Converts a domain to a more human-readable format (used for uploading).

		Inputs:
		 - domain: The domain to change, may contain api.php or index.php as suffix.

		Returns:
		 - string with suffix removed.
		"""
		domain = domain.lower()
		# Remove the suffixes
		domain = re.sub(r'(/index\.php|/api\.php)', '', domain)
		return domain

	def processargs(self):
		"""
		Processing arguments and options provided by the user.
		"""
		try:
			options, answers = getopt.getopt( sys.argv[1:], self.shortoptions, self.longoptions )
		except getopt.GetoptError:
			Output.error( "An unknown option has been specified, please check your arguments before re-running!" )
			sys.exit(1)

		# First accept all arguments and store them in a variable
		for option, answer in options:
			# Startup
			if ( option in ( "-h", "--help" ) ):
				# Display the help guide and exit
				print self.help()
				os.remove( Output.logfile )
				sys.exit(0)
			elif ( option in ( "-v", "--version" ) ):
				# Display the version of this script
				print self.version()
				os.remove( Output.logfile )
				sys.exit(0)

			# Wiki information
			elif ( option in "--api" ):
				self.urltoapi = answer
				self.configoptions[ "urltoapi" ] = self.urltoapi
			elif ( option in "--index" ):
				self.urltoindex = answer
				self.configoptions[ "urltoindex" ] = self.urltoindex

			# Dump options
			elif ( option == "--images" ):
				self.images = True
				self.configoptions[ "images" ] = True
				self.tasklist.append( "bimages" )
			elif ( option == "--logs" ):
				self.logs = True
				self.configoptions[ "logs" ] = True
				self.tasklist.append( "clogs" )
			elif ( option == "--xml" ):
				self.xml = True
				self.configoptions[ "xml" ] = True
				self.tasklist.append( "axml" )

			# XML dump options
			elif ( option == "--curonly" ):
				self.curonly = True
				self.configoptions[ "curonly" ] = True
			elif ( option in "--exnamespaces" ):
				self.exnamespaces = answer
				self.configoptions[ "exnamespaces" ] = self.exnamespaces
			elif ( option == "--titlesonly" ):
				self.titlesonly = True
				self.configoptions[ "titlesonly" ] = True
			elif ( option in "--titles" ):
				self.titles = os.path.abspath( answer )

			# Other options
			elif ( option == "--auto" ):
				self.autonomous = True
			elif ( option in "--cookies" ):
				self.cookies = answer
			elif ( option in "--delay" ):
				self.delay = answer
			elif ( option == "--nolog" ):
				self.nolog = True
			elif ( option in "--path" ):
				self.path = answer
			elif ( option == "--resume" ):
				self.resume = True

			# Private options (i.e. usable but not documented in --help)
			elif ( option == "--debug" ):
				self.debugmode = True
			else:
				Output.error( "An unknown option has been specified, please check your arguments before re-running!" )
				sys.exit(1)

		# Now to verify that the user is not messing around
		if ( self.urltoapi == "" and self.urltoindex == "" ):
			# User did not specify either --api= or --index=
			if ( self.resume == True and self.path != "" ):
				# ...but specified --resume and --path= accordingly
				self.resumeDump()
			elif ( self.resume == True and self.path == "" ):
				# ...and specified --resume without --path=
				Output.error( "--resume was provided, but you still need to tell me the path to the incomplete dump!" )
				sys.exit(1)
			else:
				Output.error( "You need to tell me the URL to either the api.php or to index.php!" )
				sys.exit(1)
		elif ( self.resume == True ) and ( self.path == "" ):
			# User specified --resume, but no --path= was given
			Output.error( "--resume was provided, but you still need to tell me the path to the incomplete dump!" )
			sys.exit(1)
		elif ( self.urltoapi != "" and self.urltoindex != "" ):
			# User specified both --api= and --index=
			self.useAPI = True
		elif ( self.xml == False and ( self.curonly == True or self.exnamespaces != "" ) ):
			# User specified --curonly and --exnamespaces without --xml
			Output.error( "You did not specify to make an XML dump using --xml, so why write --curonly or --exnamespaces? Remove them before re-running!" )
			sys.exit(1)

		if ( self.urltoapi != "" ):
			self.useAPI = True
		elif ( self.urltoindex != "" ):
			self.useIndex = True

		if ( self.useAPI == True ):
			Output.message( "Checking api.php..." )
			if not ( self.urltoapi.startswith( "http://" ) ) and not ( self.urltoapi.startswith( "https://" ) ):
				Output.error( "The URL to api.php must start with either http:// or https://!" )
				sys.exit(1)
			elif ( self.checkAPI() ):
				Output.message( "api.php is okay" )
			else:
				Output.error( "There is an error with api.php, please provide a correct path to it." )
				sys.exit(1)
		elif ( self.useIndex == True ):
			Output.message( "Checking index.php..." )
			if not ( self.urltoindex.startswith( "http://" ) ) and not ( self.urltoindex.startswith( "https://" ) ):
				Output.error( "The URL to index.php must start with either http:// or https://!" )
				sys.exit(1)
			elif ( self.checkIndex() ):
				Output.message( "index.php is okay" )
			else:
				Output.error( "There is an error with index.php, please provide a correct path to it." )
				sys.exit(1)

	def resumeDump(self):
		"""
		Resume an incomplete dump defined in self.path.
		"""
		# TODO: Add support for resuming dumps.
		os.chdir( self.path )
		self.loadConfig()
		self.prefix = "%s-%s" % ( self.makePrefix( domain ), self.date )
		self.domain = self.makeNiceURL( domain )
		if ( self.useAPI == True ):
			self.urltoindex = "%s/index.php" % ( self.domain )
		self.tasklist = sorted( self.tasklist )
		for task in self.tasklist:
			if ( task == "axml" ):
				DumpXML.run()
			elif ( task == "bimages" ):
				DumpImages.run()
			elif ( task == "clogs" ):
				DumpLogs.run()

	def run(self):
		"""
		Run the whole script itself and excute important functions.
		"""
		print self.welcome()
		Updater.checkRevision()
		# Check if previously there was a log file in the working directory and remove it if exists
		# This is followed by the equivalent of "touch" in Unix to create an empty file
		if ( os.path.exists( Output.logfile ) ):
			os.remove( Output.logfile )
			open( Output.logfile, "a" ).close()
		else:
			open( Output.logfile, "a" ).close()
		self.processargs()
		if ( DumpGenerator.nolog or DumpGenerator.debugmode):
			# Remove the dumpgenerator.log file
			os.remove( Output.logfile )
		if ( self.useAPI == True ):
			domain = self.urltoapi
		elif ( self.useIndex == True ):
			domain = self.urltoindex
		directories = os.walk( "." ).next()[1]
		for directory in directories:
			# Check if there is a dump that already exists in the current working directory
			if ( directory.startswith( self.makePrefix( domain ) ) and directory.endswith( "-wikidump" ) ):
				print "" # Create a blank line
				Output.warn( "There seems to be a similar dump at %s which might be incomplete." % ( directory ) )
				if ( self.autonomous == True ):
					Output.message( "Since auto pilot mode is enabled, that dump will not be resumed." )
					self.resume = False
				else:
					Output.warn( "Do you wish to resume using configuration from that dump? [yes, y], [no, n]" )
					reply = ""
					while reply.lower() not in [ "yes", "y", "no", "n" ]:
						reply = raw_input( "Answer: " )
					if ( reply.lower() in [ "yes", "y" ] ):
						if not ( os.path.isfile( "%s/%s" % ( directory, self.configfile ) ) ):
							Output.error( "I cannot find a %s in the directory! Please delete that directory before re-running!" % ( self.configfile ) )
							sys.exit(1)
						else:
							Output.warn( "Resuming dump and ignoring configuration given in this session..." )
							self.resume = True
							self.path = directory
							break
					elif ( reply.lower() in [ "no", "n" ] ):
						Output.message( "Not resuming..." )
						self.resume = False
			else:
				continue
		if ( self.resume == True ):
			self.resumeDump()
		else:
			self.prefix = "%s-%s" % ( self.makePrefix( domain ), self.date )
			self.domain = self.makeNiceURL( domain )
			workingdir = "%s-wikidump" % ( self.prefix )
			if ( os.path.exists( workingdir ) ):
				if ( self.autonomous == True ):
					Output.message( "Since auto pilot mode is enabled, the directory with the same name will be deleted." )
					reply = "yes"
				else:
					Output.warn( "\nThere seems to be a directory with the same name, delete the old one? [yes, y], [no, n]" )
					reply = ""
				while reply.lower() not in [ "yes", "y", "no", "n" ]:
					reply = raw_input( "Answer: " )
				if ( reply.lower() in [ "yes", "y" ] ):
					try:
						shutil.rmtree( workingdir )
					except:
						Output.error( "There was a problem deleting the directory, please manually delete it before re-running!" )
						sys.exit(1)
					print "" # Create a blank line
				elif ( reply.lower() in [ "no", "n" ] ):
					Output.error( "Existing directory exists, either delete that directory or rename it before re-running!" )
					sys.exit(1)
			else:
				pass
			Output.message( "Generating a new dump into a new directory..." )
			os.mkdir( workingdir )
			os.rename( Output.logfile, "%s/%s" % ( workingdir, Output.logfile ) )
			os.chdir( workingdir )
			self.saveConfig()
			# Guess the URL to index.php
			if ( self.useAPI == True ):
				self.urltoindex = "%s/index.php" % ( self.domain )
			if ( self.debugmode == True ):
				self.debug()
			else:
				# Run every single task that we are assigned to do in order: xml, images, logs
				# The "a", "b" and "c" prefix is just to force the order.
				self.tasklist = sorted( self.tasklist )
				if ( self.tasklist == [] ):
					Output.error( "You did not tell me what dump to create!" )
				else:
					for task in self.tasklist:
						if ( task == "axml" ):
							DumpXML.run()
						elif ( task == "bimages" ):
							DumpImages.run()
						elif ( task == "clogs" ):
							DumpLogs.run()
					self.downloadHtmlPages()
					print self.bye()

	def saveConfig(self):
		"""
		Save the configuration settings provided.
		"""
		self.configoptions[ "date" ] = self.date
		output = open( self.configfile, "w" )
		json.dump( self.configoptions, output, indent=4 )

	def version(self):
		"""
		Displays the version information and credits of the script.

		Returns: Version information and credits
		"""
		message = """DumpGenerator %s by WikiTeam

Copyright (C) 2013 Hydriz Scholz
Copyright (C) 2014 WikiTeam

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA, or visit
<http://www.gnu.org/copyleft/gpl.html>
""" % (self.Version)
		return message

	def welcome(self):
		"""
		Welcomes the user at the very beginning of the script running process.

		Returns: Welcome message.
		"""
		message = """########## Welcome to DumpGenerator %s by WikiTeam ##########\n""" % (self.Version)
		return message

class DumpImages:
	"""
	The class for generating an image dump.
	"""
	def __init__(self):
		"""
		The constructor function.
		"""
		self.files = []

	def dumpImages(self):
		"""
		Download all the images on the wiki with their corresponding XML.
		"""
		if ( DumpGenerator.useAPI == True ):
			self.getFileListAPI()
		else:
			self.getFileListIndex()
		filecount = 0
		if ( self.files == [] ):
			pass
		else:
			Output.message( "Downloading files and their descriptions into \"images\" directory..." )
			for media in self.files:
				time.sleep( DumpGenerator.delay ) # Delay between requests
				urllib.urlretrieve( media[ "url" ], "images/%s" % (media[ "name" ] ) )
				title = DumpGenerator.fixHTMLEntities( media[ "title" ].encode( "utf-8" ) )
				contentsfile = DumpXML.getXMLPage( title, siteinfo=True )
				destfile = "images/%s.xml" % ( media[ "name" ] )
				shutil.move( contentsfile, destfile )
				Output.appendToFile( destfile, "</mediawiki>\n" )
				filecount += 1
				if ( filecount % 10 == 0 ):
					# Give the user a regular status report so that it does not look stuck
					Output.message( "    Downloaded %d files." % ( filecount ) )
			if ( filecount == 1 ):
				Output.message( "Downloaded 1 file." % ( filecount ) )
			else:
				Output.message( "Downloaded %d files." % ( filecount ) )

	def getFileListAPI(self):
		"""
		Download the list of files on the wiki via the API.
		"""
		files = []
		dumpfile = "%s-images.txt" % ( DumpGenerator.prefix )
		filecount = 0
		Output.message( "Getting list of files on the wiki..." )
		aifrom = "!" # Very first page of a wiki
		while aifrom:
			sys.stderr.write('.') # Tell the user that downloading is in progress
			query = {
				"list": "allimages",
				"aifrom": aifrom,
				"ailimit": 500 } # The default limit for anonymous users of the API is 500 pages per request
			time.sleep( DumpGenerator.delay ) # Delay between requests
			filesmeta = json.loads( RequestAPI.query( query ) )
			# Store what the server tells us to continue from
			try:
				serveraifrom = filesmeta[ "query-continue" ][ "allimages" ][ "aicontinue" ]
				aifrom = DumpGenerator.fixHTMLEntities( serveraifrom )
			except:
				# Reached the end of having to keep continuing, exit the while condition
				aifrom = ""
			# TODO: On a wiki with a lot of files, this can cause huge memory problems
			files.extend( filesmeta[ "query" ][ "allimages" ] )
			for media in filesmeta[ "query" ][ "allimages" ]:
				outputline = "%s\t%s\n" % ( media[ "title" ], media[ "url" ] )
				Output.appendToFile( dumpfile, outputline )
			# Add to namespace page count
			filecount += len( files )
		Output.appendToFile( dumpfile, "--END--" )
		if ( filecount == 1 ):
			Output.message( "    Got 1 file" )
		else:
			Output.message( "    Got %d files" % ( filecount ) )

		if ( filecount == 0 ):
			Output.warn( "There are no files on the wiki to download!" )
		else:
			Output.message( "File names and URLs saved at %s." % ( dumpfile ) )
		self.files = files

	def getFileListIndex(self):
		"""
		Download the list of files on the wiki via index.php.
		"""
		# TODO: Add code here

	def run(self):
		"""
		Execute the process of producing an image dump.
		"""
		if ( os.path.isdir( "images" ) ):
			time.sleep(0)
		else:
			os.mkdir( "images" )
		self.dumpImages()

class DumpLogs:
	"""
	The class for generating a log pages dump (pages in Special:Log).
	"""
	def __init__(self):
		"""
		The constructor function.
		"""

	def run(self):
		"""
		Execute the process of producing a log pages dump.
		"""
		# TODO: Support downloading of log pages
		Output.warn( "Sorry, downloading of log pages are not yet supported!" )

class DumpXML:
	"""
	The class for generating an XML dump.
	"""
	def __init__(self):
		"""
		The constructor function.
		"""
		self.lennamespaces = 0
		self.namespaces = {}
		self.pagetitles = []
		self.titlesdumpfile = ""
		self.dumpretrycount = 0

	def dumpPageTitlesAPI(self):
		"""
		Get a list of page titles and outputs it to a file.
		"""
		self.getNamespacesAPI()
		self.getPageTitlesAPI()
		Output.message( "Saving list of page titles..." )
		Output.appendToFile( self.titlesdumpfile, "--END--" )
		Output.message( "List of page titles saved at %s." % ( self.titlesdumpfile ) )

	def dumpXML(self):
		"""
		Get the whole wiki in an XML file.
		"""
		Output.message( "Downloading the XML of every page..." )
		if ( DumpGenerator.curonly == True ):
			dumpfile = "%s-curonly.xml" % ( DumpGenerator.prefix )
		else:
			dumpfile = "%s-history.xml" % ( DumpGenerator.prefix )
		pagecount = 0
		# To reduce memory usage, we are storing the title into memory only when we need it
		for title in file( self.titlesdumpfile, "r" ).read().splitlines():
			pagecount += 1
			numberofedits = 0
			# Add the initial siteinfo and header tags for the first page
			if ( pagecount == 1 ):
				contentsfile = self.getXMLPage( title, siteinfo=True )
				contents = file( contentsfile, "r" ).readlines()
				open( dumpfile, "a" ).close() # "touch" the file
				os.remove( contentsfile )
			elif ( title == "--END--" ):
				contents = [ "</mediawiki>\n" ]
			else:
				contentsfile = self.getXMLPage( title )
				contents = file( contentsfile, "r" ).readlines()
				os.remove( contentsfile )

			for content in contents:
				# Count the number of occurrences of "<timestamp>" to determine number of revisions
				if ( "<timestamp>" in content ):
					numberofedits += 1
				Output.appendToFile( dumpfile, content )
			if ( title == "--END--" ):
				pass
			else:
				if ( numberofedits == 1 ):
					Output.message( "    %s, 1 edit" % ( title ) )
				else:
					Output.message( "    %s, %s edits" % ( title, numberofedits ) )
			if ( pagecount % 10 == 0 ):
				Output.message( "Downloaded %d pages" % ( pagecount ) )
		Output.message( "XML dump saved at %s." % ( dumpfile ) )
		self.integrityCheck( dumpfile )

	def getNamespacesAPI(self):
		"""
		Download the list of namespaces with their names and IDs
		via the API.
		"""
		query = {
			"meta": "siteinfo",
			"siprop": "namespaces" }
		namespacedetails = json.loads( RequestAPI.query( query ) )
		namespacenums = namespacedetails[ "query" ][ "namespaces" ].keys()
		# Remove the system namespaces ("Media" and "Special")
		namespacenums.remove( "-2" )
		namespacenums.remove( "-1" )
		namespaces = {}
		for namespacenum in namespacenums:
			namespacename = namespacedetails[ "query" ][ "namespaces" ][ namespacenum ][ "*" ]
			namespaces[ namespacenum ] = namespacename
		self.lennamespaces = len( list( namespacenums ) )
		Output.message( "%d namespaces found." % ( self.lennamespaces ) )
		self.namespaces = namespaces

	def getPageTitlesAPI(self):
		"""
		Grab a list of page titles in each namespace via the API.
		
		There are leading spaces in the outputs so as to make things neater on the terminal.
		"""
		titles = []
		self.titlesdumpfile = "%s-titles.txt" % ( DumpGenerator.prefix )
		totalpagecount = 0
		for namespace in self.namespaces:
			if namespace in DumpGenerator.exnamespaces:
				Output.warn( "    Skipping namespace %s" % (namespace) )
			else:
				pagecount = 0
				Output.message( "    Getting titles in namespace %s" % (namespace) )
				apfrom = "!" # Very first page of a wiki
				while apfrom:
					sys.stderr.write( "." ) # Tell the user that downloading is in progress
					query = {
						"list": "allpages",
						"apnamespace": namespace,
						"apfrom": apfrom,
						"aplimit": 500 } # The default limit for anonymous users of the API is 500 pages per request
					time.sleep( DumpGenerator.delay ) # Delay between requests
					pagetitles = json.loads( RequestAPI.query( query ) )
					# Store what the server tells us to continue from
					try:
						serverapfrom = pagetitles[ "query-continue" ][ "allpages" ][ "apcontinue" ]
						apfrom = DumpGenerator.fixHTMLEntities( serverapfrom )
					except:
						try:
							serverapfrom = pagetitles[ "query-continue" ][ "allpages" ][ "apfrom" ]
							apfrom = DumpGenerator.fixHTMLEntities( serverapfrom )
						except:
							# Reached the end of having to keep continuing, exit the while condition
							apfrom = ""
					pages = pagetitles[ "query" ][ "allpages" ]
					# Add to namespace page count
					pagecount += len( pages )
					for page in pages:
						title = "%s\n" % ( page[ "title" ] )
						Output.appendToFile( self.titlesdumpfile, title )
				if ( pagecount == 1 ):
					Output.message( "    Got 1 page title in namespace %s" % ( namespace ) )
				else:
					Output.message( "    Got %d page titles in namespace %s" % ( pagecount, namespace ) )
				# Add to total page count
				totalpagecount += pagecount
		if ( totalpagecount == 1 ):
			Output.message( "Got 1 page title in total." % ( totalpagecount ) )
		else:
			Output.message( "Got %d page titles in total." % ( totalpagecount ) )

	def getXMLPage(self, page, siteinfo=False):
		"""
		Get the XML of one page.
		
		Input:
		 - page: The title of the page to download.
		 - siteinfo: Whether to include the siteinfo header in the XML.
		"""
		parameters = {
			"title": "Special:Export",
			"pages": page,
			"action": "submit" }
		if ( DumpGenerator.curonly == True ):
			parameters[ "curonly" ] = 1
			parameters[ "limit" ] = 1
		else:
			# Make the wiki download the actual full history
			parameters["history"] = "1"
		# TODO: Can cause memory problems if the page has a huge history
		result = RequestIndex.query( parameters )
		pagehash = hashlib.sha256( page ).hexdigest()[:8]
		tempfile = "%s.xml.tmp" % ( pagehash )
		tempfile2 = "%s.xml" % ( pagehash )
		Output.appendToFile( tempfile, result )
		result = "" # Free up memory
		# Warning: The following is NOT compatible with MediaWiki XML Schema Description version 0.3 and below!
		# See http://wikiteam.googlecode.com/svn/trunk/schema/README.md for more information about MediaWiki versions 
		# this will affect and ways to overcome it.
		if ( siteinfo == False ):
			linecount = 0
			# The 11 comes from lines like <siteinfo>, "special" namespaces and the very first line
			# TODO: Hacky way of removing the siteinfo, check for backward compatibility!
			linestoskip = 11 + self.lennamespaces
			for line in open( tempfile, "r" ).read().splitlines():
				linecount += 1
				if linecount > linestoskip:
					if ( "</mediawiki>" in line ):
						pass
					else:
						line = "%s\n" % ( line )
						Output.appendToFile( tempfile2, line )
				else:
					continue
		else:
			for line in open( tempfile, "r" ).read().splitlines():
				if ( "</mediawiki>" in line ):
					pass
				else:
					line = "%s\n" % ( line )
					Output.appendToFile( tempfile2, line )
		os.remove( tempfile )
		return tempfile2

	def integrityCheck(self, dumpfile):
		"""
		Checks the integrity of the XML dump and ensures that it is not corrupted.
		"""
		Output.message( "Checking the integrity of the XML dump..." )
		checktitles = 0
		checkpageopen = 0
		checkpageclose = 0
		checkrevisionopen = 0
		checkrevisionclose = 0
		# Check the number of instances of the following tags
		# By logic they should be the same number
		for line in file( dumpfile, "r" ).read().splitlines():
			if "<title>" in line:
				checktitles += 1
			elif "<page>" in line:
				checkpageopen += 1
			elif "</page>" in line:
				checkpageclose += 1
			elif "<revision>" in line:
				checkrevisionopen += 1
			elif "</revision>" in line:
				checkrevisionclose += 1
			else:
				continue

		if ( checktitles == checkpageopen and checktitles == checkpageclose and checkrevisionopen == checkrevisionclose ):
			Output.message( "Excellent, the XML dump is not corrupted." )
		else:
			Output.warn( "WARNING: XML dump seems to be corrupted." )
			if ( DumpGenerator.autonomous == True ):
				reply = "yes"
			else:
				reply = ""
			while reply.lower() not in [ "yes", "y", "no", "n" ]:
				reply = raw_input( 'Regenerate a new dump ([yes, y], [no, n])? ' )
			if reply.lower() in [ "yes", "y" ]:
				self.dumpretrycount += 1
				if ( self.dumpretrycount < 3 ):
					Output.warn( "Generating a new dump..." )
					os.remove( dumpfile )
					self.dumpXML()
				else:
					Output.warn( "We have tried dumping the wiki 3 times, but the dump is still corrupted. Not going to carry on since it is probably a problem on the wiki." )
					# Encourage the user to tell us about this faulty wiki
					print "Please tell us about this by reporting an issue here: https://code.google.com/p/wikiteam/issues/list. Thank you!"
					print "Giving you a little time to see this message..."
					time.sleep(3) # Give time for the user to see the message
			elif reply.lower() in [ "no", "n" ]:
				Output.warn( "Not generating a new dump. Note: Your dump is corrupted and might not work with MediaWiki!" )

	def run(self):
		"""
		Execute the process of producing an XML dump.
		"""
		if ( DumpGenerator.useAPI == True ):
			if ( DumpGenerator.titlesonly == True ):
				self.dumpPageTitlesAPI()
			else:
				if ( DumpGenerator.titles != "" ):
					Output.message( "Using the list of page titles provided at %s." % ( DumpGenerator.titles ) )
					self.titlesdumpfile = DumpGenerator.titles
				else:
					self.dumpPageTitlesAPI()
				self.dumpXML()
		else:
			if ( DumpGenerator.titlesonly == True ):
				self.dumpPageTitlesIndex()
			else:
				if ( DumpGenerator.titles != "" ):
					self.titlesdumpfile = DumpGenerator.titles
				else:
					self.dumpPageTitlesIndex()
				self.dumpXML()

class Output:
	"""
	The class to output anything to the user or to a place not within the script.

	For doing outputs to user:
		This is used instead of directly using the "print" function is because 
		this is intended to log everything that is told to the user, so that it 
		is possible to check when and where things went wrong.

	For doing outputs to elsewhere:
		This is to reduce memory usage by storing large chunks of data into disk 
		and reducing the risk of getting a MemoryError.
	"""
	def __init__(self):
		self.logfile = "dumpgenerator.log"

	# Output to disk
	def appendToFile(self, outputfile, contents):
		"""
		Output contents to file.

		Inputs:
		 - outputfile: The file to output to.
		 - contents: The content to add for each line.
		"""
		if ( os.path.exists( outputfile ) == False ):
			open( outputfile, "a" ).close() # "touch" the file
		else:
			pass
		thefile = open( outputfile, "a" )
		try:
			contents = contents.encode( "utf-8", "ignore" )
		# TODO: During a test phase, this error kept coming up, though the final output was no different from
		# what was produced using dumpBackup.php and using Special:Export itself.
		except UnicodeDecodeError:
			pass
		thefile.write( contents )
		thefile.close()

	# Output to user
	def error(self, message):
		print message
		print "Write --help for more information."
		self.log( "An error occurred: %s" % (message) )

	def log(self, message):
		if ( DumpGenerator.nolog or DumpGenerator.debugmode):
			# Skip logging
			time.sleep(0)
		else:
			timestamp = datetime.datetime.fromtimestamp( time.time() ).strftime( "%Y-%m-%d %H:%M:%S" )
			logline = "%s: %s\n" % (timestamp, message)
			self.appendToFile( self.logfile, logline )

	def message(self, message):
		print message
		self.log( "Told the user: %s" % (message) )

	def warn(self, message):
		print message
		self.log( "Warned the user: %s" % (message) )

class RequestAPI:
	"""
	The RequestAPI class, to submit APi request calls to the server.
	"""
	def __init__(self):
		"""
		The constructor function.
		"""

	def query(self, params, url=""):
		"""
		The function to send an API call to the server given in the "url" 
		parameter using the parameters found in params. If url is empty, 
		DumpGenerator.urltoapi is used instead.

		Note: This function will assume action=query, other functions provides 
		the other query forms, but not this one.

		Input:
		 - params: Parameters to API call as an array (excluding action=query and format=json)

		Returns
		 - Result of API call in JSON format.
		"""
		if ( url == "" ):
			url = DumpGenerator.urltoapi
		else:
			url = url
		queryurl = "%s?action=query&format=json" % ( url )
		headers = { "User-Agent": DumpGenerator.UserAgent }
		# Convert the array to a proper URL
		paras = urllib.urlencode( params )
		# POST the parameters to the server
		request = urllib2.Request( queryurl, paras, headers )
		try:
			result = urllib2.urlopen( request )
		except:
			try:
				# Add a little delay between requests if server is slow
				sleeptime = DumpGenerator.delay + 10
				Output.warn( "Failed to get a response from the server, retrying in %d seconds..." % (sleeptime) )
				time.sleep( sleeptime )
				result = urllib2.urlopen( request )
			except:
				Output.error( "An error occurred when trying to get a response from the server. Please resume the dump with --resume." )
				sys.exit(2)
		output = result.read()
		result.close()
		return output

class RequestIndex:
	def __init__(self):
		"""
		The constructor function.
		"""

	def query(self, params, url=""):
		"""
		The function to send an request to the server given in the "url" 
		parameter using the parameters found in params. If url is empty, 
		DumpGenerator.urltoindex is used instead.

		Input:
		 - params: Parameters to the request to send, appended to url as 
		   a GET request.

		Returns
		 - Result of GET request.
		"""
		if ( url == "" ):
			url = DumpGenerator.urltoindex
		else:
			url = url
		headers = { "User-Agent": DumpGenerator.UserAgent }
		paras = urllib.urlencode( params )
		# index.php does not support POST request, formulating a correct GET URL here
		queryurl = "%s?%s" % ( url, paras )
		request = urllib2.Request( queryurl, headers=headers )
		# TODO: Make urlopen follow redirects
		try:
			result = urllib2.urlopen( request )
		except:
			try:
				# Add a little delay between requests if server is slow
				sleeptime = DumpGenerator.delay + 10
				Output.warn( "Failed to get a response from the server, retrying in %d seconds..." % (sleeptime) )
				time.sleep( sleeptime )
				result = urllib2.urlopen( request )
			except:
				Output.error( "An error occurred when trying to get a response from the server. Please resume the dump with --resume." )
				sys.exit(2)
		output = result.read()
		result.close()
		return output

	def removeIP(self, content):
		"""
		Remove the user's IP address while fetching HTML pages.
		"""
		# Remove IPv4 addresses
		content = re.sub( r"\d+\.\d+\.\d+\.\d+", "0.0.0.0", content )
		# Remove IPv6 addresses
		content = re.sub( r"(?i)[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}:[\da-f]{0,4}", "0:0:0:0:0:0:0:0", content )
		return content

class Updater:
	"""
	The class to auto-update the user's script to the latest version of DumpGenerator.
	"""
	# TODO: Get the script to check only occasionally, this is a performance concern
	def __init__(self):
		"""
		The constructor function.
		"""
		self.controlUrl = "http://wikiteam.googlecode.com/svn/trunk/revnum.json"
		self.controlUrl2 = "https://raw.github.com/dumps/DumpGenerator/master/revnum.json"
		self.result = {}

	def checkRevision(self):
		"""
		Check the current revision and ensure that it is up-to-date.
		"""
		jsonresult = self.getRevisionJson()
		if ( jsonresult == False ):
			pass
		else:
			result = json.loads( jsonresult )
			self.result = result
			if ( result[ "latest" ] == DumpGenerator.Version ):
				if ( result[ "releases" ][ DumpGenerator.Version ][ "revision" ] == DumpGenerator.revision ):
					pass
				else:
					self.update()
			else:
				self.update()

	def getRevisionJson(self):
		"""
		Download the controlling JSON file.
		"""
		headers = {'User-Agent': DumpGenerator.UserAgent}
		skip = False
		# TODO: Handle 404 errors
		try:
			revjson = urllib2.urlopen( urllib2.Request( self.controlUrl, headers=headers ) )
		except:
			try:
				revjson = urllib2.urlopen( urllib2.Request( self.controlUrl2, headers=headers ) )
			except:
				Output.warn( "Unable to check if a new version of dumpgenerator.py is available, continuing..." )
				skip = True
		if ( skip == False ):
			output = revjson.read()
			revjson.close()
			return output
		else:
			return False

	def update(self):
		"""
		Update DumpGenerator.py to the current latest version
		"""
		currentfile = sys.argv[0]
		latestver = self.result[ "latest" ]
		latestrev = self.result[ "releases" ][ latestver ][ "revision" ]
		latesturl = self.result[ "releases" ][ latestver ][ "downloadurl" ]
		latesturl2 = self.result[ "releases" ][ latestver ][ "downloadurl2" ]
		updated = True
		# TODO: Handle 404 errors
		try:
			urllib.urlretrieve( latesturl, currentfile )
		except:
			try:
				urllib.urlretrieve( latesturl2, currentfile )
			except:
				updated = False
		if ( updated == False ):
			Output.warn( "Unable to update DumpGenerator, skipping update for now..." )
		else:
			Output.message( "DumpGenerator was updated to %s (revision %s)! Changes will take effect on next run." % ( latestver, latestrev ) )

if __name__ == "__main__":
	# Class registry, for use throughout the whole script
	RequestAPI = RequestAPI()
	RequestIndex = RequestIndex()
	DumpGenerator = DumpGenerator()
	DumpImages = DumpImages()
	DumpLogs = DumpLogs()
	DumpXML = DumpXML()
	Output = Output()
	Updater = Updater()

	# Start everything up
	DumpGenerator.run()
