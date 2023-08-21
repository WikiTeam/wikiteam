from wikiteam3.dumpgenerator.config import Config

from .page_xml_api import getXMLPageWithApi
from .page_xml_export import getXMLPageWithExport


def getXMLPage(config: Config = None, title="", verbose=True, session=None):
    if config.xmlapiexport:
        return getXMLPageWithApi(
            config=config, title=title, verbose=verbose, session=session
        )
    else:
        return getXMLPageWithExport(
            config=config, title=title, verbose=verbose, session=session
        )
