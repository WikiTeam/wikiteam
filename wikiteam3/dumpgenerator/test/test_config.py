import copy
import tempfile
from collections.abc import Generator

# from contextlib import contextmanager
from typing import Any, Optional

from wikiteam3.dumpgenerator.cli import getParameters
from wikiteam3.dumpgenerator.config import Config, newConfig

CONFIG_CACHE: dict[tuple, Config] = {}


# @contextmanager
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


def get_config(
    mediawiki_ver, api=True
) -> Optional[Generator[Config, Any, Config | None]]:
    assert api
    if mediawiki_ver == "1.45.1":
        return _new_config_from_parameter(
            [
                "--api",
                "https://publictestwiki.com/api.php",
            ]
        )
    else:
        return None
