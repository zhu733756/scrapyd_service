## Scrapyd_Service

#### 1 功能:

1.1 Scrapyd_Service(以下简称SS)是对爬虫调度系统scrapyd的分布式主从架构扩展, 旨在将多机scrapyd服务串联成一个调度系统, 方便地打造数据采集监控系统

1.2 如果你的爬虫是git管理的, 可以使用pullcode.json Api自动拉取你的最新代码

1.3 如果你希望一台主机获取其他scrapyd服务是否在线, ping功能必不可少, 你只需配置分机hosts以及ping的频率

1.4 scrapyd调度系统的需要打包egg文件, 一系列操作相当繁琐, 现在你只需要把爬虫项目路径暴露给SS, 就可以远程调度了, 十分方便。当然, 作为代价, 所有与版本号有关的api被修改或是取消

1.5 scrapyd获取爬虫状态时, 已完成的爬虫信息是写在内存中的, 一旦该服务宕机后, 这一部分将不会存在, SS使用sqlite数据库将爬虫状态磁盘化了, 即便宕机, 重启也能获取先前的运行状态, 并设立了再空闲时间删除历史状态的机制, 无需担心爬虫文件冗余的问题

1.6 为了节省资源, SS中的master服务也会被部署成一个scrapyd服务。

1.7 为了解决分布式日志显示的问题, 添加了动态代理转发功能, 在master上实时创建, 定时回收资源。

#### 2 配置文件
2.1 分布式config名称必须为scrapyd_service.conf, 相对路径scrapyd_service/conf/scrapyd_service.conf

2.2 master配置
``` master's conf
[cluster]
cluster_name = cluster  # 集群名称
node_name = master  # 节点名称
identity = master  # master只能有一个,slave可以有多个
slave_hosts = ["127.0.0.1:6801"]  # 从机配置
is_all_code_same = true
pull_code_by_git = true
branch = develop  # git所在的branch

[projects]
newspapers = 你的爬虫项目路径

[scrapyd]
bind_address = 127.0.0.1
http_port = 6800
username =
password =
logs_dir = logs
dbs_dir = dbs
items_dir =
jobs_to_keep = 5
max_proc = 0
max_proc_per_cpu = 4
finished_to_keep = 100
poll_interval = 5.0
ping_interval = 5.0  # 设置ping从机的频次
debug = off
runner = scrapyd_service.runner
application = scrapyd_service.app.application
launcher = scrapyd_service.launcher.Launcher
webroot = scrapyd_service.website.Root

[master-services]
schedule.json = scrapyd_service.webservices_master.Schedule
cancel.json = scrapyd_service.webservices_master.Cancel
listprojects.json = scrapyd_service.webservices_master.ListProjects
listspiders.json = scrapyd_service.webservices_master.ListSpiders
delproject.json = scrapyd_service.webservices_master.DeleteProject
listjobs.json = scrapyd_service.webservices_master.ListJobs
daemonstatus.json = scrapyd_service.webservices_master.DaemonStatus
pullcode.json = scrapyd_service.webservices_master.PullCode
addproject.json = scrapyd_service.webservices_master.AddProject
crawllog.json = scrapyd_service.webservices_master.CrawlLog

[slave-services]
schedule.json = scrapyd_service.webservices_slave.Schedule
cancel.json = scrapyd_service.webservices_slave.Cancel
listprojects.json = scrapyd_service.webservices_slave.ListProjects
listspiders.json = scrapyd_service.webservices_slave.ListSpiders
delproject.json = scrapyd_service.webservices_slave.DeleteProject
listjobs.json = scrapyd_service.webservices_slave.ListJobs
daemonstatus.json = scrapyd_service.webservices_slave.DaemonStatus
pullcode.json = scrapyd_service.webservices_master.PullCode
```

2.3 slave配置
``` slave's config
[cluster]
cluster_name = cluster
node_name = slave001
identity = slave
slave_hosts = []  # 可省略
is_all_code_same = true
pull_code_by_git = true
branch = develop

[projects]
newspapers = 你的爬虫项目路径

[scrapyd]
bind_address = 127.0.0.1
http_port = 6801
username =
password =
logs_dir = logs
dbs_dir = dbs
items_dir =
jobs_to_keep = 5
max_proc = 0
max_proc_per_cpu = 4
finished_to_keep = 100
poll_interval = 5.0
ping_interval = 5.0
debug = off
runner = scrapyd_service.runner
application = scrapyd_service.app.application
launcher = scrapyd_service.launcher.Launcher
webroot = scrapyd_service.website.Root

[master-services]
schedule.json = scrapyd_service.webservices_master.Schedule
cancel.json = scrapyd_service.webservices_master.Cancel
listprojects.json = scrapyd_service.webservices_master.ListProjects
listspiders.json = scrapyd_service.webservices_master.ListSpiders
delproject.json = scrapyd_service.webservices_master.DeleteProject
listjobs.json = scrapyd_service.webservices_master.ListJobs
daemonstatus.json = scrapyd_service.webservices_master.DaemonStatus
pullcode.json = scrapyd_service.webservices_master.PullCode
addproject.json = scrapyd_service.webservices_master.AddProject
crawllog.json = scrapyd_service.webservices_master.CrawlLog

[slave - services]
schedule.json = scrapyd_service.webservices_slave.Schedule
cancel.json = scrapyd_service.webservices_slave.Cancel
listprojects.json = scrapyd_service.webservices_slave.ListProjects
listspiders.json = scrapyd_service.webservices_slave.ListSpiders
delproject.json = scrapyd_service.webservices_slave.DeleteProject
listjobs.json = scrapyd_service.webservices_slave.ListJobs
daemonstatus.json = scrapyd_service.webservices_slave.DaemonStatus
pullcode.json = scrapyd_service.webservices_master.PullCode
```

#### 3 项目启动
```
1 修改配置文件，参考1.2, master最多只能有一个, 配置文件只添加一个
2 cd scrapyd_service
3 pip install - r requirements.txt
4 python3 scrapyd_service / scripts / scrapyd_service_run.py
```

#### 4 关于远程调度api封装
建议参考 scrapyd_service/webservices_api.py
