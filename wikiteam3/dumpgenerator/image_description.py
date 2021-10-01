from page_xml import getXMLPage


def getXMLFileDesc(config={}, title="", session=None):
    """Get XML for image description page"""
    config["curonly"] = 1  # tricky to get only the most recent desc
    return "".join(
        [
            x
            for x in getXMLPage(
                config=config, title=title, verbose=False, session=session
            )
        ]
    )
