from api_check import checkAPI
import mwclient
import requests
import time
from urllib.parse import urlparse


def checkRetryAPI(api=None, retries=5, apiclient=False, session=None):
    """Call checkAPI and mwclient if necessary"""
    retry = 0
    retrydelay = 20
    check = None
    while retry < retries:
        try:
            check = checkAPI(api, session=session)
            break
        except requests.exceptions.ConnectionError as e:
            print("Connection error: %s" % (str(e)))
            retry += 1
            print("Start retry attempt %d in %d seconds." % (retry + 1, retrydelay))
            time.sleep(retrydelay)

    if check and apiclient:
        apiurl = urlparse(api)
        try:
            site = mwclient.Site(
                apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=apiurl.scheme
            )
        except KeyError:
            # Probably KeyError: 'query'
            if apiurl.scheme == "https":
                newscheme = "http"
                api = api.replace("https://", "http://")
            else:
                newscheme = "https"
                api = api.replace("http://", "https://")
            print(
                "WARNING: The provided API URL did not work with mwclient. Switched protocol to: {}".format(
                    newscheme
                )
            )

            try:
                site = mwclient.Site(
                    apiurl.netloc, apiurl.path.replace("api.php", ""), scheme=newscheme
                )
            except KeyError:
                check = False

    return check, api
