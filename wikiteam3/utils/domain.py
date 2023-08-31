import re

from wikiteam3.dumpgenerator.config import Config


def domain2prefix(config: Config):
    """Convert domain name to a valid prefix filename."""

    # At this point, both api and index are supposed to be defined
    domain = ""
    if config.api:
        domain = config.api
    elif config.index:
        domain = config.index

    domain = domain.lower()
    domain = re.sub(r"(https?://|www\.|/index\.php.*|/api\.php.*)", "", domain)
    domain = domain.rstrip("/")
    domain = re.sub(r"/", "_", domain)
    domain = re.sub(r"\.", "", domain)
    domain = re.sub(r"[^A-Za-z0-9]", "_", domain)

    return domain
