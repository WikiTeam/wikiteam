import json

import pytest
import requests

from wikiteam3.dumpgenerator.test.test_config import get_config

from .site_info import saveSiteInfo


def test_mediawiki_version_match():
    with get_config("1.39.5") as config:
        sess = requests.Session()
        saveSiteInfo(config, sess)
        with open(f"{config.path}/siteinfo.json") as f:
            siteInfoJson = json.load(f)
        assert siteInfoJson["query"]["general"]["generator"] == "MediaWiki 1.39.5"
