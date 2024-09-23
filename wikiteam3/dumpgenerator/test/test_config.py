import copy
import tempfile
from contextlib import contextmanager

from wikiteam3.dumpgenerator.cli import getParameters
from wikiteam3.dumpgenerator.config import newConfig

CONFIG_CACHE = {}


@contextmanager
def _new_config_from_parameter(params):
    _params = tuple(params)
    if _params in CONFIG_CACHE:
        return CONFIG_CACHE[_params]
    config, _ = getParameters(["--path=.", "--xml"] + list(params))
    CONFIG_CACHE[_params] = config
    _config = newConfig(copy.deepcopy(config.asdict()))
    try:
        with tempfile.TemporaryDirectory(prefix="wikiteam3test_") as tmpdir:
            _config.path = tmpdir
            yield _config
    finally:
        pass


def get_config(mediawiki_ver, api=True):
    assert api == True
    if mediawiki_ver == "1.39.7":
        return _new_config_from_parameter(
            [
                "--api",
                "https://testw.fandom.com/api.php",
            ]
        )
