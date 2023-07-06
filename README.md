# `MediaWiki Scraper`

**MediaWiki Scraper can archive wikis from the largest to the tiniest.**

`MediaWiki Scraper` is an ongoing project to port the legacy [`wikiteam`](https://github.com/WikiTeam/wikiteam) toolset to Python 3 and PyPI to make it more accessible for today's archivers.

Most of the focus has been on the core `dumpgenerator` tool, but Python 3 versions of the other `wikiteam` tools may be added over time.

## MediaWiki Scraper Toolset

MediaWiki Scraper is a set of tools for archiving wikis. The main general-purpose module of MediaWiki Scraper is dumpgenerator, which can download XML dumps of MediaWiki sites that can then be parsed or redeployed elsewhere.

## Python Environment

`MediaWiki Scraper` requires [Python 3.8](https://www.python.org/downloads/release/python-380/) or later (less than 4.0), but you may be able to get it run with earlier versions of Python 3. On recent versions of Linux and macOS Python 3.8 should come preinstalled, but on Windows you will need to install it from [python.org](https://www.python.org/downloads/release/python-380/).

`MediaWiki Scraper` has been tested on Linux, macOS, Windows and Android. If you are connecting to Linux or macOS via `ssh`, you can continue using the `bash` or `zsh` command prompt in the same terminal, but if you are starting in a desktop environment and don't already have a preferred Terminal environment you can try one of the following.

> **NOTE:** You may need to update and pre-install dependencies in order for `MediaWiki Scraper` to work properly. Shell commands for these dependencies appear below each item in the list. (Also note that while installing and running `MediaWiki Scraper` itself should not require administrative priviliges, installing dependencies usually will.)

* On desktop Linux you can use the default terminal application such as [Konsole](https://konsole.kde.org/) or [GNOME Terminal](https://help.gnome.org/users/gnome-terminal/stable/).

  <details>
  <summary>Linux Dependencies</summary>

  While most Linux distributions will have Python 3 preinstalled, if you are cloning `MediaWiki Scraper` rather than downloading it directly you may need to install `git`.

  On Debian, Ubuntu, and the like:

  ```bash
  sudo apt update && sudo apt upgrade && sudo install git
  ```

  (On Fedora, Arch, etc., use `dnf`, `pacman`, etc., instead.)

  </details>

* On macOS you can use the built-in application [Terminal](https://support.apple.com/guide/terminal), which is found in `Applications/Utilities`.

  <details>
  <summary>macOS Dependencies</summary>

  While macOS will have Python 3 preinstalled, if you are cloning `MediaWiki Scraper` rather than downloading it directly and you are using an older versions of macOS, you may need to install `git`.

  If `git` is not preinstalled, however, macOS will prompt you to install it the first time you run the command. Therefore, to check whether you have `git` installed or to install `git`, simply run `git` (with no arguments) in Terminal:

  ```bash
  git
  ```

  If `git` is already installed, it will print its usage instructions. If `git` is not preinstalled, the command will pop up a window asking if you want to install Apple's command line developer tools, and clicking "Install" in the popup window will install `git`.

  </details>

* On Windows 10 or Windows 11 you can use [Windows Terminal](https://aka.ms/terminal).

  <details>
  <summary>Windows Dependencies</summary>
  
  The latest version of Python is available from [python.org](https://www.python.org/downloads/). Python will then be available from any Command Prompt or PowerShell session. Optionally, adding C:\Program Files\Git\usr\bin to the PATH environment variable will add some some useful Linux commands and utilities to Command Prompt.
  
  If you are already using the [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/about), you can follow the Linux instructions above. If you don't want to install a full WSL distribution, [Git for Windows](https://gitforwindows.org/) provides Bash emulation, so you can use it as a more lightweight option instead. Git Bash also provides some useful Linux commands and utilities.

  > When installing [Python 3.8](https://www.python.org/downloads/release/python-380/) (from python.org), be sure to check "Add Python to PATH" so that installed Python scripts are accessible from any location. If for some reason installed Python scripts, e.g. `pip`, are not available from any location, you can add Python to the `PATH` environment variable using the instructions [here](https://datatofish.com/add-python-to-windows-path/).
  >
  > And while doing so should not be necessary if you follow the instructions further down and install `MediaWiki Scraper` using `pip`, if you'd prefer that Windows store installed Python scripts somewhere other than the default Python folder under `%appdata%`, you can also add your preferred alternative path such as `C:\Program Files\Python3\Scripts\` or a subfolder of `My Documents`. (You will need to restart any terminal sessions in order for this to take effect.)

  Whenever you'd like to run a Bash session, you can open a Bash terminal prompt from any folder in Windows Explorer by right-clicking and choosing the option from the context menu. (For some purposes you may wish to run Bash as an administrator.) This way you can open a Bash prompt and clone the `MediaWiki Scraper` repository in one location, and subsequently or later open another Bash prompt and run `MediaWiki Scraper` to dump a wiki wherever else you'd like without having to browse to the directory manually using Bash.

  </details>

* On Android you can use [Termux](https://termux.dev).

  <details>
  <summary>Termux Dependencies</summary>

  ```bash
  pkg update && pkg upgrade && pkg install git libxslt python
  ```

  </details>

* On iOS you can use [iSH](https://ish.app/).

  <details>
  <summary>iSH Dependencies</summary>

  ```bash
  apk update && apk upgrade && apk add git py3-pip
  ```

  > **Note:** iSH may automatically quit if your iOS device goes to sleep, and it may lose its status if you switch to another app. You can disable auto-sleep while iSH is running by clicking the gear icon and toggling "Disable Screen Dimming". (You may wish to connect your device to a charger while running iSH.)

  </details>

## Downloading and installing dumpgenerator

The Python 3 port of the `dumpgenerator` module of `wikiteam3` is largely functional and can be installed from a downloaded or cloned copy of this repository.

> If you run into a problem with the version that mostly works, you can [open an Issue](https://github.com/mediawiki-client-tools/mediawiki-scraper/issues/new/choose). Be sure to include the following:
>
> 1. The operating system you're using
> 2. What command you ran that didn't work
> 3. What output was printed to your terminal

### 1. Downloading and installing `MediaWiki Scraper`

In whatever folder you use for cloned repositories:

```bash
git clone https://github.com/mediawiki-client-tools/mediawiki-scraper
```

```bash
cd mediawiki-scraper
```

```bash
poetry update && poetry install && poetry build
```

```bash
pip install --force-reinstall dist/*.whl
```

### 2. Running `dumpgenerator` for whatever purpose you need

```bash
dumpgenerator [args]
```

### 3. Uninstalling the package and deleting the cloned repository when you're done

```shell
pip uninstall wikiteam3
```

```bash
rm -fr [cloned_MediaWiki Scraper_folder]
```

### 4. Updating MediaWiki Scraper

> **Note:** Re-run the following steps each time to reinstall each time the MediaWiki Scraper branch is updated.

```bash
git pull
```

```bash
poetry update && poetry install && poetry build
```

```bash
pip install --force-reinstall dist/*.whl
```

### 5. Manually build and install `MediaWiki Scraper`

If you'd like to manually build and install `MediaWiki Scraper` from a cloned or downloaded copy of this repository, run the following commands from the downloaded base directory:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

```bash
poetry update && poetry install && poetry build
```

```bash
pip install --force-reinstall dist/*.whl
```

### 6. To run the test suite

To run the test suite, run:

```bash
test-dumpgenerator
```

### 7. Switching branches
```bash
git checkout --track origin/python3
```

## Using `dumpgenerator` (once installed)

After installing `MediaWiki Scraper` using `pip` you should be able to use the `dumpgenerator` command from any local directory.

For basic usage, you can run `dumpgenerator` in the directory where you'd like the download to be.

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

If the script can't find itself the `api.php` and/or `index.php` paths, then you can provide them:

```bash
dumpgenerator --api http://wiki.domain.org/w/api.php --xml --images
```

```bash
dumpgenerator --api http://wiki.domain.org/w/api.php --index http://wiki.domain.org/w/index.php \
    --xml --images
```

If you only want the XML histories, just use `--xml`. For only the images, just `--images`. For only the current version of every page, `--xml --curonly`.

### Resuming an incomplete dump

```bash
dumpgenerator \
    --api http://wiki.domain.org/w/api.php --xml --images --resume --path /path/to/incomplete-dump
```

In the above example, `--path` is only necessary if the download path is not the default.

`dumpgenerator` will also ask you if you want to resume if it finds an incomplete dump in the path where it is downloading.

## Using `launcher`

`launcher` is a way to download a large list of wikis with a single invocation.

Usage:
```bash
launcher path-to-apis.txt [--7z-path path-to-7z] [--generator-arg=--arg] ...
```

`launcher` will download a complete dump (XML and images) for a list of wikis, then compress the dump into two `7z` files: `history` (containing only metadata and the XML history of the wiki) and `wikidump` (containing metadata, XML, and images). This is the format that is suitable for upload to a WikiTeam item on the Internet Archive.

`launcher` will resume incomplete dumps as appropriate and will not attempt to download wikis that have already been downloaded (as determined by the files existing in the working directory).

Each wiki will be stored into files contiaining a stripped version of the url and the date the dump was started.

`path-to-apis.txt` is a path to a file that contains a list of URLs to `api.php`s of wikis, one on each line. 

By default, a `7z` executable is found on `PATH`. The `--7z-path` argument can be used to use a specific executable instead.

The `--generator-arg` argument can be used to pass through arguments to the `generator` instances that are spawned. For example, one can use `--generator-arg=--xmlrevisions` to use the modern MediaWiki API for retrieving revisions or `--generator-arg=--delay=2` to use a delay of 2 seconds between requests.

## Using `uploader`

`uploader` is a way to upload a large set of already-generated wiki dumps to the Internet Archive with a single invocation.

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

## Checking dump integrity

If you want to check the XML dump integrity, type this into your command line to count title, page and revision XML tags:

```bash
grep -E '<title(.*?)>' *.xml -c;grep -E '<page(.*?)>' *.xml -c;grep \
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

If your first three numbers or your last two numbers are different, then, your XML dump is corrupt (it contains one or more unfinished ```</page>``` or ```</revision>```). This is not common in small wikis, but large or very large wikis may fail at this due to truncated XML pages while exporting and merging. The solution is to remove the XML dump and re-download, a bit boring, and it can fail again...
## Reporting issues

Please report any issues at [MediaWiki Scraper/issues](https://github.com/mediawiki-client-tools/mediawiki-scraper/issues)
Include the following in your report:
* The commandline you used, with full URL
* Dumpgenerator version, -v option
* Operating system version, e.g. Kubuntu 23.04 / Windows 10
* File system, e.g. EXT4 / NTFS
* Name of the terminal, e.g. Bash / CMD / Powershell
* Python version, e.g. Python 3.11.4 / Python 3.10
* The errors.log file, from the dump folder
* Stdout, copy the text from the terminal window

## Contributors

**WikiTeam** is the [Archive Team](http://www.archiveteam.org) [[GitHub](https://github.com/ArchiveTeam)] subcommittee on wikis.
It was founded and originally developed by [Emilio J. Rodríguez-Posada](https://github.com/emijrp), a Wikipedia veteran editor and amateur archivist. Thanks to people who have helped, especially to: [Federico Leva](https://github.com/nemobis), [Alex Buie](https://github.com/ab2525), [Scott Boyd](http://www.sdboyd56.com), [Hydriz](https://github.com/Hydriz), Platonides, Ian McEwen, [Mike Dupont](https://github.com/h4ck3rm1k3), [balr0g](https://github.com/balr0g) and [PiRSquared17](https://github.com/PiRSquared17).

**MediaWiki Scraper**
The Python 3 initiative is currently being led by [Elsie Hupp](https://github.com/elsiehupp), with contributions from [Victor Gambier](https://github.com/vgambier), [Thomas Karcher](https://github.com/t-karcher), [Janet Cobb](https://github.com/randomnetcat), [yzqzss](https://github.com/yzqzss), [NyaMisty](https://github.com/NyaMisty) and [Rob Kam](https://github.com/robkam)
