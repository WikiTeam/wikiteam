""" Provide login functions """

import requests
import time

from wikiteam3.utils.login.api import botLogin, clientLogin, fetchLoginToken
from wikiteam3.utils.login.index import indexLogin


def uniLogin(api: str = '', index: str = '' ,session: requests.Session = requests.Session(), username: str = '', password: str = ''):
    """ Try to login to a wiki using various methods.\n
    Return `session` if success, else return `None`.\n
    Try: `cilent login (api) => bot login (api) => index login (index)` """

    if (not api and not index) or (not username or not password):
        print('uniLogin: api or index or username or password is empty')
        return None

    if api:
        _session = clientLogin(api=api, session=session, username=username, password=password)
        if _session:
            return _session
        time.sleep(5)

        _session = botLogin(api=api, session=session, username=username, password=password)
        if _session:
            return _session
        time.sleep(5)

    if index:
        _session = indexLogin(index=index, session=session, username=username, password=password)
        if _session:
            return _session

    return None
