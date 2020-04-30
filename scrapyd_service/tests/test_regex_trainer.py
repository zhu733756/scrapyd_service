from scrapyd_api import ScrapydAPI


api = ScrapydAPI(timeout=10)


def schedule():
    r = api.schedule(project="regex_trainer", spider="regex_trainer",
                     web_name="解放网", start_urls="https://www.jfdaily.com/home",
                     settings={"LOG_LEVEL": "DEBUG"})
    print(r)


def list_projects():
    r = api.list_projects()
    print(r)


def list_spiders():
    r = api.list_spiders(project="regex_trainer")
    print(r)


def list_jobs():
    r = api.list_jobs(project="regex_trainer")
    print(r)


def cancel(jobid):
    r = api.cancel(project="regex_trainer",
                   job=jobid)
    print(r)


if __name__ == "__main__":
    # schedule()
    # list_projects()
    # list_spiders()
    # schedule()
    list_jobs()
    # cancel("f9fb6038851011eaa89df8a2d6ce3ea0")
