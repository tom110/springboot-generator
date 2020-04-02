# -*- coding: utf-8 -*-

import pymysql.cursors
import json
import re


def execsql(sqlfile):

    try:
        db = pymysql.connect(host='www.giseden.xyz',
                             user='biggeodata',
                             password='biggeodata!@#123',
                             db='biggeodata',
                             charset='utf8',
                             port=3308)
        c = db.cursor()
        sql_item = "INSERT INTO `us_permission` (psname,pspid,psc,psa,pslevel) VALUES ('test',0,'','',1)"
        c.execute(sql_item)
        sql_item = "SELECT LAST_INSERT_ID();"
        c.execute(sql_item)
        result = c.fetchall()
        print(result[0][0])
        sql_item = "INSERT INTO `us_permission` (psname,pspid,psc,psa,pslevel) VALUES ('test',0,'','',1)"
    except Exception as e:
        print(e)
    finally:
        # 关闭mysql连接
        c.close()
        db.commit()
        db.close()
    pass

execsql("permission.sql")