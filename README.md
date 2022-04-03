# `wikiteam3`

***We archive wikis, from Wikipedia to the tiniest wikis***

`wikiteam3` is an ongoing project to port the legacy [`wikiteam`](https://github.com/WikiTeam/wikiteam) toolset to Python 3 and PyPI to make it more accessible for today's archivers.

Most of the focus has been on the core `dumpgenerator` tool, but Python 3 versions of the other `wikiteam` tools may be added over time.

## `wikiteam3` Toolset

`wikiteam3` is a set of tools for archiving wikis. The tools work on MediaWiki wikis, but the team hopes to expand to other wiki engines. As of 2020, WikiTeam has preserved more than [250,000 wikis](https://github.com/WikiTeam/wikiteam/wiki/Available-Backups), several wikifarms, regular Wikipedia dumps and [34 TB of Wikimedia Commons images](https://archive.org/details/wikimediacommons).

The main general-purpose module of `wikiteam3` is `dumpgenerator`, which can download XML dumps of MediaWiki sites that can then be parsed or redeployed elsewhere.

## Using `dumpgenerator`

The Python 3 port of the `dumpgenerator` module of `wikiteam3` is largely functional and can be installed from a downloaded or cloned copy of this repository.

> `wikiteam3` requires [Python 3.8](https://www.python.org/downloads/release/python-380/) or later (less than 4.0), but you may be able to get it run with earlier versions of Python 3.

There are two versions of these instructions:

* If you just want to use a version that mostly works
* If you want to follow my progress and help me test my latest commit

> If you run into a problem with the version that mostly works, you can [open an Issue](https://github.com/elsiehupp/wikiteam3/issues/new/choose). Be sure to include the following:
>
> 1. The operating system you're using
> 2. What command you ran that didn't work
> 3. What output was printed to your terminal

### If you just want to use a version that mostly works

#### 1. Download and install

In whatever folder you use for cloned repositories:

```bash
$ git clone https://github.com/elsiehupp/wikiteam3.git
$ cd wikiteam3
$ git checkout --track origin/python3
$ pip install --force-reinstall dist/*.whl
```

#### 2. Run `dumpgenerator` for whatever purpose you need

```bash
$ dumpgenerator [args]
```

#### 3. To uninstall the package and delete the cloned repository when you're done

```shell
$ pip uninstall wikiteam3
$ rm -r [cloned_wikiteam3_folder]
```

If you'd like to manually install `wikiteam3` from a cloned or downloaded copy of this repository, run the following commands from the downloaded base directory:

```bash
$ curl -sSL https://install.python-poetry.org | python3 -
$ poetry install
$ poetry build
$ pip install --force-reinstall dist/*.whl
```

In either case, to uninstall `wikiteam3` run this command (from any local directory):

```bash
pip uninstall wikiteam3
```

### If you want to follow my progress and help me test my latest commit

> **Note:** this branch may not actually work at any given time!

#### 1. Install [Python Poetry](https://python-poetry.org/)

```bash
$ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

> **Note:** if you get an SSL error, you may need to follow the instructions [here](https://github.com/python-poetry/poetry/issues/5117).

#### 2. Clone the repository and switch to the `prepare-for-publication` branch

```bash
$ git clone git@github.com:elsiehupp/wikiteam3.git
```

or

```bash
$ git clone https://github.com/elsiehupp/wikiteam3.git
```

then:

```bash
$ cd wikiteam3
$ git checkout --track origin/prepare-for-publication
```

#### 3. Build and install

> **Note:** Re-run the following steps each time to reinstall each time the `wikiteam3` branch is updated.

```shell
$ git pull
$ poetry update && poetry install && poetry build
$ pip install --force-reinstall dist/*.whl
```

#### 4. Then, from anywhere, you should be able to run

```shell
$ dumpgenerator [args]
```

> To run the test suite, run:
>
> ```bash
> $ test-dumpgenerator
> ```

#### 5. To uninstall the package and delete the cloned repository when you're done

```shell
$ pip uninstall wikiteam3
$ rm -r [cloned_wikiteam3_folder]
```

### Using `dumpgenerator`

After installing `wikiteam3` using `pip` you should be able to use the `dumpgenerator` command from any local directory.

For basic usage, you can run `dumpgenerator` in the directory where you'd like the download to be.

For a brief summary of the `dumpgenerator` command-line options:

```bash
$ dumpgenerator --help
```

Several examples follow:

#### To download a wiki with omplete XML histories and images:

```bash
$ dumpgenerator http://wiki.domain.org --xml --images
```

#### If the script can't find itself the `api.php` and/or `index.php` paths, then you can provide them:

```bash
$ dumpgenerator --api http://wiki.domain.org/w/api.php --xml --images
```


```bash
$ dumpgenerator --api http://wiki.domain.org/w/api.php --index http://wiki.domain.org/w/index.php --xml --images
```

If you only want the XML histories, just use `--xml`. For only the images, just `--images`. For only the current version of every page, `--xml --current`.

#### You can resume an aborted download:

```bash
$ dumpgenerator --api http://wiki.domain.org/w/api.php --xml --images --resume --path=/path/to/incomplete-dump
```

`dumpgenerator` will also ask you if you want to resume if it detects an aborted download as it is running.

## WikiTeam Team

**WikiTeam** is the [Archive Team](http://www.archiveteam.org) [[GitHub](https://github.com/ArchiveTeam)] subcommittee on wikis.

It was founded and originally developed by [Emilio J. Rodríguez-Posada](https://github.com/emijrp), a Wikipedia veteran editor and amateur archivist. Thanks to people who have helped, especially to: [Federico Leva](https://github.com/nemobis), [Alex Buie](https://github.com/ab2525), [Scott Boyd](http://www.sdboyd56.com), [Hydriz](https://github.com/Hydriz), Platonides, Ian McEwen, [Mike Dupont](https://github.com/h4ck3rm1k3), [balr0g](https://github.com/balr0g) and [PiRSquared17](https://github.com/PiRSquared17).

The Python 3 initiative is currently being led by [Elsie Hupp](https://github.com/elsiehupp), with contributions from [Victor Gambier](https://github.com/vgambier) and [Thomas Karcher](https://github.com/t-karcher).
