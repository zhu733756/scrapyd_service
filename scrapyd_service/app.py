import sys
import pathlib

from twisted.application.service import Application
from twisted.application.internet import TimerService, TCPServer
from twisted.web import server
from twisted.python import log
from twisted.cred.portal import Portal
from twisted.web.guard import HTTPAuthSessionWrapper, BasicCredentialFactory

from scrapy.utils.misc import load_object

from .interfaces import IEggStorage, IPoller, ISpiderScheduler, IEnvironment, IHostPinger
# from .eggstorage import FilesystemEggStorage
from .scheduler import SpiderScheduler
from .poller import QueuePoller
from .ping import HostPinger
from .environ import Environment
from .auth import PublicHTMLRealm, StringCredentialsChecker
from .utils import get_resources
from configparser import ConfigParser
import json
import os
from twisted.web import proxy, server


def get_env(config):
    identity = os.getenv("identity")
    if identity:
        config.cp.set("cluster", "identity", identity)
    node_name = os.getenv("node")
    if node_name:
        config.cp.set("cluster", "node_name", node_name)
    slave_hosts = os.getenv("slaves")
    if slave_hosts:
        config.cp.set("cluster", "slave_hosts", slave_hosts)
    code_path = os.getenv("codepath")
    if code_path:
        config.cp.set("cluster", "local_crawler_code_path", code_path)
    branch = os.getenv("branch")
    if branch:
        config.cp.set("cluster", "branch", branch)

    bind_address = os.getenv("bind_address","127.0.0.1")
    http_port = os.getenv("http_port","6800")
    if bind_address and http_port:
        config.cp.set("scrapyd", "bind_address", bind_address)
        config.cp.set("scrapyd", "http_port", http_port)
    return config


def keep_project_cfgfile(config):
    '''
    根据cfg文件确定爬虫项目,给config添加section
    '''
    config = get_env(config)
    config.cp.add_section("cfg")
    base_project_path = dict(config.items("cluster", ())).get(
        "local_crawler_code_path")
    projects = dict(config.items("projects", ())).values()
    cfg_resources = []
    for project in projects:
        proj_path = str(pathlib.Path(base_project_path).joinpath(project))
        cfg_resources += get_resources(proj_path)
    if not config.cp.has_section("settings"):
        config.cp.add_section("settings")
    reader = ConfigParser()
    for r in cfg_resources:
        reader.read(r)
        project = reader.get("deploy", "project")
        settings_val = reader.get("settings", "default")
        config.cp.set("cfg", project, r)
        config.cp.set("settings", project, settings_val)
    return config


def application(config):
    app = Application("Scrapyd-Cluster")
    config = keep_project_cfgfile(config)
    http_port = config.getint('http_port', 6800)
    bind_address = config.get('bind_address', '127.0.0.1')
    poll_interval = config.getfloat('poll_interval', 5)

    poller = QueuePoller(config)

    # eggstorage = FilesystemEggStorage(config)
    scheduler = SpiderScheduler(config)
    environment = Environment(config)

    app.setComponent(IPoller, poller)
    # app.setComponent(IEggStorage, eggstorage)
    app.setComponent(ISpiderScheduler, scheduler)
    app.setComponent(IEnvironment, environment)

    laupath = config.get('launcher', 'scrapyd.launcher.Launcher')
    laucls = load_object(laupath)
    launcher = laucls(config, app)

    timer = TimerService(poll_interval, poller.poll)

    webpath = config.get('webroot', 'scrapyd.website.Root')
    webcls = load_object(webpath)

    username = config.get('username', '')
    password = config.get('password', '')
    if username and password:
        if ':' in username:
            sys.exit("The `username` option contains illegal character ':', "
                     "check and update the configuration file of Scrapyd")
        portal = Portal(PublicHTMLRealm(webcls(config, app)),
                        [StringCredentialsChecker(username, password)])
        credential_factory = BasicCredentialFactory("Auth")
        resource = HTTPAuthSessionWrapper(portal, [credential_factory])
        log.msg("Basic authentication enabled")
    else:
        resource = webcls(config, app)
        log.msg(
            "Basic authentication disabled as either `username` or `password` is unset")
    webservice = TCPServer(http_port, server.Site(
        resource), interface=bind_address)
    log.msg(format="Scrapyd-Service web console available at http://%(bind_address)s:%(http_port)s/",
            bind_address=bind_address, http_port=http_port)

    launcher.setServiceParent(app)
    timer.setServiceParent(app)
    webservice.setServiceParent(app)

    is_master = dict(config.items("cluster", ())).get("node_name") == "master"
    has_salves = bool(dict(config.items("cluster", ())).get("slave_hosts"))
    if is_master and has_salves:
        ping_interval = config.getfloat('ping_interval', 5)
        host_pinger = HostPinger(config)
        app.setComponent(IHostPinger, host_pinger)
        pinger = TimerService(ping_interval, host_pinger.ping)
        pinger.setServiceParent(app)
        log.msg("The master has prepared to ping")

    return app
