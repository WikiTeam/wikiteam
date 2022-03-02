import json
import os

from .delay import delay
from .get_json import getJSON


def saveSiteInfo(config={}, session=None):
    """Save a file with site info"""

    if config["api"]:
        if os.path.exists("%s/siteinfo.json" % (config["path"])):
            print("siteinfo.json exists, do not overwrite")
        else:
            print("Downloading site info as siteinfo.json")

            # MediaWiki 1.13+
            r = session.get(
                url=config["api"],
                params={
                    "action": "query",
                    "meta": "siteinfo",
                    "siprop": "general|namespaces|statistics|dbrepllag|interwikimap|namespacealiases|specialpagealiases|usergroups|extensions|skins|magicwords|fileextensions|rightsinfo",
                    "sinumberingroup": 1,
                    "format": "json",
                },
                timeout=10,
            )
            # MediaWiki 1.11-1.12
            if not "query" in getJSON(r):
                r = session.get(
                    url=config["api"],
                    params={
                        "action": "query",
                        "meta": "siteinfo",
                        "siprop": "general|namespaces|statistics|dbrepllag|interwikimap",
                        "format": "json",
                    },
                    timeout=10,
                )
            # MediaWiki 1.8-1.10
            if not "query" in getJSON(r):
                r = session.get(
                    url=config["api"],
                    params={
                        "action": "query",
                        "meta": "siteinfo",
                        "siprop": "general|namespaces",
                        "format": "json",
                    },
                    timeout=10,
                )
            result = getJSON(r)
            delay(config=config, session=session)
            with open("%s/siteinfo.json" % (config["path"]), "w", encoding="utf-8") as outfile:
                outfile.write(json.dumps(result, indent=4, sort_keys=True))
