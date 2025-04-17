import datetime
import logging
from typing import List, Optional
from urllib.parse import urlparse

from internetarchive import ArchiveSession, Search

from wikiteam3.dumpgenerator.config import Config

IA_MAX_RETRY = 5
logger = logging.getLogger(__name__)


def ia_s3_tasks_load_avg(session: ArchiveSession) -> float:
    api = "https://s3.us.archive.org/?check_limit=1"
    r = session.get(api, timeout=16)
    r.raise_for_status()
    r_json = r.json()
    total_tasks_queued = r_json["detail"]["total_tasks_queued"]
    total_global_limit = r_json["detail"]["total_global_limit"]
    logger.info(f"ia_s3_load_avg(): {total_tasks_queued} / {total_global_limit}")
    return total_tasks_queued / total_global_limit


def search_ia(apiurl: Optional[str] = None, indexurl: Optional[str] = None, addeddate_intervals: Optional[List[str]] = None):
    if apiurl is None:
        apiurl = 'api.php'.join(indexurl.rsplit('index.php', 1)) if indexurl else None
    if indexurl is None:
        indexurl = 'index.php'.join(apiurl.rsplit('api.php', 1)) if apiurl else None

    if not (apiurl or indexurl):
        raise ValueError('apiurl or indexurl must be provided')

    ia_session = ArchiveSession()

    urls_to_check: List[str] = [
        urlparse(url)._replace(scheme=scheme).geturl()
        for url in (apiurl, indexurl) if url
        for scheme in ('http', 'https')
    ]

    query = '(' + ' OR '.join([f'originalurl:"{url}"' for url in urls_to_check]) + ')'
    if addeddate_intervals:
        query += f' AND addeddate:[{addeddate_intervals[0]} TO {addeddate_intervals[1]}]'
    search = Search(ia_session, query=query,
                    fields=['identifier', 'addeddate', 'title', 'subject', 'originalurl', 'uploader', 'item_size'],
                    sorts=['addeddate desc'], # newest first
                    max_retries=IA_MAX_RETRY, # default 5
                    )
    item = None
    for result in search: # only get the first result
        # {'identifier': 'wiki-wikiothingxyz-20230315',
        # 'addeddate': '2023-03-15T01:42:12Z',
        # 'subject': ['wiki', 'wikiteam', 'MediaWiki', .....]}
        if result['originalurl'].lower() in [
            apiurl.lower() if apiurl else None,
            indexurl.lower() if indexurl else None
            ]:
            logger.info(f'Original URL match: {result}')
            yield result
            item = result
        else:
            logger.warning(f'Original URL mismatch: {result}')

    if item is None:
        logger.warning('No suitable dump found at Internet Archive')
        return # skip


def search_ia_recent(config: Config, days: int = 365):

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_utc_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    one_year_ago = now_utc - datetime.timedelta(days=days)
    one_year_ago_iso = one_year_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    addeddate_intervals = [one_year_ago_iso, now_utc_iso]

    for item in search_ia(apiurl=config.api, indexurl=config.index, addeddate_intervals=addeddate_intervals):
        yield item


def any_recent_ia_item_exists(config: Config, days: int = 365):
    for item in search_ia_recent(config=config, days=days):
        print('Found an existing dump at Internet Archive')
        print(item)
        print(f'https://archive.org/details/{item["identifier"]}')
        return True

    return False


def search_ia_all(config: Config):
    for item in search_ia(apiurl=config.api, indexurl=config.index):
        yield item
