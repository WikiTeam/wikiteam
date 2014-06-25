# WikiTeam
### We archive wikis, from Wikipedia to tiniest wikis

**WikiTeam software is a set of tools for archiving wikis.** They work on MediaWiki wikis, but we want to expand to other wiki engines. As of June 2014, WikiTeam has preserved more than [13,000 stand-alone wikis](https://wikiapiary.com/wiki/WikiTeam_websites), several wikifarms, regular Wikipedia dumps and [24TB of Wikimedia Commons images](https://archive.org/details/wikimediacommons).

There are [thousands](http://wikiindex.org) of [wikis](https://wikiapiary.com) in the Internet. Everyday some of them are no longer publicly available and, due to lack of backups, lost forever. Millions of people download tons of media files (movies, music, books, etc) from the Internet, implementing a kind of distributed backup. Wikis, most of them under free licenses, disappear from time to time because nobody grabbed a copy of them. That is a shame that we would like to solve.

**WikiTeam** is the [Archive Team](http://www.archiveteam.org) subcommittee on wikis. It was founded and originally developed by [Emilio J. Rodríguez-Posada](https://github.com/emijrp), a Wikipedia veteran editor and amateur archivist. Many people have help sending suggestions, [reporting bugs](https://github.com/WikiTeam/wikiteam/issues), writing [documentation](https://github.com/WikiTeam/wikiteam/wiki), providing help in the [mailing list](http://groups.google.com/group/wikiteam-discuss) and making wiki backups. Thanks to all, especially to: [Federico Leva](https://github.com/nemobis), [Alex Buie](https://github.com/ab2525), [Scott Boyd](http://www.sdboyd56.com), [Hydriz](https://github.com/Hydriz), Platonides, Ian McEwen and [Mike Dupont](https://github.com/h4ck3rm1k3).

<table border=0 cellpadding=5px>
<tr><td>
<a href="http://code.google.com/p/wikiteam/wiki/NewTutorial"><img src="http://upload.wikimedia.org/wikipedia/commons/f/f3/Nuvola_apps_Wild.png" width=100px alt="Documentation" title="Documentation"/></a>
</td><td>
<a href="http://code.google.com/p/wikiteam/source/browse/trunk/dumpgenerator.py"><img src="http://upload.wikimedia.org/wikipedia/commons/2/2a/Nuvola_apps_kservices.png" width=100px alt="Source code" title="Source code"/></a>
</td><td>
<a href="http://code.google.com/p/wikiteam/wiki/AvailableBackups"><img src="http://upload.wikimedia.org/wikipedia/commons/3/37/Nuvola_devices_3floppy_mount.png" width=100px alt="Download available backups" title="Download available backups"/></a>
</td><td>
<a href="http://groups.google.com/group/wikiteam-discuss"><img src="http://upload.wikimedia.org/wikipedia/commons/0/0f/Nuvola_apps_kuser.png" width=100px alt="Community" title="Community"/></a>
</td><td>
<a href="http://twitter.com/#!/_WikiTeam"><img src="http://upload.wikimedia.org/wikipedia/commons/e/eb/Twitter_logo_initial.png" width=90px alt="Follow us on Twitter" title="Follow us on Twitter"/></a>
</td></tr>
</table>

## Quick guide

For downloading a wiki, including the complete XML history and all images, use:

`python dumpgenerator.py --api=http://en.wikipedia.org/w/api.php --xml --images`
