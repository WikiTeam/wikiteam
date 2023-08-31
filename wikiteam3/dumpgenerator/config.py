"""
config = {
        "curonly": args.curonly,
        "date": datetime.datetime.now().strftime("%Y%m%d"),
        "api": api,
        "failfast": args.failfast,
        "http_method": "POST",
        "index": index,
        "images": args.images,
        "logs": False,
        "xml": args.xml,
        "xmlrevisions": args.xmlrevisions,
        "namespaces": namespaces,
        "exnamespaces": exnamespaces,
        "path": args.path and os.path.normpath(args.path) or "",
        "cookies": args.cookies or "",
        "delay": args.delay,
        "retries": int(args.retries),
    }
"""

import contextlib
import dataclasses
import json
import sys
from dataclasses import field
from typing import List


def _dataclass_from_dict(klass_or_obj, d):
    ret = klass_or_obj() if isinstance(klass_or_obj, type) else klass_or_obj
    for k, v in d.items():
        if hasattr(ret, k):
            setattr(ret, k, v)
    return ret


@dataclasses.dataclass
class Config:
    def asdict(self):
        return dataclasses.asdict(self)

    # General params
    delay: float = 0.0
    retries: int = 0
    path: str = ""
    logs: bool = False
    date: str = ""

    # URL params
    index: str = ""
    api: str = ""

    # Download params
    xml: bool = False
    curonly: bool = False
    xmlapiexport: bool = False
    xmlrevisions: bool = False
    xmlrevisions_page: bool = False
    images: bool = False
    namespaces: List[int] = field(default_factory=lambda: [])
    exnamespaces: List[int] = field(default_factory=lambda: [])

    api_chunksize: int = 0  # arvlimit, ailimit, etc
    export: str = ""  # Special:Export page name
    http_method: str = ""

    # Meta info params
    failfast: bool = False

    templates: bool = False


def newConfig(configDict) -> Config:
    return _dataclass_from_dict(Config, configDict)


def loadConfig(config: Config, configfilename=""):
    """Load config file"""

    configDict = dataclasses.asdict(config)

    if config.path:
        with contextlib.suppress(Exception):
            with open(f"{config.path}/{configfilename}", encoding="utf-8") as infile:
                configDict.update(json.load(infile))
            return newConfig(configDict)
    print("There is no config file. we can't resume. Start a new dump.")
    sys.exit()


def saveConfig(config: Config, configfilename=""):
    """Save config file"""

    with open(f"{config.path}/{configfilename}", "w", encoding="utf-8") as outfile:
        json.dump(dataclasses.asdict(config), outfile)
