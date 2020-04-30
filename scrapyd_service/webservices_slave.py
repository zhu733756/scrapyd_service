from scrapyd.webservice import DaemonStatus, WsResource
import uuid
from scrapyd.utils import native_stringify_dict, UtilsCache
from copy import copy
from .utils import get_spider_list, get_resource
import os
import pathlib
import time
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
import six
from subprocess import Popen, PIPE


class Schedule(WsResource):

    def render_POST(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        settings = args.pop('setting', [])
        settings = dict(x.split('=', 1) for x in settings)
        args = dict((k, v[0]) for k, v in args.items())
        project = args.pop('project')
        spider = args.pop('spider')
        priority = float(args.pop('priority', 0))
        spiders = get_spider_list(project, self.root.setting)
        if not spider in spiders:
            return {"status": "error", "message": "spider '%s' not found" % spider}
        args['settings'] = settings
        jobid = args.pop('jobid', uuid.uuid1().hex)
        args['_job'] = jobid
        self.root.scheduler.schedule(
            project, spider, priority=priority, **args)
        return {"node_name": self.root.node_name, "status": "ok", "jobid": jobid}


class Cancel(WsResource):

    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        project = args['project']
        jobid = args['job']
        signal = args.get('signal', 'TERM')
        prevstate = None
        queue = self.root.poller.queues[project]
        c = queue.remove(lambda x: x["_job"] == jobid)
        if c:
            prevstate = "pending"
        spiders = self.root.launcher.processes.values()
        for s in spiders:
            if s.job == jobid:
                s.transport.signalProcess(signal)
                prevstate = "running"
        return {"node_name": self.root.node_name, "status": "ok", "prevstate": prevstate}


class ListProjects(WsResource):

    def render_GET(self, txrequest):
        projects = list(self.root.scheduler.list_projects())
        return {"node_name": self.root.node_name, "status": "ok", "projects": projects}


class ListSpiders(WsResource):

    def render_GET(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        spiders = get_spider_list(project, self.root.setting)
        return {"node_name": self.root.node_name, "status": "ok", "spiders": spiders}


class ListVersions(WsResource):

    def render_GET(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        versions = get_spider_list(project, self.root.setting)
        return {"node_name": self.root.node_name, "status": "ok", "versions": versions}


class ListJobs(WsResource):

    def render_GET(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        spiders = self.root.launcher.processes.values()
        running = [{"id": s.job, "spider": s.spider, "pid": s.pid,
                    "start_time": s.start_time}
                   for s in spiders if s.project == project]
        queue = self.root.poller.queues[project]
        pending = [{"id": x["_job"], "spider": x["name"]}
                   for x in queue.list()]
        finished = [{"id": s.job, "spider": s.spider,
                     "start_time": s.start_time,
                     "end_time": s.end_time} for s in self.root.launcher.finished
                    if s.project == project]
        return {"node_name": self.root.node_name, "status": "ok", "pending": pending, "running": running, "finished": finished}


class DeleteProject(WsResource):

    def render_POST(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        self._delete_project(project)
        UtilsCache.invalid_cache(project)
        return {"node_name": self.root.node_name, "status": "ok"}

    def _delete_project(self, project):
        cfg_path = self.root.cfg_resources.get(project)
        project_path = pathlib.Path(cfg_path).parent
        if project_path and project_path.exists():
            os.remove(str(project_path))
            self.root.update_projects()


class PullCode(WsResource):

    def render_POST(self, txrequest):
        if not self.root.pull_code_by_git:
            return {"node_name": self.root.node_name, "status": "error", "message": "canot pull code by git"}
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        cfg_filepath = self.root.cfg_resources.get(project)
        project_path = str(pathlib.Path(cfg_filepath).parent)
        os.chdir(project_path)
        cmd = f"git checkout -- . && git pull origin {self.root.git_branch}"
        proc = Popen(cmd.split(" "), stdout=PIPE, stderr=PIPE, env=env)
        out, err = proc.communicate()
        if proc.returncode:
            msg = err or out or ''
            msg = msg.decode('utf8')
            raise RuntimeError(msg.encode('unicode_escape')
                               if six.PY2 else msg)
        # FIXME: can we reliably decode as UTF-8?
        # scrapy list does `print(list)`
        tmp = out.decode('utf-8').splitlines()
        return {"node_name": self.root.node_name, "status": "ok", "message": tmp}
