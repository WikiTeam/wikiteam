from .domain import domain2prefix
from .login import botLogin, clientLogin, indexLogin, uniLogin
from .monkey_patch import mod_requests_text
from .uprint import uprint
from .user_agent import getUserAgent
from .util import cleanHTML, cleanXML, removeIP, sha1File, undoHTMLEntities
from .wiki_avoid import avoidWikimediaProjects

__all__ = [domain2prefix, botLogin, clientLogin, indexLogin, uniLogin, mod_requests_text, uprint, getUserAgent, cleanHTML, cleanXML, removeIP, sha1File, undoHTMLEntities, avoidWikimediaProjects]  # type: ignore
