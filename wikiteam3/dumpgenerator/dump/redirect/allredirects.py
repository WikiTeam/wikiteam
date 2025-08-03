
import requests

from wikiteam3.dumpgenerator.api.namespaces import getNamespacesAPI
from wikiteam3.dumpgenerator.cli.delay import Delay
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.utils.util import ALL_NAMESPACE_FLAG

def get_redirects_by_allredirects(config: Config, session: requests.Session):
    continueKey = 'arcontinue'
    assert config.api, "API URL is required"

    namespaces, namespacenames = getNamespacesAPI(config=config, session=session)
    ar_params = {
        "action": "query",
        "format": "json",
        "list": "allredirects",
        "arlimit": config.api_chunksize,
        "arprop": "ids|title|fragment|interwiki",
        "ardir": "ascending",
        "continue": "" # DEV.md#Continuation
    }
    for ns in namespaces:
        if continueKey in ar_params:
            del ar_params[continueKey] # reset continue parameter
        if ALL_NAMESPACE_FLAG not in config.namespaces: # user has specified namespaces
            if ns not in config.namespaces:
                print(f"Skipping namespace {ns}")
                continue

        print(f"Processing namespace {ns} ({namespacenames[ns] if ns in namespacenames else 'unknown'})")
        ar_params["arnamespace"] = str(ns)
        while True:
            Delay(config=config)
            r = session.get(url=config.api, params=ar_params)
            allredirects_response = r.json()

            redirects = allredirects_response["query"]["allredirects"]
            for redirect in redirects:
                yield redirect

            if "continue" in allredirects_response:
                # update continue parameter
                ar_params[continueKey] = allredirects_response["continue"][continueKey]
                print(f"  {continueKey}={ar_params[continueKey]}")
            else:
                # End of continuation. We are done with this namespace.
                break

# TODO: unit test
if __name__ == "__main__":
    config = Config(
        api="https://en.wikipedia.org/w/api.php",
        namespaces=[ALL_NAMESPACE_FLAG], # type: ignore
        redirects=True,
        api_chunksize=500
    )
    ss = requests.Session()
    for redirect in get_redirects_by_allredirects(config, ss):
        print(redirect)