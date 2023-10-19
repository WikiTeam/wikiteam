# Usage

## `Dumpgenerator`

`MediaWiki Dump Generator` has been tested on Linux, macOS, Windows and Android. If you are connecting to Linux or macOS via `ssh`, you can continue using the `bash` or `zsh` command prompt in the same terminal, but if you are starting in a desktop environment and don't already have a preferred Terminal see the INSTALLATION.md document.

After installing `MediaWiki Dump Generator` you should be able to use the `dumpgenerator` command from any local directory. Run `dumpgenerator` in the directory where you'd like the download to be:

```bash
dumpgenerator [args]
```

For a brief summary of the `dumpgenerator` command-line options:

```bash
dumpgenerator --help
```

Several examples follow.

> **Note:** the `\` and line breaks in the examples below are for legibility in this documentation. Run `dumpgenerator` with the arguments in a single line and a single space between.

### Downloading a wiki with complete XML history and images

```bash
dumpgenerator http://wiki.domain.org --xml --images
```

### Manually specifying `api.php` and/or `index.php`

If the script itself can't find the `api.php` and/or `index.php` paths, then you can provide them. To find api.php on a particular wiki, see section "Entry point URLs" on the Special:Version page.

```bash
dumpgenerator --api http://wiki.domain.org/w/api.php --xml --images
```

```bash
dumpgenerator --api http://wiki.domain.org/w/api.php --index http://wiki.domain.org/w/index.php \
    --xml --images
```

If you only want the XML histories, just use `--xml`. For only the images, just `--images`. For only the current version of every page, `--xml --curonly`.

To dump a private wiki you will have to use a login which has at the least read permission on that wiki.

### Resuming an incomplete dump

```bash
dumpgenerator \
    --api http://wiki.domain.org/w/api.php --xml --images --resume --path /path/to/incomplete-dump
```

In the above example, `--path` is only necessary if the download path is not the default.

`dumpgenerator` will also ask you if you want to resume if it finds an incomplete dump in the path where it is downloading.

### Checking dump integrity

If you want to check the XML dump integrity, type this into your command line to count title, page and revision XML tags:

```bash
grep -Ec "<title(.*?)>" *.xml;grep -Ec "<page(.*?)>" *.xml;grep -Ec "</page>" *.xml; \
    grep -Ec "<revision(.*?)>" *.xml;grep -Ec "</revision>" *.xml
```

You should see something similar to this (not the actual numbers) - the first three numbers should be the same and the last two should be the same as each other:

```bash
580
580
580
5677
5677
```

If your first three numbers or your last two numbers are different, then, your XML dump is corrupt (it contains one or more unfinished ```</page>``` or ```</revision>```). This is not common in small wikis, but large or very large wikis may fail at this due to truncated XML pages while exporting and merging. The solution is to remove the XML dump and re-download, a bit boring, and it can fail again.

## Viewing MediaWiki XML Dumps

* [XML namespaces](https://www.mediawiki.org/xml/)
* [XML export format](https://www.mediawiki.org/wiki/Help:Export#Export_format)

## Publishing the dump

Please consider publishing your wiki dump(s). You can do it yourself as explained in [Publishing](./PUBLISHING.md).

## `Launcher`

The script `launcher` is a way to download a list of wikis with a single invocation.

Usage:

```bash
launcher path-to-apis.txt [--7z-path path-to-7z] [--generator-arg=--arg] ...
```

`launcher` will download a complete dump (XML and images) for a list of wikis, then compress the dump into two `7z` files: `history` (containing only metadata and the XML history of the wiki) and `wikidump` (containing metadata, XML, and images). This is the format that is suitable for upload to a WikiTeam item on the Internet Archive.

`launcher` will resume incomplete dumps as appropriate and will not attempt to download wikis that have already been downloaded (as determined by the files existing in the working directory).

Each wiki will be stored into files contiaining a stripped version of the url and the date the dump was started.

`path-to-apis.txt` is a path to a file that contains a list only of URLs to `api.php`s of wikis, one on each line.

By default, a `7z` executable is found on `PATH`. The `--7z-path` argument can be used to use a specific executable instead.

The `--generator-arg` or `-g` argument can be used on the command line to pass through arguments to the `generator` instances that are spawned. For example:
- `--generator-arg=--xmlrevisions` to use the modern MediaWiki API for retrieving revisions
- `--generator-arg=--delay=2` to use a delay of 2 seconds between requests
- `-g=--user -g=USER -g=--pass -g=PASSWORD` to dump a wiki that only logged in users can read

## `Uploader`

The script `uploader` is a way to upload a set of already-generated wiki dumps to the Internet Archive with a single invocation.

Usage:

```bash
uploader [-pd] [-pw] [-a] [-c COLLECTION] [-wd WIKIDUMP_DIR] [-u] [-kf KEYSFILE] [-lf LOGFILE] listfile
```

For the positional parameter `listfile`, `uploader` expects a path to a file that contains a list of URLs to `api.php`s of wikis, one on each line (exactly the same as `launcher`).

`uploader` will search a configurable directory for files with the names generated by `launcher` and upload any that it finds to an Internet Archive item. The item will be created if it does not already exist.

Named arguments (short and long versions):

* `-pd`, `--prune_directories`: After uploading, remove the raw directory generated by `launcher`
* `-pw`, `--prune_wikidump`: After uploading, remove the `wikidump.7z` file generated by `launcher`
* `-c`, `--collection`: Assign the Internet Archive items to the specified collection
* `-a`, `--admin`: Used only if you are an admin of the WikiTeam collection on the Internet Archive
* `-wd`, `--wikidump_dir`: The directory to search for dumps. Defaults to `.`.
* `-u`, `--update`: Update the metadata on an existing Internet Archive item
* `-kf`, `--keysfile`: Path to a file containing Internet Archive API keys. Should contain two lines: the access key, then the secret key. Defaults to `./keys.txt`.
* `-lf`, `--logfile`: Where to store a log of uploaded files (to reduce duplicate work). Defaults to `uploader-X.txt`, where `X` is the final part of the `listfile` path.

## Restoring a wiki

To restore a wiki from a wikidump follow the instructions at MediaWiki's [Manual:Restoring a wiki from backup](https://www.mediawiki.org/wiki/Manual:Restoring_a_wiki_from_backup).
