import sqlite3
import json
from pathlib import Path
import os
from collections import namedtuple


def singleton(cls):
    _instance = {}

    def getinstance(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return getinstance


@singleton
class FinishedSpidersDB(object):
    """
    finished spiders database
    """

    def __init__(self, dbpath, database="spider_infos.db", table="spiders_finished"):
        dbpath = Path(dbpath)
        if not dbpath.exists():
            os.makedirs(str(Path(dbpath)))
        self.database = str(Path(dbpath).joinpath(database))
        self.table = table
        # about check_same_thread: http://twistedmatrix.com/trac/ticket/4040
        self.conn = sqlite3.connect(self.database, check_same_thread=False)
        q = "create table if not exists %s (id integer primary key, " \
            "project char(50) not null, " \
            "spider char(50) not null," \
            "job char(50) not null," \
            "start_time TEXT not null," \
            "end_time TEXT not null)" % table
        self.conn.execute(q)
        self.properties = ("project",
                           "spider", "job", "start_time", "end_time")
        self.transfer_tuples = namedtuple("transfer_tuples", self.properties)

    def insert(self, process):
        args = [getattr(process, props, None) for props in self.properties]
        q = "insert into %s %s values (?,?,?,?,?)" % (
            self.table, self.properties)
        self.conn.execute(q, tuple(args))
        self.conn.commit()

    def load(self):
        '''
        sqlite eg.
        DELETE FROM StatisticsData WHERE date('now', '-7 day') >= date(start_time);
        DELETE FROM StatisticsData WHERE julianday('now') - julianday(start_time) >= 7;
        '''
        # 获取当天的数据
        q = "select * from %s where date('now') >= date(start_time);" % self.table
        c = self.conn.execute(q)
        if not c.rowcount:  # record vanished, so let's try again
            self.conn.rollback()
            return self.load()
        msgs = c.fetchall()
        self.conn.commit()
        return self.transfer(msgs)

    def transfer(self, msgs):
        if not isinstance(msgs, list):
            msgs = [msgs]
        if len(msgs) == 0:
            return []
        objects = []
        for _, proj, spider, job, start, end in msgs:
            obj = self.transfer_tuples(**{
                "project": proj,
                "spider": spider,
                "job": job,
                "start_time": start,
                "end_time": end
            })
            objects.append(obj)
        return objects

    def delete(self, n):
        # 删除历史数据
        n = -n if n > 0 else n
        q = "delete from %s where date('now', '%s day') >= date(start_time)" \
            % (self.table, n)
        self.conn.execute(q)
        self.conn.commit()

    def clear(self):
        self.conn.execute("delete from %s" % self.table)
        self.conn.commit()

    def __len__(self):
        q = "select count(*) from %s" % self.table
        return self.conn.execute(q).fetchone()[0]
