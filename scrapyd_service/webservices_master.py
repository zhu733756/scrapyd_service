from scrapyd.webservice import WsResource
import uuid
from scrapyd.utils import native_stringify_dict, UtilsCache
from copy import copy
from .utils import get_spider_list
import os
import pathlib
import time
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO
from .webservices_api import DistributedScrapydApi
import six
from subprocess import Popen, PIPE


class DaemonStatus(WsResource):

    def render_GET(self, txrequest):
        pending = sum(q.count() for q in self.root.poller.queues.values())
        running = len(self.root.launcher.processes)
        finished = len(self.root.launcher.finished.load())

        return {"node_name": self.root.node_name, "status": "ok", "pending": pending, "running": running, "finished": finished}


class Schedule(WsResource):

    def load_balance(self, project, spider, priority, **args):
        '''
        负载均衡,比较pending+running的值
        '''
        local_pending = sum(q.count()
                            for q in self.root.poller.queues.values())
        local_runing = len(self.root.launcher.processes)
        local_pushed_jobs = local_pending + local_runing
        choice = self.root.master_host
        other_slave_hosts = copy(self.root.ping.available_slave_hosts)
        for slave in other_slave_hosts:
            client = DistributedScrapydApi(
                target=f'http://{slave}', auth=self.root.auth)
            try:
                jobs = client.list_jobs(project=project)
                slave_pushed_jobs = len(jobs["pending"]) + len(jobs["running"])
                if slave_pushed_jobs < local_pushed_jobs:
                    choice = slave
            except:
                pass
        if choice != self.root.master_host:
            client = DistributedScrapydApi(
                target=f'http://{choice}', auth=self.root.auth)
            kwargs = copy(args)
            kwargs.pop("project", None)
            kwargs.pop("spider", None)
            client_node = client.schedule(
                project, spider, **kwargs)["node_name"]
        else:
            self.root.scheduler.schedule(
                project, spider, priority=priority, **args)
            client_node = self.root.node_name
        return client_node

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
            return {"node_name": self.root.node_name, "status": "error", "message": "spider '%s' not found" % spider}
        args['settings'] = settings
        jobid = args.pop('jobid', uuid.uuid1().hex)
        args['_job'] = jobid
        node_name = self.load_balance(
            project, spider, priority=priority, **args)
        return {"cluster": self.root.cluster_name, "node_name": node_name, "status": "ok", "jobid": jobid}


class Cancel(WsResource):

    def cancel_cluster_jobs(self, project, jobid, signal, host):
        other_slave_hosts = [host] if host else copy(
            self.root.ping.available_slave_hosts)
        for slave in other_slave_hosts:
            client = DistributedScrapydApi(
                target=f'http://{slave}', auth=self.root.auth)
            json = client.cancel(project, jobid, signal)
            prevstate = json.get("prevstate", "not found")
            if prevstate != "not found":
                return json.get("node_name")
        return None

    def render_POST(self, txrequest):
        args = dict((k, v[0])
                    for k, v in native_stringify_dict(copy(txrequest.args),
                                                      keys_only=False).items())
        project = args['project']
        jobid = args['job']
        signal = args.get('signal', 'TERM')
        host = args.get("host")
        prevstate = None
        queue = self.root.poller.queues[project]
        c = queue.remove(lambda x: x["_job"] == jobid)
        if c:
            prevstate = "pending"
        else:
            prevstate = "not found"
        spiders = self.root.launcher.processes.values()
        for s in spiders:
            if s.job == jobid:
                s.transport.signalProcess(signal)
                prevstate = "running"
        node_name = self.root.node_name
        if prevstate == "not found":
            node_name = self.cancel_cluster_jobs(
                project, jobid, signal, host)
        return {"cluster": self.root.cluster_name, "node_name": node_name, "status": "ok", "prevstate": prevstate}


class ListProjects(WsResource):

    def load_cluser_projects(self, projects):
        other_slave_hosts = copy(self.root.ping.available_slave_hosts)
        for slave in other_slave_hosts:
            client = DistributedScrapydApi(
                target=f'http://{slave}', auth=self.root.auth)
            projects.extend(client.list_projects())
        return list(set(projects))

    def render_GET(self, txrequest):
        projects = list(self.root.scheduler.list_projects())
        if not self.root.all_code_is_same:
            projects = self.load_cluser_projects(projects)
        return {"cluster": self.root.cluster_name, "status": "ok", "projects": projects}


class ListSpiders(WsResource):

    def load_cluser_spiders(self, project, spiders):
        other_slave_hosts = copy(self.root.ping.available_slave_hosts)
        for slave in other_slave_hosts:
            client = DistributedScrapydApi(
                target=f'http://{slave}', auth=self.root.auth)
            spiders.extend(client.list_spiders(project))
        return list(set(spiders))

    def render_GET(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        spiders = get_spider_list(project, self.root.setting)
        if not self.root.all_code_is_same:
            spiders = self.load_cluser_spiders(project, spiders)
        return {"cluster": self.root.cluster_name, "status": "ok", "spiders": spiders}


class ListJobs(WsResource):

    def load_cluser_jobs(self, project, jobs_details):
        other_slave_hosts = copy(self.root.ping.available_slave_hosts)
        for slave in other_slave_hosts:
            client = DistributedScrapydApi(
                target=f'http://{slave}', auth=self.root.auth)
            jobs = client.list_jobs(project)
            jobs_details.append({
                "node_name": jobs["node_name"],
                "finished": jobs["finished"],
                "running": jobs["running"],
                "pending": jobs["pending"],
            })
        return jobs_details

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
                     "end_time": s.end_time} for s in self.root.launcher.finished.load()
                    if s.project == project]
        job_details = [{
            "node_name": self.root.node_name,
            "running": running,
            "finished": finished,
            "pending": pending
        }]
        job_details = self.load_cluser_jobs(project, job_details)
        return {"cluster": self.root.cluster_name, "status": "ok",  "project": project, "job_details": job_details}


class DeleteProject(WsResource):

    def delete_cluser_project(self, project):
        other_slave_hosts = copy(self.root.ping.available_slave_hosts)
        for slave in other_slave_hosts:
            client = DistributedScrapydApi(
                target=f'http://{slave}', auth=self.root.auth)
            client.delete_project(project)

    def render_POST(self, txrequest):
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        self._delete_project(project)
        UtilsCache.invalid_cache(project)
        self.delete_cluser_project(project)
        return {"cluster": self.root.cluster_name, "status": "ok"}

    def _delete_project(self, project):
        cfg_path = self.root.cfg_resources.get(project)
        project_path = pathlib.Path(cfg_path).parent
        if project_path and project_path.exists():
            os.remove(str(project_path))
            self.root.update_projects()


class PullCode(WsResource):

    def pull_code_for_cluster(self, project, message_details):
        other_slave_hosts = copy(self.root.ping.available_slave_hosts)
        for slave in other_slave_hosts:
            client = DistributedScrapydApi(
                target=f'http://{slave}', auth=self.root.auth)
            rel = client.pull_code(project)
            message_details.append({
                "node_name": rel.get("node_name"),
                "message": rel.get("message"),
                "status": rel.get("status"),
            })
        return message_details

    def render_POST(self, txrequest):
        if not self.root.pull_code_by_git:
            return {"cluster": self.root.cluster_name, "status": "error", "message": "canot pull code by git"}
        args = native_stringify_dict(copy(txrequest.args), keys_only=False)
        project = args['project'][0]
        cfg_filepath = self.root.cfg_resources.get(project)
        project_path = str(pathlib.Path(cfg_filepath).parent)
        os.chdir(project_path)
        cmd = f"git checkout -- . && git pull origin {self.root.git_branch}"
        proc = Popen(cmd.split(" "), shell=True, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        if proc.returncode:
            msg = err or out or ''
            msg = msg.decode('utf8')
            raise RuntimeError(msg.encode('unicode_escape')
                               if six.PY2 else msg)
        # FIXME: can we reliably decode as UTF-8?
        # scrapy list does `print(list)`
        tmp = out.decode('utf-8').splitlines()
        message_details = [
            {"node_name": self.root.node_name, "message": tmp}
        ]
        message_details = self.pull_code_for_cluster(project, message_details)
        return {"cluster": self.root.cluster_name, "status": "ok", "message_details": message_details}
