import pkgutil

__version__ = pkgutil.get_data(__package__, 'VERSION').decode('ascii').strip()
version_info = tuple(__version__.split('.')[:3])


from scrapy.utils.misc import load_object
from .config import Config


def get_application(config_path=None):
    if config_path is None:
        config = Config()
    else:
        config = Config(extra_sources=config_path)
    apppath = config.get('application', 'scrapyd_service.app.application')
    appfunc = load_object(apppath)
    return appfunc(config)
