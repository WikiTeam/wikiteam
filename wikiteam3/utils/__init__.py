from .domain import domain2prefix
from .login import botLogin, clientLogin, fetchLoginToken, indexLogin, uniLogin
from .monkey_patch import mod_requests_text
from .uprint import uprint
from .user_agent import getUserAgent
from .util import cleanHTML, cleanXML, removeIP, sha1File, undoHTMLEntities
from .wiki_avoid import avoidWikimediaProjects
