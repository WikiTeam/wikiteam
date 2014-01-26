Description
-----------
checkalive.pl is a Perl script that will go thru a list of URLs & determine if they are online and if they are Mediawiki wikis. It should work with "index.php/Main_Page", "index.php" and "api.php". As of 01/23/2014, I have started using version numbers.

Required programs and modules
-----------------------------
checkalive.pl has been developed in Linux, and of course requires Perl 5.x to be on your system. You will also need to have the following Perl modules installed:
LWP::Simple
LWP::UserAgent
Crypt::SSLeay
The first two are contained in LWP - The World-Wide Web library for Perl (aka: libwww-perl-6.x), available at CPAN, or through  your Linux distro's package manager.
Crypt::SSLeay (OpenSSL support for LWP) is also available at CPAN. This module is needed to properly handle any URLs beginning with "https".

Configuration
-------------
There are several variables you can change, or you can just use them as-is: 
-- "$slp" is the number of seconds to sleep between requests (currently set to 2 seconds).
-- "$urllist" is for the name of the file that contains the list of URLs to check (currently set to 'URL-list.txt'). If you don't want to change this variable, make sure your list is named 'URL-list.txt'.
--"$alivelist" is the file that will contain the list of URLs that are both online AND powered by MediaWiki. 
--"$deadlist" is the file that will contain the list of URLs that don't meet the above criteria. URLs that are online and NOT powered by MediaWiki are also in this file, and will be noted as such.
Any other variable that you want to change - you do so at your own risk.

Issues
------
The script does NOT have a "resume" feature at this time. If you are running through a list of 1000's of URLs, and the script crashes, or you kill it, your lists of alive and dead URLs will NOT BE SAVED TO DISK. I suggest breaking up your list into smaller lists of a few hundred URLs in each list until I can implement a resume feature.

The LWP library does transparent redirect handling, so I can't capture the new URL that is displayed on screen as the script is running. Therefore, any of the URLs that get redirected to a new URL will have the original URL saved to the appropriate list (whether it's dead or alive).

