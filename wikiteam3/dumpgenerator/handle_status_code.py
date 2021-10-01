import sys


def handleStatusCode(response):
    statuscode = response.status_code
    if statuscode >= 200 and statuscode < 300:
        return

    print("HTTP Error %d." % statuscode)
    if statuscode >= 300 and statuscode < 400:
        print("Redirect should happen automatically: please report this as a bug.")
        print(response.url)

    elif statuscode == 400:
        print("Bad Request: The wiki may be malfunctioning.")
        print("Please try again later.")
        print(response.url)
        sys.exit(1)

    elif statuscode == 401 or statuscode == 403:
        print("Authentication required.")
        print("Please use --user and --pass.")
        print(response.url)

    elif statuscode == 404:
        print("Not found. Is Special:Export enabled for this wiki?")
        print(response.url)
        sys.exit(1)

    elif statuscode == 429 or (statuscode >= 500 and statuscode < 600):
        print("Server error, max retries exceeded.")
        print("Please resume the dump later.")
        print(response.url)
        sys.exit(1)
