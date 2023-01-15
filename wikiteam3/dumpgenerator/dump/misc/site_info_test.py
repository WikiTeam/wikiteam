import json

import pytest
import requests

from wikiteam3.dumpgenerator.test.test_config import get_config

from .site_info import saveSiteInfo

def test_mediawiki_1_16():
    with get_config('1.16.5') as config:
        sess = requests.Session()
        saveSiteInfo(config, sess)
        with open(config.path + '/siteinfo.json', 'r') as f:
            siteInfoJson = json.load(f)
        assert siteInfoJson['query']['general']['generator'] == "MediaWiki 1.16.5"
