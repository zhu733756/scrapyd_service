
from twisted.web import proxy, server


def make_server(ip, port, listen_port, expire=10):
    site = server.Site(proxy.ReverseProxyResource(ip, port, b''))

    from twisted.internet import reactor
    reactor.listenTCP(listen_port, site)
    reactor.callLater(10, reactor.stop)
    reactor.run()


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description="解析需要代理的服务器ip,port,以及本地listen_port")
    parser.add_argument("-i", "--ip", type=str, default="localhost")
    parser.add_argument("-p", "--port", type=int, default=6800)
    parser.add_argument("-l", "--listen", type=int, default=6888)
    parser.add_argument("-e", "--expire", type=int, default=10)
    args = parser.parse_args()
    ip = args.ip
    port = args.port
    listen_port = args.listen
    expire = args.expire
    make_server(ip, port, listen_port, expire)
