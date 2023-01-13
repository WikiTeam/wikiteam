import re
import sys
from typing import *

from wikiteam3.dumpgenerator.config import Config

def avoidWikimediaProjects(config: Config=None, other: Dict=None):
    """Skip Wikimedia projects and redirect to the dumps website"""

    # notice about wikipedia dumps
    url = ""
    if config.api:
        url = url + config.api
    if config.index:
        url = url + config.index
    if re.findall(
        r"(?i)(wikipedia|wikisource|wiktionary|wikibooks|wikiversity|wikimedia|wikispecies|wikiquote|wikinews|wikidata|wikivoyage)\.org",
        url,
    ):
        print("PLEASE, DO NOT USE THIS SCRIPT TO DOWNLOAD WIKIMEDIA PROJECTS!")
        print("Download the dumps from http://dumps.wikimedia.org")
        if not other["force"]:
            print("Thanks!")
            sys.exit()
