# WikiTeam
### We archive wikis, from Wikipedia to tiniest wikis

**WikiTeam software is a set of tools for archiving wikis.** They work on MediaWiki wikis, but we want to expand to other wiki engines. As of June 2014, WikiTeam has preserved more than [13,000 stand-alone wikis](https://github.com/WikiTeam/wikiteam/wiki/Available-Backups), several wikifarms, regular Wikipedia dumps and [24TB of Wikimedia Commons images](https://archive.org/details/wikimediacommons).

There are [thousands](http://wikiindex.org) of [wikis](https://wikiapiary.com) in the Internet. Every day some of them are no longer publicly available and, due to lack of backups, lost forever. Millions of people download tons of media files (movies, music, books, etc) from the Internet, serving as a kind of distributed backup. Wikis, most of them under free licenses, disappear from time to time because nobody grabbed a copy of them. That is a shame that we would like to solve.

**WikiTeam** is the [Archive Team](http://www.archiveteam.org) ([GitHub](https://github.com/ArchiveTeam)) subcommittee on wikis. It was founded and originally developed by [Emilio J. Rodríguez-Posada](https://github.com/emijrp), a Wikipedia veteran editor and amateur archivist. Many people have helped by sending suggestions, [reporting bugs](https://github.com/WikiTeam/wikiteam/issues), writing [documentation](https://github.com/WikiTeam/wikiteam/wiki), providing help in the [mailing list](http://groups.google.com/group/wikiteam-discuss) and making [wiki backups](https://github.com/WikiTeam/wikiteam/wiki/Available-Backups). Thanks to all, especially to: [Federico Leva](https://github.com/nemobis), [Alex Buie](https://github.com/ab2525), [Scott Boyd](http://www.sdboyd56.com), [Hydriz](https://github.com/Hydriz), Platonides, Ian McEwen, [Mike Dupont](https://github.com/h4ck3rm1k3) and [balrog](https://github.com/balr0g).

<table border=0 cellpadding=5px>
<tr><td>
<a href="https://github.com/WikiTeam/wikiteam/wiki/New-Tutorial"><img src="https://upload.wikimedia.org/wikipedia/commons/f/f3/Nuvola_apps_Wild.png" width=100px alt="Documentation" title="Documentation"/></a>
</td><td>
<a href="https://raw.githubusercontent.com/WikiTeam/wikiteam/master/dumpgenerator.py"><img src="http://upload.wikimedia.org/wikipedia/commons/2/2a/Nuvola_apps_kservices.png" width=100px alt="Source code" title="Source code"/></a>
</td><td>
<a href="https://github.com/WikiTeam/wikiteam/wiki/Available-Backups"><img src="https://upload.wikimedia.org/wikipedia/commons/3/37/Nuvola_devices_3floppy_mount.png" width=100px alt="Download available backups" title="Download available backups"/></a>
</td><td>
<a href="https://groups.google.com/group/wikiteam-discuss"><img src="https://upload.wikimedia.org/wikipedia/commons/0/0f/Nuvola_apps_kuser.png" width=100px alt="Community" title="Community"/></a>
</td><td>
<a href="https://twitter.com/_WikiTeam"><img src="https://upload.wikimedia.org/wikipedia/commons/e/eb/Twitter_logo_initial.png" width=90px alt="Follow us on Twitter" title="Follow us on Twitter"/></a>
</td></tr>
</table>

## Quick guide

This is a very quick guide for the most used features of WikiTeam tools. For further information, read the [tutorial](https://github.com/WikiTeam/wikiteam/wiki/New-Tutorial) and the rest of the [documentation](https://github.com/WikiTeam/wikiteam/wiki). You can also ask in the [mailing list](http://groups.google.com/group/wikiteam-discuss).

### Download any wiki

For downloading any wiki, use one of the following options:

`python dumpgenerator.py --api=http://wiki.domain.org/w/api.php --xml --images` (complete XML histories and images)

`python dumpgenerator.py --api=http://wiki.domain.org/w/api.php --xml` (complete XML histories)

`python dumpgenerator.py --api=http://wiki.domain.org/w/api.php --xml --curonly` (only current version of every page)

You can resume an aborted download:

`python dumpgenerator.py --api=http://wiki.domain.org/w/api.php --xml --images --resume --path=/path/to/incomplete-dump`

See more options:

`python dumpgenerator.py --help`

### Download Wikimedia dumps

For downloading [Wikimedia XML dumps](http://dumps.wikimedia.org/backup-index.html) (Wikipedia, Wikibooks, Wikinews, etc):

`python wikipediadownloader.py` (download all projects)

See more options:

`python wikipediadownloader.py --help`

### Download Wikimedia Commons images

There is a script for this, but we have [uploaded the tarballs](https://archive.org/details/wikimediacommons) to Internet Archive, so perhaps it is a better option download them from IA instead re-generating them with the script.
