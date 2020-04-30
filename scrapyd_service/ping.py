from zope.interface import implementer
from twisted.internet.defer import inlineCallbacks

from .interfaces import IHostPinger
import json
from .webservices_api import DistributedScrapydApi
from twisted.python import log


@implementer(IHostPinger)
class HostPinger(object):

    def __init__(self, config):
        self.config = config
        self.registered_slave_hosts = self.get_registered_slave_hosts(config)
        self.available_slave_hosts = []
        self.auth = self.get_auth(config)

    def get_registered_slave_hosts(self, config):
        bind_address = config.get("bind_address", "127.0.0.1")
        port = config.get("http_port", 6800)
        master_host = f"{bind_address}:{port}"
        cluster = dict(config.items("cluster", ()))
        slave_hosts = json.loads(cluster.get("slave_hosts", '[]'))
        unduplicated_slave_hosts = set(
            slave_hosts).difference(set([master_host]))
        log.msg(
            f"Reading slave hosts from the config:{unduplicated_slave_hosts}")
        return unduplicated_slave_hosts

    def get_auth(self, config):
        username = config.get("username")
        password = config.get("password")
        auth = None
        if username and password:
            auth = {
                "username": username,
                "password": password
            }
        return auth

    @inlineCallbacks
    def ping(self):
        if len(self.registered_slave_hosts) == 0:
            return
        drops = set()
        for slave in self.registered_slave_hosts:
            try:
                client = DistributedScrapydApi(
                    target=f'http://{slave}', auth=self.auth, timeout=10)
                yield client.daemon_status()
            except:
                drops.add(slave)
        self.available_slave_hosts = \
            self.registered_slave_hosts.difference(drops)
        if len(drops) > 0:
            log.msg(
                f"The slave hosts:{','.join(drops)} are lost, please check it....")
        if len(self.available_slave_hosts) == 0:
            log.msg("No available salves")
