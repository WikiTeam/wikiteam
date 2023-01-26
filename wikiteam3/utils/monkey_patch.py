import requests

def mod_requests_text(requests: requests):
    def new_text(self):
        return self.content.lstrip(b'\xef\xbb\xbf').decode(self.encoding)
    requests.Response.text = property(new_text)