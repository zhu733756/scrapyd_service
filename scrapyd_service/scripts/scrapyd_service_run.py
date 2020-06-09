#!/usr/bin/env python

from twisted.scripts.twistd import run
from pathlib import Path
from sys import argv, path
import codecs
try:
    import scrapyd_service
except ImportError:
    project_path = Path(__file__).parent.parent.parent
    path.insert(0, str(project_path))
    import scrapyd_service


def main():
    argv[1:1] = ['-n', '-y',
                 str(Path(scrapyd_service.__file__).parent.joinpath('txapp.py'))]
    run()

if __name__ == '__main__':
    main()
