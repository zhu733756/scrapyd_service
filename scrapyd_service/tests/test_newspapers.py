import sys
from pathlib import Path
project_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_path))

from scrapyd_service.webservices_api import DistributedScrapydApi

api = DistributedScrapydApi(timeout=10)


def pull_code():
    r = api.pull_code(project="newspapers")
    print(r)


def schedule():
    r = api.schedule(project="newspapers", spider="宣城日报")
    print(r)


def list_projects():
    r = api.list_projects()
    print(r)


def list_spiders():
    r = api.list_spiders(project="newspapers")
    print(r)


def list_jobs():
    r = api.list_jobs(project="newspapers")
    print(r)


def cancel():
    r = api.cancel(project="newspapers",
                   job="d8b023647fbe11eaabcef8a2d6ce3ea0")
    print(r)


def deamon_status():
    r = api.daemon_status()
    print(r)

if __name__ == "__main__":
    # pull_code()
    # schedule()
    # list_projects()
    # list_spiders()
    schedule()
