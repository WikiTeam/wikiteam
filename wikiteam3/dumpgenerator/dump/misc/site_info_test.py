import json
from collections.abc import Generator
from typing import Any, Optional

import requests

from wikiteam3.dumpgenerator.config import Config
from wikiteam3.dumpgenerator.test.test_config import get_config

from .site_info import saveSiteInfo


def test_mediawiki_version_match():
    config: Optional[Generator[Config, Any, Config | None]] = get_config("1.45.1")
    if config and type(config) is Config:
        sess = requests.Session()
        saveSiteInfo(config, sess)
        with open(f"{config.path}/siteinfo.json") as f:
            siteInfoJson = json.load(f)
        assert siteInfoJson["query"]["general"]["generator"] == "MediaWiki 1.45.1"
