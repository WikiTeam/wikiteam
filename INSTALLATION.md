# Installation

## Python Environment

`MediaWiki Dump Generator` requires [Python 3.8](https://www.python.org/downloads/release/python-380/) or later (less than 4.0), but you may be able to get it run with earlier versions of Python 3. On recent versions of Linux and macOS Python 3.8 should come preinstalled, but on Windows you will need to install it from [python.org](https://www.python.org/downloads/release/python-380/).

`MediaWiki Dump Generator` has been tested on Linux, macOS, Windows and Android. If you are connecting to Linux or macOS via `ssh`, you can continue using the `bash` or `zsh` command prompt in the same terminal, but if you are starting in a desktop environment and don't already have a preferred Terminal environment you can try one of the following.

> **NOTE:** You may need to update and pre-install dependencies in order for `MediaWiki Dump Generator` to work properly. Shell commands for these dependencies appear below each item in the list. (Also note that while installing and running `MediaWiki Dump Generator` itself should not require administrative priviliges, installing dependencies usually will.)

* On desktop Linux you can use the default terminal application such as [Konsole](https://konsole.kde.org/) or [GNOME Terminal](https://help.gnome.org/users/gnome-terminal/stable/).

  <details>
  <summary>Linux Dependencies</summary>

  While most Linux distributions will have Python 3 preinstalled, if you are cloning `MediaWiki Dump Generator` rather than downloading it directly you may need to install `git`.

  On Debian, Ubuntu, and the like:

  ```bash
  sudo apt update && sudo apt upgrade && sudo install git
  ```

  (On Fedora, Arch, etc., use `dnf`, `pacman`, etc., instead.)

  </details>

* On macOS you can use the built-in application [Terminal](https://support.apple.com/guide/terminal), which is found in `Applications/Utilities`.

  <details>
  <summary>macOS Dependencies</summary>

  While macOS will have Python 3 preinstalled, if you are cloning `MediaWiki Dump Generator` rather than downloading it directly and you are using an older versions of macOS, you may need to install `git`.

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
  > And while doing so should not be necessary if you follow the instructions further down and install `MediaWiki Dump Generator` using `pip`, if you'd prefer that Windows store installed Python scripts somewhere other than the default Python folder under `%appdata%`, you can also add your preferred alternative path such as `C:\Program Files\Python3\Scripts\` or a subfolder of `My Documents`. (You will need to restart any terminal sessions in order for this to take effect.)

  Whenever you'd like to run a Bash session, you can open a Bash terminal prompt from any folder in Windows Explorer by right-clicking and choosing the option from the context menu. (For some purposes you may wish to run Bash as an administrator.) This way you can open a Bash prompt and clone the `MediaWiki Dump Generator` repository in one location, and subsequently or later open another Bash prompt and run `MediaWiki Dump Generator` to dump a wiki wherever else you'd like without having to browse to the directory manually using Bash.

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

> If you run into a problem with the version that mostly works, you can [open an Issue](https://github.com/mediawiki-client-tools/mediawiki-dump-generator/issues/new/choose). Be sure to include the following:
>
> 1. The operating system you're using
> 2. What command you ran that didn't work
> 3. What output was printed to your terminal

### 1. Downloading and installing `MediaWiki Dump Generator`

In whatever folder you use for cloned repositories:

```bash
git clone https://github.com/mediawiki-client-tools/mediawiki-dump-generator
```

```bash
cd mediawiki-dump-generator
```

```bash
poetry update && poetry install && poetry build
```

```bash
pip install --force-reinstall dist/*.whl
```

<details>
<summary>For Windows Command Prompt, enter this pip command instead, (in a batch file use %%x).</summary>

```bash
for %x in (dist\*.whl) do pip install --force-reinstall %x
```

</details>
<details>
<summary>For Windows Powershell, enter this pip command instead.</summary>

```bash
pip install --force-reinstall (Get-ChildItem .\dist\*.whl).FullName
```

</details>

### 2. Running `dumpgenerator` for whatever purpose you need

After installing `MediaWiki Dump Generator` using `pip` you should be able to use the `dumpgenerator` command from any local directory.

```bash
dumpgenerator [args]
```

### 3. Uninstalling the package and deleting the cloned repository when you're done

```shell
pip uninstall wikiteam3
```

```bash
rm -fr [cloned mediawiki dump generator folder]
```

### 4. Updating MediaWiki Dump Generator

> **Note:** Re-run the following steps each time to reinstall each time the MediaWiki Dump Generator branch is updated.

```bash
git pull
```

```bash
poetry update && poetry install && poetry build
```

```bash
pip install --force-reinstall dist/*.whl
```

<details>
<summary>For Windows Command Prompt, enter this pip command instead, (in a batch file use %%x).</summary>

```bash
for %x in (dist\*.whl) do pip install --force-reinstall %x
```

</details>
<details>
<summary>For Windows Powershell, enter this pip command instead.</summary>

```bash
pip install --force-reinstall (Get-ChildItem .\dist\*.whl).FullName
```

</details>

### 5. Manually build and install `MediaWiki Dump Generator`

If you'd like to manually build and install `MediaWiki Dump Generator` from a cloned or downloaded copy of this repository, run the following commands from the downloaded base directory:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

```bash
poetry update && poetry install && poetry build
```

```bash
pip install --force-reinstall dist/*.whl
```

<details>
<summary>For Windows Command Prompt, enter this pip command instead, (in a batch file use %%x).</summary>

```bash
for %x in (dist\*.whl) do pip install --force-reinstall %x
```

</details>
<details>
<summary>For Windows Powershell, enter this pip command instead.</summary>

```bash
pip install --force-reinstall (Get-ChildItem .\dist\*.whl).FullName
```

</details>

### 6. To run the test suite

To run the test suite, run:

```bash
test-dumpgenerator
```

### 7. Switching branches

```bash
git checkout --track origin/python3
```
