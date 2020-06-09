FROM python:3.7

MAINTAINER zhu733756 1079333812@qq.com

WORKDIR /app

COPY ./etc/pip.conf /root/.pip/pip.conf
COPY ../scrpyd_service /app/source
COPY ./scrpyd_service.conf /app/source/scrpyd_service/conf/scrapyd_service.conf
COPY ./run.sh /app/run.sh

RUN cd /app/source && pip install -r requirements.txt && chmod a+x /app/run.sh

CMD /bin/bash /app/run.sh
