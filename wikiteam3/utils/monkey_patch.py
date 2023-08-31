import requests

from wikiteam3.dumpgenerator.cli.delay import Delay


def mod_requests_text(requests: requests):  # type: ignore
    """Monkey patch `requests.Response.text` to remove BOM"""

    def new_text(self):
        return self.content.lstrip(b"\xef\xbb\xbf").decode(self.encoding)

    requests.Response.text = property(new_text)  # type: ignore


class DelaySession:
    """Monkey patch `requests.Session.send` to add delay"""

    def __init__(self, session, msg=None, delay=None, config=None):
        self.session = session
        self.msg = msg
        self.delay = delay
        self.old_send = None
        self.config = config

    def hijack(self):
        """Don't forget to call `release()`"""

        def new_send(request, **kwargs):
            Delay(msg=self.msg, delay=self.delay, config=self.config)  # type: ignore
            return self.old_send(request, **kwargs)  # type: ignore

        self.old_send = self.session.send
        self.session.send = new_send

    def release(self):
        """Undo monkey patch"""
        self.session.send = self.old_send
        del self
