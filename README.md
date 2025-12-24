# `wikiteam3`

![Dynamic JSON Badge](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Farchive.org%2Fadvancedsearch.php%3Fq%3Dsubject%3Awikiteam3%26rows%3D1%26page%3D1%26output%3Djson&query=%24.response.numFound&label=WikiTeam3%20Dumps%40IA)
[![PyPI version](https://badge.fury.io/py/wikiteam3.svg)](https://badge.fury.io/py/wikiteam3)

<!-- !["MediaWikiArchive.png"](./MediaWikiArchive.png) -->
<div align=center><img width = "150" height ="150" src ="https://raw.githubusercontent.com/saveweb/wikiteam3/v4-main/MediaWikiArchive.png"/></div>

> Countless MediaWikis are still waiting to be archived.
>
> _Image by [@gledos](https://github.com/gledos/)_

`wikiteam3` is a fork of `mediawiki-scraper`.

<details>

## Why we fork mediawiki-scraper

Originally, mediawiki-scraper was named wikiteam3, but wikiteam upstream (py2 version) suggested that the name should be changed to avoid confusion with the original wikiteam.  
Half a year later, we didn't see any py3 porting progress in the original wikiteam, and mediawiki-scraper lacks "code" reviewers.  
So, we decided to break that suggestion, fork and named it back to wikiteam3, put the code here, and release it to pypi wildly.

Everything still under GPLv3 license.

</details>

## For webmaster

We archive every MediaWiki site yearly and upload to the Internet Archive.
We crawl sites with 1.5s crawl-delay by default, and we respect Retry-After header.
If you don’t want your wiki to be archived, add the following to your `<domain>/robots.txt`:

```robots.txt
User-agent: wikiteam3
Disallow: /
```

Our bots are running on the following IPs: [wikiteam3.txt](https://static.saveweb.org/bots_ips/wikiteam3.txt) (ips+info) | [wikiteam3.ips.txt](https://static.saveweb.org/bots_ips/wikiteam3.ips.txt) (ips)

## Installation/Upgrade

```shell
pip install wikiteam3 --upgrade
```

>[!NOTE]
> For public MediaWiki, you don't need to install wikiteam3 locally. You can send an archive request (include the reason for the archive request, e.g. wiki is about to shutdown, need a wikidump to migrate to another wikifarm, etc.) to the wikiteam IRC channel. An online member will run a [wikibot](https://wikibot.digitaldragon.dev/) job for your request.
>
> Even more, we also accept DokuWiki and PukiWiki archive requests.
> 
> - wikiteam IRC (webirc): <https://chat.hackint.org/?join=%23wikiteam>
> - wikiteam IRC logs: https://irclogs.archivete.am/wikiteam

## Dumpgenerator usage

<!-- DUMPER -->
<details>

```bash
usage: wikiteam3dumpgenerator [-h] [-v] [--cookies cookies.txt] [--delay 1.5]
                              [--retries 5] [--hard-retries 3] [--path PATH]
                              [--resume] [--force] [--user USER]
                              [--pass PASSWORD] [--http-user HTTP_USER]
                              [--http-pass HTTP_PASSWORD]
                              [--http-method {GET,POST}] [--insecure]
                              [--verbose] [--api_chunksize 50] [--api API]
                              [--index INDEX] [--index-check-threshold 0.80]
                              [--xml] [--curonly] [--xmlapiexport]
                              [--xmlrevisions] [--xmlrevisions_page]
                              [--redirects] [--namespaces 1,2,3] [--images]
                              [--bypass-cdn-image-compression]
                              [--image-timestamp-interval 2019-01-02T01:36:06Z/2023-08-12T10:36:06Z]
                              [--ia-wbm-booster {0,1,2,3}]
                              [--assert-max-pages 123]
                              [--assert-max-edits 123]
                              [--assert-max-images 123]
                              [--assert-max-images-bytes 123]
                              [--get-wiki-engine] [--failfast] [--upload]
                              [-g UPLOADER_ARGS]
                              [wiki]

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  --cookies cookies.txt
                        path to a cookies.txt file
  --delay 1.5           adds a delay (in seconds) [NOTE: most HTTP servers
                        have a 5s HTTP/1.1 keep-alive timeout, you should
                        consider it if you wanna reuse the connection]
  --retries 5           Maximum number of retries for each request before
                        failing.
  --hard-retries 3      Maximum number of hard retries for each request before
                        failing. (for now, this only controls the hard retries
                        during images downloading)
  --path PATH           path to store wiki dump at
  --resume              resumes previous incomplete dump (requires --path)
  --force               download it even if Wikimedia site or a recent dump
                        exists in the Internet Archive
  --user USER           Username if MediaWiki authentication is required.
  --pass PASSWORD       Password if MediaWiki authentication is required.
  --http-user HTTP_USER
                        Username if HTTP authentication is required.
  --http-pass HTTP_PASSWORD
                        Password if HTTP authentication is required.
  --http-method {GET,POST}
                        HTTP method to use when making API requests to the
                        wiki (default: POST)
  --insecure            Disable SSL certificate verification
  --verbose
  --api_chunksize 50    Chunk size for MediaWiki API (arvlimit, ailimit, etc.)

  wiki                  URL to wiki (e.g. http://wiki.domain.org), auto
                        detects API and index.php
  --api API             URL to API (e.g. http://wiki.domain.org/w/api.php)
  --index INDEX         URL to index.php (e.g.
                        http://wiki.domain.org/w/index.php), (not supported
                        with --images on newer(?) MediaWiki without --api)
  --index-check-threshold 0.80
                        pass index.php check if result is greater than (>)
                        this value (default: 0.80)

Data to download:
  What info download from the wiki

  --xml                 Export XML dump using Special:Export (index.php).
                        (supported with --curonly)
  --curonly             store only the latest revision of pages
  --xmlapiexport        Export XML dump using API:revisions instead of
                        Special:Export, use this when Special:Export fails and
                        xmlrevisions not supported. (supported with --curonly)
  --xmlrevisions        Export all revisions from an API generator
                        (API:Allrevisions). MediaWiki 1.27+ only. (not
                        supported with --curonly)
  --xmlrevisions_page   [[! Development only !]] Export all revisions from an
                        API generator, but query page by page MediaWiki 1.27+
                        only. (default: --curonly)
  --redirects           Dump page redirects via API:Allredirects
  --namespaces 1,2,3    comma-separated value of namespaces to include (all by
                        default)
  --images              Generates an image dump

Image dump options:
  Options for image dump (--images)

  --bypass-cdn-image-compression
                        Bypass CDN image compression. (CloudFlare Polish,
                        etc.) [WARNING: This will increase CDN origin traffic,
                        and not effective for all HTTP Server/CDN, please
                        don't use this blindly.]
  --image-timestamp-interval 2019-01-02T01:36:06Z/2023-08-12T10:36:06Z
                        Only download images uploaded in the given time
                        interval. [format: ISO 8601 UTC interval] (only works
                        with api)
  --ia-wbm-booster {0,1,2,3}
                        Download images from Internet Archive Wayback Machine
                        if possible, reduce the bandwidth usage of the wiki.
                        [0: disabled (default), 1: use earliest snapshot, 2:
                        use latest snapshot, 3: the closest snapshot to the
                        image's upload time]

Assertions:
  What assertions to check before actually downloading, if any assertion
  fails, program will exit with exit code 45. [NOTE: This feature requires
  correct siteinfo API response from the wiki, and not working properly with
  some wikis. But it's useful for mass automated archiving, so you can
  schedule a re-run for HUGE wiki that may run out of your disk]

  --assert-max-pages 123
                        Maximum number of pages to download
  --assert-max-edits 123
                        Maximum number of edits to download
  --assert-max-images 123
                        Maximum number of images to download
  --assert-max-images-bytes 123
                        Maximum number of bytes to download for images [NOTE:
                        this assert happens after downloading images list]

Meta info:
  What meta info to retrieve from the wiki

  --get-wiki-engine     returns the wiki engine
  --failfast            [lack maintenance] Avoid resuming, discard failing
                        wikis quickly. Useful only for mass downloads.

wikiteam3uploader params:
  --upload              (run `wikiteam3uplaoder` for you) Upload wikidump to
                        Internet Archive after successfully dumped
  -g, --uploader-arg UPLOADER_ARGS
                        Arguments for uploader.

```
</details>

<!-- DUMPER -->

### Downloading a wiki with complete XML history and images

```bash
wikiteam3dumpgenerator http://wiki.domain.org --xml --images
```

>[!WARNING]
>
> `NTFS/Windows` users please note: When using `--images`, because NTFS does not allow characters such as `:*?"<>|` in filenames, some files may not be downloaded, please pay attention to the `XXXXX could not be created by OS` error in your `errors.log`.
> We will not make special treatment for NTFS/EncFS "path too long/illegal filename", highly recommend you to use ext4/xfs/btrfs, etc.
> <details>
> - Introducing the "illegal filename rename" mechanism will bring complexity. WikiTeam(python2) had this before, but it caused more problems, so it was removed in WikiTeam3.
> - It will cause confusion to the final user of wikidump (usually the Wiki site administrator).
> - NTFS is not suitable for large-scale image dump with millions of files in a single directory.(Windows background service will occasionally scan the whole disk, we think there should be no users using WIN/NTFS to do large-scale MediaWiki archive)
> - Using other file systems can solve all problems.
> </details>

### Manually specifying `api.php` and/or `index.php`

If the script can't find itself the `api.php` and/or `index.php` paths, then you can provide them:

```bash
wikiteam3dumpgenerator --api http://wiki.domain.org/w/api.php --xml --images
```

```bash
wikiteam3dumpgenerator --api http://wiki.domain.org/w/api.php --index http://wiki.domain.org/w/index.php \
    --xml --images
```

If you only want the XML histories, just use `--xml`. For only the images, just `--images`. For only the current version of every page, `--xml --curonly`.

### Resuming an incomplete dump

<details>

```bash
wikiteam3dumpgenerator \
    --api http://wiki.domain.org/w/api.php --xml --images --resume --path /path/to/incomplete-dump
```

In the above example, `--path` is only necessary if the download path (wikidump dir) is not the default.

>[!NOTE]
>
> en: When resuming an incomplete dump, the configuration in `config.json` will override the CLI parameters. (But not all CLI parameters will be ignored, check `config.json` for details)

`wikiteam3dumpgenerator` will also ask you if you want to resume if it finds an incomplete dump in the path where it is downloading.

</details>

## Using `wikiteam3uploader`

<!-- UPLOADER -->
<details>

```bash
usage:  Upload wikidump to the Internet Archive. [-h] [-kf KEYS_FILE]
                                                 [-c COLLECTION] [--dry-run]
                                                 [-u] [--bin-zstd BIN_ZSTD]
                                                 [--zstd-level {17,18,19,20,21,22}]
                                                 [--rezstd]
                                                 [--rezstd-endpoint URL]
                                                 [--bin-7z BIN_7Z]
                                                 [--parallel]
                                                 wikidump_dir

positional arguments:
  wikidump_dir

options:
  -h, --help            show this help message and exit
  -kf, --keys_file KEYS_FILE
                        Path to the IA S3 keys file. (first line: access key,
                        second line: secret key) [default:
                        ~/.wikiteam3_ia_keys.txt]
  -c, --collection COLLECTION
  --dry-run             Dry run, do not upload anything.
  -u, --update          Update existing item. [!! not implemented yet !!]
  --bin-zstd BIN_ZSTD   Path to zstd binary. [default: zstd]
  --zstd-level {17,18,19,20,21,22}
                        Zstd compression level. [default: 17] If you have a
                        lot of RAM, recommend to use max level (22).
  --rezstd              [server-side recompression] Upload pre-compressed zstd
                        files to rezstd server for recompression with best
                        settings (which may eat 10GB+ RAM), then download
                        back. (This feature saves your lowend machine, lol)
  --rezstd-endpoint URL
                        Rezstd server endpoint. [default: http://pool-
                        rezstd.saveweb.org/rezstd/] (source code:
                        https://github.com/yzqzss/rezstd)
  --bin-7z BIN_7Z       Path to 7z binary. [default: 7z]
  --parallel            Parallelize compression tasks

```
</details>

<!-- UPLOADER -->

### Requirements

> [!NOTE]
>
> Please make sure you have the following requirements before using `wikiteam3uploader`, and you don't need to install them if you don't wanna upload the dump to IA.

- unbinded localhost port 62954 (for multiple processes compressing queue)
- 3GB+ RAM (~2.56GB for commpressing)
- 64-bit OS (required by 2G `wlog` size)

- `7z` (binary)
    > Debian/Ubuntu: install `p7zip-full`  

    > [!NOTE]
    >
    > Windows: install <https://7-zip.org> and add `7z.exe` to PATH
- `zstd` (binary)
    > 1.5.5+ (recommended), v1.5.0-v1.5.4(DO NOT USE), 1.4.8 (minimum)  
    > install from <https://github.com/facebook/zstd>  

    > [!NOTE]
    >
    > Windows: add `zstd.exe` to PATH

### Uploader usage

> [!NOTE]
>
> Read `wikiteam3uploader --help` and do not forget `~/.wikiteam3_ia_keys.txt` before using `wikiteam3uploader`.

```bash
wikiteam3uploader {YOUR_WIKI_DUMP_PATH}
```

## Checking dump integrity

TODO: xml2titles.py

If you want to check the XML dump integrity, type this into your command line to count title, page and revision XML tags:

```bash
grep -E '<title(.*?)>' *.xml -c; grep -E '<page(.*?)>' *.xml -c; grep \
    "</page>" *.xml -c;grep -E '<revision(.*?)>' *.xml -c;grep "</revision>" *.xml -c
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

## import wikidump to MediaWiki / wikidump data tips

> [!IMPORTANT]
>
> In the article name, spaces and underscores are treated as equivalent and each is converted to the other in the appropriate context (underscore in URL and database keys, spaces in plain text). <https://www.mediawiki.org/wiki/Manual:Title.php#Article_name>

> [!NOTE]
>
> `WikiTeam3` uses `zstd` to compress `.xml` and `.txt` files, and `7z` to pack images (media files).  
> `zstd` is a very fast stream compression algorithm, you can use `zstd -d` to decompress `.zst` file/steam.

## Contributors

**WikiTeam** is the [Archive Team](http://www.archiveteam.org) [[GitHub](https://github.com/ArchiveTeam)] subcommittee on wikis.
It was founded and originally developed by [Emilio J. Rodríguez-Posada](https://github.com/emijrp), a Wikipedia veteran editor and amateur archivist. Thanks to people who have helped, especially to: [Federico Leva](https://github.com/nemobis), [Alex Buie](https://github.com/ab2525), [Scott Boyd](http://www.sdboyd56.com), [Hydriz](https://github.com/Hydriz), Platonides, Ian McEwen, [Mike Dupont](https://github.com/h4ck3rm1k3), [balr0g](https://github.com/balr0g) and [PiRSquared17](https://github.com/PiRSquared17).

**Mediawiki-Scraper** The Python 3 initiative is currently being led by [Elsie Hupp](https://github.com/elsiehupp), with contributions from [Victor Gambier](https://github.com/vgambier), [Thomas Karcher](https://github.com/t-karcher), [Janet Cobb](https://github.com/randomnetcat), [yzqzss](https://github.com/yzqzss), [NyaMisty](https://github.com/NyaMisty) and [Rob Kam](https://github.com/robkam)

**WikiTeam3** Every archivist who has uploaded a wikidump to the [Internet Archive](https://archive.org/search?query=subject%3Awikiteam3).
