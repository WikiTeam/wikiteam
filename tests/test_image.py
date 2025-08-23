import pytest

from wikiteam3.dumpgenerator.dump.image.image import Image

# https://github.com/saveweb/wikiteam3/issues/51

def test_get_image_names_API_spaces2underscore(monkeypatch):
    class DummyConfig:
        api = 'https://example.com/api.php'
        api_chunksize = 10
        index = 'https://example.com/index.php'
    class DummySession:
        def get(self, url, params=None, timeout=None):
            class DummyResponse:
                def __init__(self):
                    self.status_code = 200
                    self.headers = {}
                def json(self):
                    return {
                        'query': {
                            'allimages': [
                                {'name': 'Video:Fatal 5 combo video', 'url': 'https://example.com/1', 'user': 'User A'},
                                {'name': 'Test_image_with_underscore', 'url': 'https://example.com/2', 'user': 'User B'},
                            ]
                        }
                    }
            return DummyResponse()
    # Patch handle_StatusCode/get_JSON/Delay to be no-ops
    monkeypatch.setattr('wikiteam3.dumpgenerator.dump.image.image.handle_StatusCode', lambda r: None)
    monkeypatch.setattr('wikiteam3.dumpgenerator.dump.image.image.get_JSON', lambda r: r.json())
    monkeypatch.setattr('wikiteam3.dumpgenerator.dump.image.image.Delay', lambda config: None)
    result = Image.get_image_names_API(DummyConfig(), DummySession())
    # The result is a array, filename is at index 0
    filenames = [row[0] for row in result]
    assert all(' ' not in fn for fn in filenames)
    assert 'Video:Fatal_5_combo_video' in filenames