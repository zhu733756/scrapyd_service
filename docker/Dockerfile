FROM python:3.7.1

MAINTAINER zhu733756 1079333812@qq.com

RUN mkdir -p /app/source/scrapyd_service
RUN mkdir -p /app/spider/DataCrawl
WORKDIR /app/source

COPY ./docker/etc/pip.conf /root/.pip/pip.conf
COPY ./scrapyd_service /app/source/scrapyd_service
COPY ./requirements.txt /app/source/scrapyd_service/requirements.txt
COPY ./docker/etc/scrapyd_service.conf /app/source/scrapyd_service/conf/scrapyd_service.conf
COPY ./docker/run.sh /app/run.sh

RUN cd /app/source/scrapyd_service && pip install -r requirements.txt && chmod a+x /app/run.sh

CMD /bin/bash /app/run.sh
