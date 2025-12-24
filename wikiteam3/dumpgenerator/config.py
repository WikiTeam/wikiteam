import dataclasses
from dataclasses import field
import json
from typing import List, Optional

import requests


def _dataclass_from_dict(klass_or_obj, d: dict):
    if isinstance(klass_or_obj, type): # klass
        ret = klass_or_obj()
    else:
        ret = klass_or_obj
    for k,v in d.items():
        if hasattr(ret, k):
            setattr(ret, k, v)
    return ret


@dataclasses.dataclass
class Config:
    def asdict(self):
        return dataclasses.asdict(self)

    # General params
    delay: float = 0.0
    """ Delay between requests """
    retries: int = 0
    """ Number of retries """
    path: str = ''
    """ Path to save the wikidump """
    logs: bool = False
    """
    Save MediaWiki logs #NOTE: this feature is not implemented yet
    https://www.mediawiki.org/wiki/Manual:Logging_table
    """
    date: str = False
    """
    Date of the dump
    `datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")`
    """

    # URL params
    index: str = ''
    api: str = ''

    # Download params
    xml: bool = False
    curonly: bool = False
    xmlapiexport: bool = False
    xmlrevisions: bool = False
    xmlrevisions_page: bool = False
    images: bool = False
    redirects: bool = False
    namespaces: List[int] = field(default_factory=list)
    """ [ALL_NAMESPACE_FLAG] or [int,...] """
    exnamespaces: List[int] = field(default_factory=list)
    """ [REMOVED FEATURE] keep for config backward compatibility. check wikiteam3#35 """

    api_chunksize: int = 0  # arvlimit, ailimit, etc
    export: str = ''
    """ `Special:Export` page name """
    http_method: str = ''
    """ GET/POST """

    # Meta info params
    failfast: bool = False

    templates: bool = False # TODO: rename to `xml_export_include_templates`
    """
    Whether to include `&templates=1` parameter in the `Special:Export` (--xml) export action.
    https://www.mediawiki.org/wiki/Manual:Parameters_to_Special:Export#Available_parameters

    NOTE: this config is not used to control the export of templates namespace (--namespaces).
    """

def new_config(configDict) -> Config:
    return _dataclass_from_dict(Config, configDict)

def load_config(config: Config, config_filename: str):
    """Load config file"""

    config_dict = dataclasses.asdict(config)

    if config.path:
        try:
            with open(f"{config.path}/{config_filename}", encoding="utf-8") as infile:
                config_dict.update(json.load(infile))
            return new_config(config_dict)
        except FileNotFoundError:
            raise

    raise FileNotFoundError(f"Config file {config_filename} not found")

def save_config(config: Config, config_filename: str):
    """Save config file"""

    with open(f"{config.path}/{config_filename}", "w", encoding="utf-8") as outfile:
        json.dump(dataclasses.asdict(config), outfile, indent=4, sort_keys=True)


@dataclasses.dataclass
class OtherConfig:
    resume: bool
    force: bool 
    session: requests.Session 
    bypass_cdn_image_compression: bool 
    add_referer_header: Optional[str] 
    '''None, "auto", {URL}'''
    image_timestamp_interval: Optional[str]
    ''' 2019-01-02T01:36:06Z/2023-08-12T10:36:06Z '''
    ia_wbm_booster: int 

    assert_max_pages: Optional[int] 
    assert_max_edits: Optional[int] 
    assert_max_images: Optional[int] 
    assert_max_images_bytes: Optional[int] 

    hard_retries: int
    """ Number of hard retries """

    upload: bool 
    uploader_args: List[str]