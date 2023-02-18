""" Available since MediaWiki 1.27. login to a wiki using username and password (API) """

from typing import *

import requests


def fetchLoginToken(session: requests.Session, api: str) -> Optional[str]:
    """ fetch login token by API .(MediaWiki 1.27+)"""

    response = session.get(
        url=api,
        params={
            'action': "query",
            'meta': "tokens",
            'type': "login",
            'format': "json"})
    data = response.json()
    try:
        token = data['query']['tokens']['logintoken']
        if type(token) is str:
            return token
    except KeyError:
        print('fetch login token: Oops! Something went wrong -- ', data)
        return None


def clientLogin(api: str ,session: requests.Session, username: str, password: str) -> Optional[requests.Session]:
    """ login to a wiki using username and password. (MediaWiki 1.27+)"""

    login_token = fetchLoginToken(session=session, api=api)
    if not login_token:
        return None

    response = session.post(url=api, data={
        'action': "clientlogin",
        'username': username,
        'password': password,
        'loginreturnurl': 'http://127.0.0.1:5000/',
        'logintoken': login_token,
        'format': "json"
    })

    data = response.json()

    try:
        if data['clientlogin']['status'] == 'PASS':
            print('client login: Success! Welcome, ' + data['clientlogin']['username'] + '!')
    except KeyError:
        print('client login: Oops! Something went wrong -- ', data)
        return None


    return session


def botLogin(api:str ,session: requests.Session, username: str, password: str) -> Optional[requests.Session]:
    """ login to a wiki using BOT's name and password. (MediaWiki 1.27+) """

    login_token = fetchLoginToken(session=session, api=api)
    if not login_token:
        return None

    response = session.post(url=api, data={
        'action': "login",
        'lgname': username,
        'lgpassword': password,
        'lgtoken': login_token,
        'format': "json"
    })

    data = response.json()

    try:
        if data['login']['result'] == 'Success':
            print('bot login: Success! Welcome, ' + data['login']['lgusername'] + '!')
    except KeyError:
        print('bot login: Oops! Something went wrong -- ' + data)
        return None
    
    return session