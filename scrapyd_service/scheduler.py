from zope.interface import implementer

from .interfaces import ISpiderScheduler
from .utils import get_spider_queues, get_resources
from scrapyd.spiderqueue import SqliteSpiderQueue
from pathlib import Path


@implementer(ISpiderScheduler)
class SpiderScheduler(object):

    def __init__(self, config):
        self.config = config
        self.update_projects()

    def schedule(self, project, spider_name, priority=0.0, **spider_args):
        q = self.queues[project]
        # priority passed as kw for compat w/ custom queue. TODO use pos in 1.4
        if spider_args.get("name"):
            raise ValueError("spiders自定义参数中不能包含name字段")
        q.add(spider_name, priority=priority, **spider_args)

    def list_projects(self):
        return self.queues.keys()

    def update_projects(self):
        self.queues = get_spider_queues(self.config)

    def add_project(self, project):
        '''动态添加一个爬虫项目'''
        # 写入内存config
        self.config.cp.set("projects", project, project)
        # cfg path
        base_project_path = dict(self.config.items("cluster", ())).get(
            "local_crawler_code_path")
        proj_path = str(Path(base_project_path).joinpath(project))
        cfg_resources = get_resources(proj_path)
        if cfg_resources:
            self.config.cp.set("cfg", project, list(cfg_resources)[0])
        self.config.cp.set("settings", project, f"{project}.settings")
        # 备份config到文件
        config_path = Path(__file__).parent.joinpath(
            "conf/scrapyd_service.conf")
        with open(str(config_path), "w", encoding="utf-8") as fp:
            self.config.cp.write(fp)
