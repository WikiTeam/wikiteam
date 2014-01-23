#!/usr/bin/perl

# Name: checkalive.pl
# Description: This script will go thru a list of wiki URLs & determine 
# if they are online & if they are Mediawiki wikis. It should work with
# "index.php/Main_Page", "index.php" and "api.php".

# Created: 12/14/2013
# Most recently updated: 01/21/2014
# Copyright (c) 2013-2014 Scott D. Boyd - scottdb56@gmail.com

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

# NOTE: The following three Perl modules need to be installed on your computer.
#       Search for them on cpan.org or use your Linux distro's package manager.
use LWP::Simple;
use LWP::UserAgent;
use Crypt::SSLeay;
my $slp=2;       # You can change this number for seconds to sleep between requests (currently 2)
my $urllist="URL-list.txt";
my $alivelist="alive-wikis.txt";
my $deadlist="dead-wikis.txt";
my $pwrdby1="Powered by MediaWiki";
my $pwrdby2="poweredby_mediawiki";
my $mwapi="MediaWiki API documentation page";
my $lw=0;
my $dw=0;
my $flag=0;
my $ua = LWP::UserAgent->new;
$ua->agent("Mozilla/5.0");			                     # using this user-agent gets around the wikis that don't allow scripts
$ua->timeout(30);
$ua->show_progress(1);

# Here's where most of the work takes place:
open (MYURLLIST,"<$urllist");
open (ALIVEFILE,">$alivelist");
open (DEADFILE,">$deadlist");
while (<MYURLLIST>) {
  if (/\#(.*?)/) {				                           # check to see if line is commented-out
    next;					                                  # if so - skip it
  } else {
    $url=$_;					                               # assign the current line to $url
    chomp $url;
    $req = HTTP::Request->new(GET => $url);  	      #				                         --|
    $req->header('Accept' => 'text/html');	         #				                           | -- some of these lines
    $res = $ua->request($req);			                 # send request 			               | -- were adapted from
    if ($res->is_success) {			                    # if the URL still exists	         | -- lwpcook.pod
      print "Got it! ";				                      #				                           |
      $doc=$res->content;
      &ParsePage;				                            # go to "ParsePage" sub-routine	 --|
    } else {
      $errormsg=$res->status_line;
      if (substr($errormsg,0,3) eq "500") {		      # if response-code 500
        &reCheck;				                            # try the fetch once more
      } elsif  (substr($errormsg,0,3) eq "403") {	  # if URL is forbidden (code 403)
        print DEADFILE "$url is alive but forbidding the script\n"; $dw++;	# print to the dead-file
      } elsif  (substr($errormsg,0,3) eq "404") {	  # if URL is dead (code 404)
        print DEADFILE "$url\n"; $dw++;			        # print to the dead-file
      } elsif  (substr($errormsg,0,3) eq "406") {	  # if Not Acceptable (code 406)
        print DEADFILE "$url\n"; $dw++;			        # print to the dead-file
      }
    }
    print "Pausing for $slp seconds...\n"; sleep $slp;
  }
}
close DEADFILE; close ALIVEFILE; close MYURLLIST;
print "I found $lw live wikis and $dw dead or non-Mediawiki wikis.\n";

# Here's the sub-routines
# =======================
sub ParsePage  {
   print "Parsing the document... ";
   if (($doc=~/$pwrdby1/i) || ($doc=~/$pwrdby2/i)) {	# if the page contains: "Powered by MediaWiki"
      print "It's alive and running Mediawiki.\n";	  # or: "poweredby_mediawiki"
      print ALIVEFILE "$url\n";
      $flag=1;$lw++;
   } elsif ($doc=~/$mwapi/i) {				                # if the api.php contains: "MediaWiki API documentation page"
      print "It's alive and running Mediawiki.\n";
      print ALIVEFILE "$url\n";
      $flag=1;$lw++;
   }
  unless ($flag) {
    print "It's alive but NOT running MediaWiki.\n";
    print DEADFILE "$url is alive but NOT running Mediawiki.\n"; $dw++;
  }
  $flag=0;
}

sub reCheck  {				
    print "Sleeping for 15 seconds - then re-trying...\n"; sleep 15;
    $req = HTTP::Request->new(GET => $url);  	
    $req->header('Accept' => 'text/html');
    $res = $ua->request($req);
    if ($res->is_success) {
       print "Got it! ";
       $doc=$res->content;
       &ParsePage;					                          # go to "ParsePage" sub-routine
    } else {
       print DEADFILE "$url\n"; $dw++; 
    }
}

