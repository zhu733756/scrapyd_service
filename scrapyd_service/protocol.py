
import sys
from twisted.internet import defer, error, protocol, reactor
from twisted.python import log
import socket


class ClusterLogProtocol(protocol.ProcessProtocol):

    def __init__(self, ip, port, listen_port):
        self.ip = ip
        self.port = port
        self.listen_port = listen_port
        self.pid = None
        self.deferred = defer.Deferred()

    def outReceived(self, data):
        log.msg(data.rstrip(), system="ClusterLog,%d/stdout" % self.pid)

    def errReceived(self, data):
        log.msg(data.rstrip(), system="ClusterLog,%d/stderr" % self.pid)

    def processExited(self, data):
        log.msg(data, system="ClusterLog,%d/stderr" % self.pid)

    def connectionMade(self):
        self.pid = self.transport.pid
        self.log("Process started: ")

    def processEnded(self, status):
        if isinstance(status.value, error.ProcessDone):
            self.log("Process finished: ")
        else:
            self.log("Process died: exitstatus=%r " % status.value.exitCode)
        self.deferred.callback(self)

    def log(self, action):
        fmt = 'ip=%(ip)r,port=%(port)r,pid=%(pid)r,listening at%(listen_port)r'
        log.msg(format=fmt, ip=self.ip, pid=self.pid,
                port=self.port, listen_port=self.listen_port)


def is_available(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', int(port)))
        s.shutdown(2)
        return False
    except:
        pass
    return True


def make_listenport():
    port = 6888
    while port <= 9999:
        if is_available(port):
            break
        port += 1
    return port
