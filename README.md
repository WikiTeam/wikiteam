# `wikiteam3`

***We archive wikis, from Wikipedia to the tiniest wikis***

`wikiteam3` is an ongoing project to port the legacy [`wikiteam`](https://github.com/WikiTeam/wikiteam) toolset to Python 3 and PyPI to make it more accessible for today's archivers.

Most of the focus has been on the core `dumpgenerator` tool, but Python 3 versions of the other `wikiteam` tools may be added over time.

## `wikiteam3` Toolset

`wikiteam3` is a set of tools for archiving wikis. The tools work on MediaWiki wikis, but the team hopes to expand to other wiki engines. As of 2020, WikiTeam has preserved more than [250,000 wikis](https://github.com/WikiTeam/wikiteam/wiki/Available-Backups), several wikifarms, regular Wikipedia dumps and [34 TB of Wikimedia Commons images](https://archive.org/details/wikimediacommons).

The main general-purpose module of `wikiteam3` is `dumpgenerator`, which can download XML dumps of MediaWiki sites that can then be parsed or redeployed elsewhere.

## Python Environment

`wikiteam3` requires [Python 3.8](https://www.python.org/downloads/release/python-380/) or later (less than 4.0), but you may be able to get it run with earlier versions of Python 3. On recent versions of Linux and macOS Python 3.8 should come preinstalled, but on Windows you will need to install it from [python.org](https://www.python.org/downloads/release/python-380/).

`wikiteam3` has been tested on Linux, macOS, Windows and Android. If you are connecting to Linux or macOS via `ssh`, you can continue using the `bash` or `zsh` command prompt in the same terminal, but if you are starting in a desktop environment and don't already have a preferred Terminal environment you can try one of the following.

> **NOTE:** You may need to update and pre-install dependencies in order for `wikiteam3` to work properly. Shell commands for these dependencies appear below each item in the list. (Also note that while installing and running `wikiteam3` itself should not require administrative priviliges, installing dependencies usually will.)

* On desktop Linux you can use the default terminal application such as [Konsole](https://konsole.kde.org/) or [GNOME Terminal](https://help.gnome.org/users/gnome-terminal/stable/).

  <details>
  <summary>Linux Dependencies</summary>

  While most Linux distributions will have Python 3 preinstalled, if you are cloning `wikiteam3` rather than downloading it directly you may need to install `git`.

  On Debian, Ubuntu, and the like:

  ```bash
  sudo apt update && sudo apt upgrade && sudo install git
  ```

  (On Fedora, Arch, etc., use `dnf`, `pacman`, etc., instead.)

  </details>

* On macOS you can use the built-in application [Terminal](https://support.apple.com/guide/terminal), which is found in `Applications/Utilities`.

  <details>
  <summary>macOS Dependencies</summary>

  While macOS will have Python 3 preinstalled, if you are cloning `wikiteam3` rather than downloading it directly and you are using an older versions of macOS, you may need to install `git`.

  If `git` is not preinstalled, however, macOS will prompt you to install it the first time you run the command. Therefore, to check whether you have `git` installed or to install `git`, simply run `git` (with no arguments) in Terminal:

  ```bash
  git
  ```

  If `git` is already installed, it will print its usage instructions. If `git` is not preinstalled, the command will pop up a window asking if you want to install Apple's command line developer tools, and clicking "Install" in the popup window will install `git`.

  </details>

* On Windows 10 or Windows 11 you can use [Windows Terminal](https://aka.ms/terminal).

  <details>
  <summary>Windows Dependencies</summary>

  If you are already using the [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/about), you can follow the Linux instructions above. If you don't want to install a full WSL distribution, [Git for Windows](https://gitforwindows.org/) provides Bash emulation, so you can use it as a more lightweight option instead.

  > When installing [Python 3.8](https://www.python.org/downloads/release/python-380/) (from python.org), be sure to check "Add Python to PATH" so that installed Python scripts are accessible from any location. If for some reason installed Python scripts, e.g. `pip`, are not available from any location, you can add Python to the `PATH` environment variable using the instructions [here](https://datatofish.com/add-python-to-windows-path/).
  >
  > And while doing so should not be necessary if you follow the instructions further down and install `wikiteam3` using `pip`, if you'd prefer that Windows store installed Python scripts somewhere other than the default Python folder under `%appdata%`, you can also add your preferred alternative path such as `C:\Program Files\Python3\Scripts\` or a subfolder of `My Documents`. (You will need to restart any terminal sessions in order for this to take effect.)

  Whenever you'd like to run a Bash session, you can open a Bash terminal prompt from any folder in Windows Explorer by right-clicking and choosing the option from the context menu. (For some purposes you may wish to run Bash as an administrator.) This way you can open a Bash prompt and clone the `wikiteam3` repository in one location, and subsequently or later open another Bash prompt and run `wikiteam3` to dump a wiki wherever else you'd like without having to browse to the directory manually using Bash.

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

## Using `dumpgenerator`

The Python 3 port of the `dumpgenerator` module of `wikiteam3` is largely functional and can be installed from a downloaded or cloned copy of this repository.

There are two versions of these instructions:

* If you just want to use a version that mostly works
* If you want to follow my progress and help me test my latest commit

> If you run into a problem with the version that mostly works, you can [open an Issue](https://github.com/elsiehupp/wikiteam3/issues/new/choose). Be sure to include the following:
>
> 1. The operating system you're using
> 2. What command you ran that didn't work
> 3. What output was printed to your terminal

### If you just want to use a version that mostly works

#### 1. Downloading and installing `wikiteam3`

In whatever folder you use for cloned repositories:

```bash
git clone https://github.com/elsiehupp/wikiteam3.git
```

```bash
cd wikiteam3
```

```bash
git checkout --track origin/python3
```

```bash
pip install --force-reinstall dist/*.whl
```

#### 2. Running `dumpgenerator` for whatever purpose you need

```bash
dumpgenerator [args]
```

#### 3. Uninstalling the package and deleting the cloned repository when you're done

```shell
pip uninstall wikiteam3
```

```bash
rm -r [cloned_wikiteam3_folder]
```

If you'd like to manually build and install `wikiteam3` from a cloned or downloaded copy of this repository, run the following commands from the downloaded base directory:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

```bash
poetry install
```

```bash
poetry build
```

```bash
pip install --force-reinstall dist/*.whl
```

In either case, to uninstall `wikiteam3` run this command (from any local directory):

```bash
pip uninstall wikiteam3
```

### If you want to follow my progress and help me test my latest commit

> **Note:** this branch may not actually work at any given time!

#### 1. Install [Python Poetry](https://python-poetry.org/)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

> **Note:** if you get an SSL error, you may need to follow the instructions [here](https://github.com/python-poetry/poetry/issues/5117).

#### 2. Cloning the repository and switching to the `prepare-for-publication` branch

```bash
git clone git@github.com:elsiehupp/wikiteam3.git
```

or

```bash
git clone https://github.com/elsiehupp/wikiteam3.git
```

then:

```bash
cd wikiteam3
```

```bash
git checkout --track origin/prepare-for-publication
```

#### 3. Downloading and installing `wikiteam3`

> **Note:** Re-run the following steps each time to reinstall each time the `wikiteam3` branch is updated.

```shell
git pull
```

```bash
poetry update && poetry install && poetry build
```

```bash
pip install --force-reinstall dist/*.whl
```

#### 4. Then, from anywhere, you should be able to run

```shell
dumpgenerator [args]
```

> To run the test suite, run:
>
> ```bash
> test-dumpgenerator
> ```

#### 5. Uninstalling the package and deleting the cloned repository when you're done

```shell
pip uninstall wikiteam3
```

```bash
rm -r [cloned_wikiteam3_folder]
```

### Using `dumpgenerator` (once installed)

After installing `wikiteam3` using `pip` you should be able to use the `dumpgenerator` command from any local directory.

For basic usage, you can run `dumpgenerator` in the directory where you'd like the download to be.

For a brief summary of the `dumpgenerator` command-line options:

```bash
dumpgenerator --help
```

Several examples follow.

> **Note:** the `\` and line breaks in the examples below are for legibility in this documentation. `dumpgenerator` can also be run with the arguments in a single line and separated by a single space each.

#### Downloading a wiki with complete XML history and images

```bash
dumpgenerator \
    http://wiki.domain.org \
    --xml \
    --images
```

#### Manually specifying `api.php` and/or `index.php`

If the script can't find itself the `api.php` and/or `index.php` paths, then you can provide them:

```bash
dumpgenerator \
    --api http://wiki.domain.org/w/api.php \
    --xml \
    --images
```

```bash
dumpgenerator \
    --api http://wiki.domain.org/w/api.php \
    --index http://wiki.domain.org/w/index.php \
    --xml \
    --images
```

If you only want the XML histories, just use `--xml`. For only the images, just `--images`. For only the current version of every page, `--xml --current`.

#### Resuming an incomplete dump

```bash
dumpgenerator \
    --api http://wiki.domain.org/w/api.php \
    --xml \
    --images \
    --resume \
    --path=/path/to/incomplete-dump
```

In the above example, `--path` is only necessary if the download path is not the default.

`dumpgenerator` will also ask you if you want to resume if it finds an incomplete dump in the path where it is downloading.

## WikiTeam Team

**WikiTeam** is the [Archive Team](http://www.archiveteam.org) [[GitHub](https://github.com/ArchiveTeam)] subcommittee on wikis.

It was founded and originally developed by [Emilio J. Rodríguez-Posada](https://github.com/emijrp), a Wikipedia veteran editor and amateur archivist. Thanks to people who have helped, especially to: [Federico Leva](https://github.com/nemobis), [Alex Buie](https://github.com/ab2525), [Scott Boyd](http://www.sdboyd56.com), [Hydriz](https://github.com/Hydriz), Platonides, Ian McEwen, [Mike Dupont](https://github.com/h4ck3rm1k3), [balr0g](https://github.com/balr0g) and [PiRSquared17](https://github.com/PiRSquared17).

The Python 3 initiative is currently being led by [Elsie Hupp](https://github.com/elsiehupp), with contributions from [Victor Gambier](https://github.com/vgambier) and [Thomas Karcher](https://github.com/t-karcher).
