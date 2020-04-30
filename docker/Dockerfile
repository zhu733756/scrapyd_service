# 基于镜像基础
FROM python:3.7

# 设置代码文件夹工作目录 /app
WORKDIR /home/spider/app

# 复制当前代码文件到容器中 /app
COPY . /home/spider/app/source
COPY ./docker/run.sh /app/run.sh

# 安装所需的包
RUN cd /home/spider/app/source \
    && pip install  -r requirements.txt \
    && chmod a+x /home/spider/app/run.sh

VOLUME /home/spider/app/scrapyd_service
CMD /bin/bash /home/spider/app/run.sh

# Run app.py when the container launches
