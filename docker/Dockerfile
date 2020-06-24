FROM python:3.7.1

MAINTAINER zhu733756 1079333812@qq.com

RUN mkdir -p /app/source/scrapyd_service
RUN mkdir -p /app/spider/DataCrawl
WORKDIR /app/source

COPY ./docker/etc/pip.conf /root/.pip/pip.conf
# 拷贝爬虫代码到容器
COPY ./DataCrawl /app/spider/DataCrawl
## 安装爬虫依赖
RUN cd  /app/spider/DataCrawl && pip install -r requirements.txt
COPY ./scrapyd_service /app/source/scrapyd_service
COPY ./requirements.txt /app/source/scrapyd_service/requirements.txt
COPY ./docker/etc/scrapyd_service.conf /etc/scrapyd_service/conf/scrapyd_service.conf
COPY ./docker/run.sh /app/run.sh

RUN cd /app/source/scrapyd_service && pip install -r requirements.txt && chmod a+x /app/run.sh
RUN apt-get install -y git

CMD /bin/bash /app/run.sh
