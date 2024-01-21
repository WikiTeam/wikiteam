import requests

"""Return a cool user-agent to hide Python user-agent"""


def getUserAgent():
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    return useragent


def setupUserAgent(session: requests.Session):
    session._orirequest = session.request

    def newrequest(*args, **kwargs):
        session.headers.update({"User-Agent": getUserAgent()})
        return session._orirequest(*args, **kwargs)

    session.request = newrequest
