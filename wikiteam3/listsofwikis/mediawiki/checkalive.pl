#!/usr/bin/perl

# Name: checkalive.pl v2.01
# Description: This script will go thru a list of URLs & determine if they are online & if they are Mediawiki wikis.
# It should work with: "/index.php/Main_Page", "index.php", "api.php" and even pages such as: "/wiki/Pagina_principale".
# If the URl is not "api.php", it will look for it, check it, and output it if found to be a valid api.php. If not found,
# it will output the URL with "index.php" if that's available.
#
# Created: 12/14/2013
# Most recently updated: 04/11/2014
# Copyright (c) 2013-2014 by Scott D. Boyd - scottdb56@gmail.com
#
# ===========================================================================================================================
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.  If not,
# see <http://www.gnu.org/licenses/>.
# ===========================================================================================================================
#
# NOTE: The following four Perl modules need to be installed on your computer.
#       Search for them on cpan.org or use your Linux distro's package manager.
use LWP::Simple;
use LWP::UserAgent;
use Crypt::SSLeay;
use Mojo::URL;
my $slp=2; 	# You can change this number for seconds to sleep between requests (currently 2 seconds)
my $urllist="URL-list.txt";
my $alivelist="alive-wikis.txt";
my $deadlist="dead-wikis.txt";
my $pwrdby1="Powered by MediaWiki";
my $pwrdby2="poweredby_mediawiki";
my $genmw="meta name\=\"generator\" content\=\"MediaWiki";
my $mwapi="MediaWiki API documentation page";
my $mwapi2="API Home Page";				# found in an older version of the api
my $indexphp="index.php";
my $apiphp="api.php";
my $wapiphp="w\/api.php";
my $wikiapiphp="wiki\/api.php";
my $apiurl="";
my $live=0; my $dead=0;
my $a=1; my $b=0; my $c=0;
my $flag=0;
my $ua = LWP::UserAgent->new;
$ua->agent("Mozilla/5.0");				# use this user-agent to get into wikis that block spiders & robots
$ua->timeout(30);
$ua->show_progress(1);

open (MYURLLIST,"<$urllist")
  or die "Cannot open the URL-list file: $!";
open (ALIVEFILE,">$alivelist");
open (DEADFILE,">$deadlist");
while (<MYURLLIST>) {
  if ((/\#(.*?)/) || (/^\s*$/)) {			# check to see if line is a comment or a blank line
    next;						# if so - skip it
  } else {
    $url=$_;						# assign the current line to $url
    chomp $url;
    $req = HTTP::Request->new(GET => $url);  		#				 --|
    $req->header('Accept' => 'text/html');		#				   |-- some of these lines
    $res = $ua->request($req);				# send request 			   |-- were adapted from
    if ($res->is_success) {				# if the URL still exists	   |-- lwpcook.pod
       print "Got it! ";				#				   |
       $doc=$res->content;				#				   |
       print "Parsing the document... ";
       if (($doc=~/$pwrdby1/i) || ($doc=~/$pwrdby2/i)) {	# if the page contains: "Powered by MediaWiki"
          print "It's alive and powered by MediaWiki\n";	# or: "poweredby_mediawiki"
          $flag=1;$live++;					# then it's a MediaWiki wiki
          & Check4api;
       } elsif ($doc=~/$genmw/i) {				# if the content generator is MediaWiki
          print "It's alive and powered by MediaWiki\n";	# then it's a MediaWiki wiki
          $flag=1;$live++;
          & Check4api;
       } elsif ($doc=~/$mwapi/i) {				# if the api.php contains: "MediaWiki API documentation page"
          print "It's alive and powered by MediaWiki\n";	# then it's a MediaWiki wiki
          print ALIVEFILE "$url\n";
          $flag=1;$live++;
       } elsif ($doc=~/$mwapi2/i) {				# if the api.php contains: "API Home Page" (older version)
          print "It's alive and powered by MediaWiki\n";	# then it's a MediaWiki wiki
          print ALIVEFILE "$url\n";
          $flag=1;$live++;
       }
       unless ($flag) {
         print "It's alive but NOT powered by MediaWiki\n";
         print DEADFILE "$url is alive but NOT powered by MediaWiki\n"; $dead++;
       }
    $flag=0;
    } else {
      $errormsg=$res->status_line;
      if (substr($errormsg,0,3) eq "500") {		# if response-code 500
         print DEADFILE "$url\n"; $dead++;
      } elsif  (substr($errormsg,0,3) eq "401") {	# if Unauthorized (code 401)
         print DEADFILE "$url\n"; $dead++;
      } elsif  (substr($errormsg,0,3) eq "403") {	# if forbidden (code 403)
         print DEADFILE "$url is alive but access is denied.\n"; $dead++;
      } elsif  (substr($errormsg,0,3) eq "404") {	# if URL is dead (code 404)
         print DEADFILE "$url\n"; $dead++;
      } elsif  (substr($errormsg,0,3) eq "406") {	# if Not Acceptable (code 406)
         print DEADFILE "$url\n"; $dead++;
      }
    }
    $c++; $b=$c/10;
    if ($b==$a) {
       print "Checked $c URLs -- ";			# print the progress every 10 URLs
       $a++;
    }
    &PauseRoutine;
  }
}
close DEADFILE; close ALIVEFILE; close MYURLLIST;
print "\nFinished! I found $live live wikis and $dead dead or non-MediaWiki wikis.\n";

# Here's the sub-routines
# =======================
sub Check4api {
   $pos=rindex($url,"\/");				# $pos will contain the position of the final "/" (counting from zero)
   $base_plus=substr($url,0,($pos+1)); 			# $base_plus will contain everything up to & including the final "/"
   my $len1=length($url); my $len2=length($base_plus);
   if ($len2 < 10) {					# if $base_plus contains only "http://" or "https://"
      $base_plus=$url;					# then assign $url to $base_plus
      my $tail=substr $base_plus, -1;
      if (!($tail=~/\//)) {				# if the last character of $base_plus is not a "/"
         $base_plus=$base_plus."\/" ;			# then add it
      }
   }
   $apiurl=$base_plus.$apiphp;				# $apiurl is our new URL with api.php tacked on the end
   &PauseRoutine; & Fetch_api;				# pause & then try to get api.php
   if ($res->is_success) {
     print "Found api.php... "; $doc=$res->content;
     &Parse_api;
   }else{						# if no api.php...
     $apiurl=$base_plus.$wapiphp;			# modify the URL
     &PauseRoutine; & Fetch_api;			# pause & then try to get /w/api.php
     if ($res->is_success) {
       print "Found api.php... "; $doc=$res->content;
       &Parse_api;
      }else{						# if no /w/api.php...
        $apiurl=$base_plus.$wikiapiphp;			# modify the URL
        &PauseRoutine; & Fetch_api;			# pause & then try to get /wiki/api.php
        if ($res->is_success) {
          print "Found api.php... "; $doc=$res->content;
          &Parse_api;
        }else{
          if (/https:\/\//) {
            $scheme="https://";
          } else {
            $scheme="http://";
          }
          $url = Mojo::URL->new($url);
          $base = $url->host;				# extract just the host from $url & assign it to $base
          $base=$scheme.$base;
          my $tail=substr $base, -1;
          if (!($tail=~/\//)) {				# if the last character of $base_plus is not a "/"
          $base=$base."\/" ;				# then add it
          }
          $apiurl=$base.$apiphp;			# $apiurl is our new URL with api.php tacked on the end
          &PauseRoutine; & Fetch_api;			# pause & then try to get api.php
          if ($res->is_success) {
            print "Found api.php... "; $doc=$res->content;
            &Parse_api;
          }else{					# if no api.php...
            $apiurl=$base.$wapiphp;			# modify the URL
            &PauseRoutine; & Fetch_api;			# pause & then try to get /w/api.php
            if ($res->is_success) {
              print "Found api.php... "; $doc=$res->content;
              &Parse_api;
            }else{					# if no /w/api.php...
              $apiurl=$base.$wikiapiphp;		# modify the URL
              &PauseRoutine; & Fetch_api;		# pause & then try to get /wiki/api.php
              if ($res->is_success) {
                print "Found api.php... "; $doc=$res->content;
              &Parse_api;
              }else{
               if (!($url=~/index.php/i)) {		# if the URL does not end with index.php...
                 print "There is no api.php -- I'll try index.php...\n";
                 $indexurl=$base_plus.$indexphp;	# then tack on index.php...
                 $req = HTTP::Request->new(GET => $indexurl); # and try to get it
                 $req->header('Accept' => 'text/html');
                 $res = $ua->request($req);		# send request
                 if ($res->is_success) {
                   $doc=$res->content;
                   if (($doc=~/$pwrdby1/i) || ($doc=~/$pwrdby2/i)) {	# if the page contains: "Powered by MediaWiki"
                     print ALIVEFILE "$indexurl\n";   			# or: "poweredby_mediawiki"
                   }elsif ($doc=~/$genmw/i) {				# if the content generator is MediaWiki
                      print ALIVEFILE "$indexurl\n";
                   }else{
                      print "There is no api.php OR index.php for this URL\n";
                      print ALIVEFILE "$url\n";
                   }
                 }else{
                    print ALIVEFILE "$url\n";
                 }
               }else{
                  print "There is no api.php for this URL\n";
                  print ALIVEFILE "$url\n";
               }
              }
            }
          }
        }
     }
   }
}

sub Fetch_api {
   $req = HTTP::Request->new(GET => $apiurl);
   $req->header('Accept' => 'text/html');
   $res = $ua->request($req);				# send request
}

sub Parse_api {
   print "Parsing the document...\n";
   if ($doc=~/$mwapi/i) {				# if the api.php contains: "MediaWiki API documentation page"
      print "Found a valid api.php and writing it to the list\n";
      print ALIVEFILE "$apiurl\n";			# then it's a MediaWiki wiki - print it to the list
   }elsif ($doc=~/$mwapi2/i) {				# if the api.php contains: "API Home Page" (older version)
      print "Found a valid api.php and writing it to the list\n";
      print ALIVEFILE "$apiurl\n";			# then it's a MediaWiki wiki - print it to the list
   }else{
      print "This api.php is not valid.\n";  		# then try to get index.php
      $indexurl=$base_plus.$indexphp;
      print "Trying to get $indexurl...\n";
      $req = HTTP::Request->new(GET => $indexurl);
      $req->header('Accept' => 'text/html');
      $res = $ua->request($req);			# send request
      if ($res->is_success) {
        $doc=$res->content;
        if (($doc=~/$pwrdby1/i) || ($doc=~/$pwrdby2/i)) { # if the page contains: "Powered by MediaWiki"
          print "Found a good index.php and writing it to the list\n";
          print ALIVEFILE "$indexurl\n";   		  # or: "poweredby_mediawiki"
        }elsif ($doc=~/$genmw/i) {			  # if the content generator is MediaWiki
           print "Found a good index.php and writing it to the list\n";
           print ALIVEFILE "$indexurl\n";
        }else{
           print "There is no api.php OR index.php for $url\n";
           print ALIVEFILE "$url\n";
        }
      }
   }
}

sub PauseRoutine {
   if ($slp > 0) {
      print "Pausing for $slp seconds...\n\n"; sleep $slp;
   } else { }						# don't pause - go on to the next URL
}
