import datetime

from wikiteam3.dumpgenerator.version import getVersion


def welcome():
    message = ""
    """Opening message"""
    message += "#" * 73
    message += "\n"
    welcome_string = "# Welcome to DumpGenerator %s by WikiTeam (GPL v3)" % (
        getVersion()
    )
    welcome_string += " " * (73 - len(welcome_string) - 1) + "#"
    message += welcome_string
    message += "\n"
    message += (
        "# More info at: https://github.com/elsiehupp/wikiteam3                  #"
    )
    message += "\n"
    message += "#" * 73
    message += "\n"
    message += ""
    message += "\n"
    message += "#" * 73
    message += "\n"
    message += (
        "# Copyright (C) 2011-%d WikiTeam developers                           #\n"
        % (datetime.datetime.now().year)
    )
    message += """#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #"""
    message += "\n"
    message += "#" * 73
    message += "\n"
    message += ""

    return message


def bye():
    """Closing message"""
    print("")
    print("---> Congratulations! Your dump is complete <---")
    print("")
    print("If you encountered a bug, you can report it on GitHub Issues:")
    print("  https://github.com/mediawiki-client-tools/mediawiki-scraper/issues")
    print("")
    print("If you need any other help, you can reach out on GitHub Discussions:")
    print("  https://github.com/orgs/mediawiki-client-tools/discussions")
    print("")
    print("If this is a public wiki, please, consider publishing this dump.")
    print("Do it yourself as explained in:")
    print("  https://github.com/WikiTeam/wikiteam/wiki/Tutorial#Publishing_the_dump")
    print("")
    print("Good luck! Bye!")
    print("")
