from typing import Iterable

import requests

from wikiteam3.dumpgenerator.config import Config


def checkXMLIntegrity(config: Config, titles: Iterable[str], session: requests.Session):
    """Check XML dump integrity, to detect broken XML chunks"""
    # TODO: Fix XML Integrity Check
    return
