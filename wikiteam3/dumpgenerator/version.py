__VERSION__ = "unknown"

try:
    import importlib.metadata
    __VERSION__ = importlib.metadata.version("wikiteam3")
except Exception:
    pass


def getVersion():
    return __VERSION__
