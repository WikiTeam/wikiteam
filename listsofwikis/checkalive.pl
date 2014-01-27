#!/usr/bin/perl

# Name: checkalive.pl v1.2
# Description: This script will go thru a list of URLs & determine 
# if they are online & if they are Mediawiki wikis. It should work
# with: "/index.php/Main_Page", "index.php", "api.php" and even pages
# such as: "/wiki/Pagina_principale".
#
# Created: 12/14/2013
# Most recently updated: 01/26/2014 (It's a work-in-progress...)
# Copyright (c) 2013-2014 by Scott D. Boyd - scottdb56@gmail.com
# ====================================================================
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
# ====================================================================
#
# NOTE: The following three Perl modules need to be installed on your computer.
# Search for them on cpan.org or use your Linux distro's package manager.
use LWP::Simple;
use LWP::UserAgent;
use Crypt::SSLeay;
my $slp=2; # You can change this number for seconds to sleep between requests (currently 2 seconds)
my $urllist="my-URL-list.txt";
my $alivelist="alive-wikis.txt";
my $deadlist="dead-wikis.txt";
my $pwrdby1="Powered by MediaWiki";
my $pwrdby2="poweredby_mediawiki";
my $genmw="meta name=\"generator\" content=\"MediaWiki"
my $mwapi="MediaWiki API documentation page";
my $lw=0; my $dw=0;
my $a=1; my $b=0; my $c=0;
my $flag=0;
my $ua = LWP::UserAgent->new;
$ua->agent("Mozilla/5.0");			# use this user-agent to get into wikis that block spiders & robots
$ua->timeout(30);
$ua->show_progress(1);

# Here's where most of the work takes place:
open (MYURLLIST,"<$urllist")
  or die "Cannot open the URL-list file: $!";
open (ALIVEFILE,">$alivelist");
open (DEADFILE,">$deadlist");
while (<MYURLLIST>) {
  if ((/\#(.*?)/) || (/^\s*$/)) {		# check to see if line is a comment or a blank line
    next;					# if so - skip it
  } else {
    $url=$_;					# assign the current line to $url
    chomp $url;
    $req = HTTP::Request->new(GET => $url);  	#				 --|
    $req->header('Accept' => 'text/html');	#				   |-- some of these lines
    $res = $ua->request($req);			# send request 			   |-- were adapted from
    if ($res->is_success) {			# if the URL still exists	   |-- lwpcook.pod
       print "Got it! ";			#				   |
       $doc=$res->content;			#				   |
       &ParsePage;				# go to "ParsePage" sub-routine	   |
    } else {					#				   |
      $errormsg=$res->status_line;		#				 --|
      if (substr($errormsg,0,3) eq "500") {		# if response-code 500
         print DEADFILE "$url\n"; $dw++;
      } elsif  (substr($errormsg,0,3) eq "401") {	# if Unauthorized (code 401)
         print DEADFILE "$url\n"; $dw++;
      } elsif  (substr($errormsg,0,3) eq "403") {	# if forbidden (code 403)
         print DEADFILE "$url is alive but access is denied.\n"; $dw++;
      } elsif  (substr($errormsg,0,3) eq "404") {	# if URL is dead (code 404)
         print DEADFILE "$url\n"; $dw++;
      } elsif  (substr($errormsg,0,3) eq "406") {	# if Not Acceptable (code 406)
         print DEADFILE "$url\n"; $dw++;
      }
    }
    $c++; $b=$c/10; 
    if ($b==$a) { 
       print "Checked $c URLs -- ";		# print the progress every 10 URLs
       $a++;
    } 
    if ($slp > 0) {
       print "Pausing for $slp seconds...\n\n"; sleep $slp;
    } else { 					# don't pause - go on to the next URL
    }
  }
}
close DEADFILE; close ALIVEFILE; close MYURLLIST;
print "\nFinished! I found $lw live wikis and $dw dead or non-Mediawiki wikis.\n";

# Here's the sub-routine
# ======================
sub ParsePage  {
   print "Parsing the document... ";
   if (($doc=~/$pwrdby1/i) || ($doc=~/$pwrdby2/i)) {	# if the page contains: "Powered by MediaWiki"
      print "It's alive and powered by Mediawiki\n";	# or: "poweredby_mediawiki"
      print ALIVEFILE "$url\n";				# then it's a MediaWiki wiki
      $flag=1;$lw++;
   } elsif ($doc=~/$genmw/i) {				# if the content generator is MediaWiki
      print "It's alive and powered by Mediawiki\n";	# then it's a MediaWiki wiki
      print ALIVEFILE "$url\n";
      $flag=1;$lw++;
   } elsif ($doc=~/$mwapi/i) {				# if the api.php contains: "MediaWiki API documentation page"
      print "It's alive and powered by Mediawiki\n";	# then it's a MediaWiki wiki
      print ALIVEFILE "$url\n";
      $flag=1;$lw++;
   }
   unless ($flag) {
     print "It's alive but NOT powered by MediaWiki\n";
     print DEADFILE "$url is alive but NOT powered by Mediawiki\n"; $dw++;
   }
   $flag=0;
}

