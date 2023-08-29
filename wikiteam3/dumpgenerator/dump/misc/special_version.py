import os

from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.utils import removeIP


def saveSpecialVersion(config: Config = None, session=None):
    """Save Special:Version as .html, to preserve extensions details"""

    if os.path.exists(f"{config.path}/SpecialVersion.html"):
        print("SpecialVersion.html exists, do not overwrite")
    else:
        print("Downloading Special:Version with extensions and other related info")
        r = session.post(
            url=config.index, params={"title": "Special:Version"}, timeout=10
        )
        raw = str(r.text)
        Delay(config=config, session=session)
        raw = str(removeIP(raw=raw))
        with open(
            f"{config.path}/SpecialVersion.html", "w", encoding="utf-8"
        ) as outfile:
            outfile.write(raw)
