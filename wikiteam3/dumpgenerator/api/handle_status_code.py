import sys

import requests


def handle_StatusCode(response: requests.Response):
    status_code = response.status_code
    if status_code >= 200 and status_code < 300:
        return

    print("HTTP Error %d." % status_code)
    if status_code >= 300 and status_code < 400:
        print("Redirect should happen automatically: please report this as a bug.")
        print(response.url)

    elif status_code == 400:
        print("Bad Request: The wiki may be malfunctioning.")
        print("Please try again later.")
        print(response.url)
        sys.exit(1)

    elif status_code == 401 or status_code == 403:
        print("Authentication required.")
        print("Please use --user and --pass.")
        print(response.url)
        sys.exit(1)

    elif status_code == 404:
        print("Not found. Is Special:Export enabled for this wiki?")
        print(response.url)
        sys.exit(1)

    elif status_code == 429 or (status_code >= 500 and status_code < 600):
        print("Server error, max retries exceeded.")
        print("Please resume the dump later.")
        print(response.url)
        sys.exit(1)
