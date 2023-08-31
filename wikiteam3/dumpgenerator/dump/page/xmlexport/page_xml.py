import requests

from wikiteam3.dumpgenerator.config import Config

from .page_xml_api import getXMLPageWithApi
from .page_xml_export import getXMLPageWithExport


# title="", verbose=True
def getXMLPage(config: Config, title: str, verbose: bool, session: requests.Session):
    if config.xmlapiexport:
        return getXMLPageWithApi(
            config=config, title=title, verbose=verbose, session=session
        )
    else:
        return getXMLPageWithExport(
            config=config, title=title, verbose=verbose, session=session
        )
