import os
import re
import sys
import pathlib
from scrapyd.spiderqueue import SqliteSpiderQueue
from scrapyd.utils import _to_native_str, native_stringify_dict, UtilsCache
from six.moves import cPickle as pickle
from scrapy.spiderloader import SpiderLoader
from configparser import ConfigParser

from scrapy.settings import Settings
from scrapy.utils.misc import load_object
from scrapyd.utils import get_spider_list
from shutil import ignore_patterns,copy2,copystat


def get_spider_queues(config):
    """Return a dict of Spider Queues keyed by project name"""
    dbsdir = config.get('dbs_dir', 'dbs')
    if not os.path.exists(dbsdir):
        os.makedirs(dbsdir)
    d = {}
    projects = get_project_list(config)
    if projects is None:
        raise Exception("当前配置找不到任何scrapy爬虫项目！")
    for project in projects:
        dbpath = os.path.join(dbsdir, '%s.db' % project)
        d[project] = SqliteSpiderQueue(dbpath)
    return d


def closest_scrapy_cfg(path='.', deep=0, method="down", resources=[]):
    """
    Return the path to the closest scrapy.cfg file
    """
    dirpath = pathlib.Path(path).absolute()
    if deep >= 2 or re.match("^[\._]", dirpath.name) or dirpath.is_file():
        return
    # 如果是文件夹
    cfgfilepath = dirpath.joinpath("scrapy.cfg")
    if cfgfilepath.exists():
        resources.append(str(cfgfilepath))
        return
    if method == "down":
        for x in dirpath.iterdir():
            closest_scrapy_cfg(x, deep + 1, "down", resources)
    else:
        closest_scrapy_cfg(dirpath.parent, deep + 1, "up", resources)


def get_resources(path):
    '''
    @功能:上下递归两级寻找scarpy.cfg文件
    '''
    resources = []
    target_path = pathlib.Path(path)
    if not target_path.exists():
        return
    if target_path.is_file() and path.name == "scrapy.cfg":
        # 直接给定cfg path
        resources.append(str(target_path))
    if len(resources) == 0:
        # 向上寻找,直接从父目录开始递归
        closest_scrapy_cfg(target_path.parent, 0, "up", resources)
    if len(resources) == 0:
        # 向下寻找,从当前目录和子目录开始
        closest_scrapy_cfg(target_path, 0, "down", resources)
    if len(resources) > 0:
        resources = set(resources)
        for resource in resources:
            project_path = str(pathlib.Path(resource).parent)
            if project_path not in sys.path:
                sys.path.append(project_path)
    return resources


def get_project_list(config):
    settings = dict(config.items("settings"))
    if settings:
        return list(settings.keys())


def get_spider_list(project, setting):
    """Return the spider list from the given project, using the given runner"""
    if "cache" not in get_spider_list.__dict__:
        get_spider_list.cache = UtilsCache()
    if project in get_spider_list.cache.cache_manager:
        return get_spider_list.cache[project]
    spiders = []
    settings_module_path = setting.get(project)
    settings = Settings()
    if settings_module_path:
        settings.setmodule(settings_module_path, priority='project')
    spider_loader = SpiderLoader.from_settings(settings)
    spiders = spider_loader.list()
    get_spider_list.cache[project] = spiders
    return spiders


def get_crawl_args(message, env=os.environ):
    """Return the command-line arguments to use for the scrapy crawl process
    that will be started for this message
    """
    msg = message.copy()
    project, spider = msg.pop('_spider'), msg.pop('_project')
    args = ["--name", project]
    args += ["--project", spider]
    settings = msg.pop('settings', {})
    if not settings.get("LOG_FILE"):
        settings.update(
            {"LOG_FILE": str(pathlib.Path(env.get('SCRAPY_LOG_FILE')).absolute())})
    for k, v in native_stringify_dict(msg, keys_only=False).items():
        args += [f'--{k.replace("_","") if k.startswith("_") else k}']
        args += [v]
    for k, v in native_stringify_dict(settings, keys_only=False).items():
        args += ['--settings']
        args += ['%s=%s' % (k, v)]
    return args

def get_project_settings(st=None):
    env = os.environ.copy()
    project_path = env.get('SCRAPY_PROJECT_PATH')
    if project_path and project_path not in sys.path:
        sys.path.insert(0, project_path)
    settings = Settings(st)
    settings_module_path = env.get('SCRAPY_SETTINGS_MODULE')
    settings.setmodule(settings_module_path, priority='project')
    return settings


def _copytree(src, dst):
    """复制一份项目结构"""

    ignore = ignore_patterns('*.pyc', '.svn')
    names = os.listdir(src)
    ignored_names = ignore(src, names)

    if not os.path.exists(dst):
        os.makedirs(dst)

    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            _copytree(srcname, dstname)
        else:
            copy2(srcname, dstname)
    copystat(src, dst)
