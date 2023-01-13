"""Family module for WikiApiary wiki."""

__version__ = "$Id: 8c9856dd7c0af8d400d0d95b00bf406002729008 $"

from pywikibot import family


# The MediaWiki family
# user-config.py: usernames['wikiapiary']['wikiapiary'] = 'User name'
class Family(family.WikimediaFamily):

    """Family module for WikiApiary wiki."""

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.name = "wikiapiary"

        self.langs = {
            "wikiapiary": "wikiapiary.com",
        }

        # Wikimedia wikis all use "bodyContent" as the id of the <div>
        # element that contains the actual page content; change this for
        # wikis that use something else (e.g., mozilla family)
        self.content_id = "bodyContent"

    def scriptpath(self, code):
        """The prefix used to locate scripts on this wiki.

        This is the value displayed when you enter {{SCRIPTPATH}} on a
        wiki page (often displayed at [[Help:Variables]] if the wiki has
        copied the master help page correctly).

        The default value is the one used on Wikimedia Foundation wikis,
        but needs to be overridden in the family file for any wiki that
        uses a different value.

        """
        return "/w"

    # Which version of MediaWiki is used? REQUIRED
    def version(self, code):
        # Replace with the actual version being run on your wiki
        return "1.25.3"

    def code2encoding(self, code):
        """Return the encoding for a specific language wiki"""
        # Most wikis nowadays use UTF-8, but change this if yours uses
        # a different encoding
        return "utf-8"

    def path(self, code):
        return "/w/index.php"

    def apipath(self, code):
        return "/w/api.php"

    def protocol(self, code):
        return "HTTPS"
