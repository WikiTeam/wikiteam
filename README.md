# WikiTeam
### We archive wikis, from Wikipedia to tiniest wikis

**WikiTeam software is a set of tools for archiving wikis.** They work on MediaWiki wikis, but we want to expand to other wiki engines. As of 2020, WikiTeam has preserved more than [250,000 wikis](https://github.com/WikiTeam/wikiteam/wiki/Available-Backups), several wikifarms, regular Wikipedia dumps and [34 TB of Wikimedia Commons images](https://archive.org/details/wikimediacommons).

There are [thousands](http://wikiindex.org) of [wikis](https://wikiapiary.com) in the Internet. Every day some of them are no longer publicly available and, due to lack of backups, lost forever. Millions of people download tons of media files (movies, music, books, etc) from the Internet, serving as a kind of distributed backup. Wikis, most of them under free licenses, disappear from time to time because nobody grabbed a copy of them. That is a shame that we would like to solve.

**WikiTeam** is the [Archive Team](http://www.archiveteam.org) ([GitHub](https://github.com/ArchiveTeam)) subcommittee on wikis. It was founded and originally developed by [Emilio J. Rodríguez-Posada](https://github.com/emijrp), a Wikipedia veteran editor and amateur archivist. Many people have helped by sending suggestions, [reporting bugs](https://github.com/WikiTeam/wikiteam/issues), writing [documentation](https://github.com/WikiTeam/wikiteam/wiki), providing help in the [mailing list](http://groups.google.com/group/wikiteam-discuss) and making [wiki backups](https://github.com/WikiTeam/wikiteam/wiki/Available-Backups). Thanks to all, especially to: [Federico Leva](https://github.com/nemobis), [Alex Buie](https://github.com/ab2525), [Scott Boyd](http://www.sdboyd56.com), [Hydriz](https://github.com/Hydriz), Platonides, Ian McEwen, [Mike Dupont](https://github.com/h4ck3rm1k3), [balr0g](https://github.com/balr0g) and [PiRSquared17](https://github.com/PiRSquared17).

<table border=0 cellpadding=5px>
<tr><td>
<a href="https://github.com/WikiTeam/wikiteam/wiki/Tutorial"><img src="https://upload.wikimedia.org/wikipedia/commons/f/f3/Nuvola_apps_Wild.png" width=100px alt="Documentation" title="Documentation"/></a>
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

This is a very quick guide for the most used features of WikiTeam tools. For further information, read the [tutorial](https://github.com/WikiTeam/wikiteam/wiki/Tutorial) and the rest of the [documentation](https://github.com/WikiTeam/wikiteam/wiki). You can also ask in the [mailing list](http://groups.google.com/group/wikiteam-discuss).

### Python Environment

WikiTeam requires [Python 2.7(https://www.python.org/downloads/release/python-278/). However, as Python 2.7 [reached the end of its official service life on January 1st, 2020](https://pip.pypa.io/en/latest/development/release-process/#python-2-support), modern operating systems no longer offer a working Python 2.7 environment by default. Therefore, most users will have to install a virtual environment such as `miniconda`.

Per-platform instructions for `miniconda` can be found [here](https://docs.conda.io/en/latest/miniconda.html). Generic instructions for Linux x86-64 will continue below.

### Generic `miniconda` Instructions for Linux x86-64

If you don't have `wget`, you will need to install it first (or use `curl` or another download method).

1. Download `miniconda`:
```bash
$ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```
2. Install
```bash
$ bash Miniconda3-latest-Linux-x86_64.sh
```
3. Restart `bash`:
```bash
$ exec bash
```
4. Update `conda`:
```bash
$ conda update -n base -c defaults conda
```
> You'll probably want to turn off `conda`'s autorun for your default shell environment:
> ```bash
> $ conda config --set auto_activate_base false
> ```
6. Create a new `conda` environment for `wikiteam` titled, e.g., 'wikiteam_env':
```bash
$ conda create -n wikiteam_env
```
7. Enter your new `conda` environemnt:
```bash
$ conda activate wikiteam_env
```
8. Install Python 2.7 in order to run `wikiteam`
```bash
conda install python=2.7
```
> This python version 2.7 is only accessible from within the conda environment 'wikiteam_env' and does not affect the system files. The binaries are stored in your home directory, and none of this requires root access as you are not changing system files.

When you're done working in the `wikiteam` `conda` environment, you'll probably want to exit to the default environment, either by starting a new shell or with the following command:
```bash
$ conda deactivate
```

### Requirements

Once you have a working Python 2.7 environment set up and activate, check and install `wikiteam`'s Python dependencies:
```bash
$ pip install --upgrade -r requirements.txt
```
Or, if you don't have enough permissions for the above,
```bash
$ pip install --user --upgrade -r requirements.txt
```
To check to see if `wikiteam` is properly set up, try:
```bash
$ ./dumpgenerator.py --version
```

### Download any wiki

To download any wiki, use one of the following options:

`python dumpgenerator.py http://wiki.domain.org --xml --images` (complete XML histories and images)

If the script can't find itself the API and/or index.php paths, then you can provide them:

`python dumpgenerator.py --api=http://wiki.domain.org/w/api.php --xml --images`

`python dumpgenerator.py --api=http://wiki.domain.org/w/api.php --index=http://wiki.domain.org/w/index.php --xml --images`

If you only want the XML histories, just use `--xml`. For only the images, just `--images`. For only the current version of every page, `--xml --curonly`.

You can resume an aborted download:

`python dumpgenerator.py --api=http://wiki.domain.org/w/api.php --xml --images --resume --path=/path/to/incomplete-dump`

See more options:

`python dumpgenerator.py --help`

### Download Wikimedia dumps

To download [Wikimedia XML dumps](http://dumps.wikimedia.org/backup-index.html) (Wikipedia, Wikibooks, Wikinews, etc) you can run:

`python wikipediadownloader.py` (download all projects)

See more options:

`python wikipediadownloader.py --help`

### Download Wikimedia Commons images

There is a script for this, but we have [uploaded the tarballs](https://archive.org/details/wikimediacommons) to Internet Archive, so it's more useful to reseed their torrents than to re-generate old ones with the script.

## Developers

[![Build Status](https://travis-ci.org/WikiTeam/wikiteam.svg)](https://travis-ci.org/WikiTeam/wikiteam)

You can run tests easily by using the [tox](https://pypi.python.org/pypi/tox) command.  It is probably already present in your operating system, you would need version 1.6.  If it is not, you can download it from pypi with: `pip install tox`.

Example usage:

    $ tox
    py27 runtests: commands[0] | nosetests --nocapture --nologcapture
    Checking http://wiki.annotation.jp/api.php
    Trying to parse かずさアノテーション - ソーシャル・ゲノム・アノテーション.jpg from API
    Retrieving image filenames
    .    Found 266 images
    .
    -------------------------------------------
    Ran 1 test in 2.253s

    OK
    _________________ summary _________________
      py27: commands succeeded
      congratulations :)
    $
