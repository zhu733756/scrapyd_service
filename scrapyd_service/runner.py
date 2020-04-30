import sys
import os
from .utils import get_project_settings


def main():
    from scrapy.cmdline import execute
    settings = get_project_settings()
    if "LOG_FILE" in settings:
        settings["LOG_FILE"] = os.environ.get("SCRAPY_LOG_FILE")
    execute(settings=settings)

if __name__ == '__main__':
    main()
