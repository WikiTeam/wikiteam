from typing import Iterable

from wikiteam3.dumpgenerator.config import Config


def checkXMLIntegrity(
    config: Config, titles: (Iterable[str] | None) = None, session=None
):
    """Check XML dump integrity, to detect broken XML chunks"""
    # TODO: Fix XML Integrity Check
    return
