""" Always available login methods.(mw 1.16-1.39)
    Even oler versions of MW may work, but not tested. """

from typing import Optional

import lxml.html
import requests


def indexLogin(
    index: str, session: requests.Session, username: str, password: str
) -> Optional[requests.Session]:
    """Try to login to a wiki using username and password through `Special:UserLogin`.
    (tested on MW 1.16...1.39)"""
    wpEditToken = None
    wpLoginToken = None

    params = {
        "title": "Special:UserLogin",
    }
    r = session.get(index, allow_redirects=True, params=params)

    # Sample r.text:
    # MW 1.16: <input type="hidden" name="wpLoginToken" value="adf5ed40243e9e5db368808b27dc289c" />
    # MW 1.39: <input name="wpLoginToken" type="hidden" value="ad43f6cc89ef50ac3dbd6d03b56aedca63ec4c90+\"/>
    html = lxml.html.fromstring(r.text)
    if "wpLoginToken" in r.text:
        wpLoginToken = html.xpath('//input[@name="wpLoginToken"]/@value')[0]

    # Sample r.text:
    # MW 1.16: None
    # MW 1.39: <input id="wpEditToken" type="hidden" value="+\" name="wpEditToken"/>
    if "wpEditToken" in r.text:
        wpEditToken = html.xpath('//input[@name="wpEditToken"]/@value')[0]
        print("index login: wpEditToken found.")

    data = {
        "wpName": username,  # required
        "wpPassword": password,  # required
        "wpLoginattempt": "Log in",  # required
        "wpLoginToken": wpLoginToken,  # required
        "wpRemember": "1",  # 0: not remember, 1: remember
        "wpEditToken": wpEditToken,  # introduced before MW 1.27, not sure whether it's required.
        "authAction": "login",  # introduced before MW 1.39.
        "title": "Special:UserLogin",  # introduced before MW 1.39.
        "force": "",  # introduced before MW 1.39, empty string is OK.
    }
    r = session.post(index, allow_redirects=False, params=params, data=data)  # type: ignore
    if r.status_code == 302:
        print("index login: Success! Welcome, ", username, "!")
        return session
    else:
        print(
            "index login: Oops! Something went wrong -- ",
            r.status_code,
            "wpLoginToken: ",
            wpLoginToken,
            "wpEditToken: ",
            wpEditToken,
        )
        return None
