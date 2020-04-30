from zope.interface import Interface
from scrapyd.interfaces import IEggStorage, IEnvironment, IPoller, ISpiderQueue, ISpiderScheduler


class IHostPinger(Interface):
    """A component that pings for the available slave hosts"""

    def ping():
        """ping other hosts on the cluster"""
