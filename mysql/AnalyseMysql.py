# -*- coding: utf-8 -*-

import pymysql.cursors
import json
import re


class AnalyseMysql:
    def __init__(self, iniParser, socketio, **params):
        self.host = iniParser.db_host
        self.user = iniParser.db_user
        self.password = iniParser.db_pass
        self.port = iniParser.db_port
        self.db = iniParser.db_name
        self.charset = iniParser.db_charset
        self.prefix = iniParser.db_pre
        self.package = iniParser.pro_package
        self.socketio = socketio
        self.params = params

    # 得到数据库信息
    def getMysqlInfo(self):
        try:
            connection = pymysql.connect(host=self.host,
                                         user=self.user,
                                         password=self.password,
                                         db=self.db,
                                         charset=self.charset,
                                         port=int(self.port))
            with connection.cursor() as cursor:
                sql = "SHOW TABLES"
                count = cursor.execute(sql)
                # print(count)

                result = cursor.fetchall()
                # print(result)
                column = ''
                columnKey = ''
                columnNullable = ''
                columnDefault = ''
                columnAutoincrease = ''
                columnComment = ''
                tableComment = ''
                tableForeign = ''

                resultJson = '['
                for i in result:
                    if self.params.get("permission") == "true":
                        if i[0][0:3] == self.prefix or i[0][0:3] == "us_":
                            resultJson = self.getInfoMysql(cursor, i, resultJson)
                    else:
                        if i[0][0:3] == self.prefix:
                            resultJson = self.getInfoMysql(cursor, i, resultJson)
                return resultJson[0:-1] + ']'
                # print(resultJson[0:-1] + ']')

        finally:
            connection.close()

    def getInfoMysql(self, cursor, i, resultJson):
        # cursor.execute('show create table `%s`;'%i[0])
        # ret=cursor.fetchall()
        # print(json.dumps(ret,ensure_ascii=False))
        cursor.execute('desc `%s`' % i[0])
        ret = cursor.fetchall()
        # print(json.dumps(ret,ensure_ascii=False))
        # 制作columns
        s = '{'
        for x in ret:
            s = s + '\n\t\t\"' + x[0] + '\":\"' + x[1] + '\",'
        s = s[0:-1] + '\n\t}'
        s = re.sub(r'varchar\([0-9,]*\)', 'String', s)
        s = re.sub(r'int\([0-9,]*\)', 'Integer', s)
        s = re.sub(r'bigInteger', 'Long', s)  # 承接上一步int处理
        s = re.sub('date', 'Date', s)
        s = re.sub('Datetime', 'Date', s)  # 承接上一步date处理
        s = re.sub(r'double\([0-9,]+\)', 'Double', s)
        s = re.sub(r'text', 'String', s)
        # s = json.loads(s)
        # print(s)
        # print(type(s))
        column = s
        # 制作columns可空限制
        s = '{'
        for x in ret:
            s = s + '\n\t\t\"' + x[0] + '\":\"' + x[2] + '\",'
        s = s[0:-1] + '\n\t}'
        s = s.replace("YES", "nullable = true")
        s = s.replace("NO", "nullable = false")
        # s = json.loads(s)
        # print(s)
        # print(type(s))
        columnNullable = s
        # 制作columns 键值
        s = '{'
        for x in ret:
            s = s + '\n\t\t\"' + x[0] + '\":\"' + x[3] + '\",'
        s = s[0:-1] + '\n\t}'
        s = s.replace("PRI", "@Id")
        s = s.replace("MUL", "")
        # s=json.loads(s)
        # print(s)
        # print(type(s))
        columnKey = s
        # 制作columns默认值
        s = '{'
        for x in ret:
            if x[4] is None:
                s = s + '\n\t\t\"' + x[0] + '\":\"' + 'null' + '\",'
            else:
                s = s + '\"' + x[0] + '\":\"' + x[4] + '\",'
        s = s[0:-1] + '\n\t}'
        # s = json.loads(s)
        # print(s)
        # print(type(s))
        columnDefault = s
        # 制作columns自增长
        s = '{'
        for x in ret:
            s = s + '\n\t\t\"' + x[0] + '\":\"' + x[5] + '\",'
        s = s[0:-1] + '\n\t}'
        s = s.replace("auto_increment", "@GeneratedValue(strategy = GenerationType.IDENTITY)")
        # s = json.loads(s)
        # print(s)
        # print(type(s))
        columnAutoincrease = s
        # 遍历出表字段的comment
        cursor.execute('show create table `%s`;' % i[0])
        ret2 = cursor.fetchall()
        # print(ret2[0][1])
        createInfo = ret2[0][1]
        s = '{'
        for x in ret:
            comment = re.findall(x[0] + r"[`0-9A-Za-z  ()_]+'(.+)'", createInfo)
            if len(comment) >= 1:
                s = s + '\n\t\t\"' + x[0] + '\":\"' + comment[0] + '\",'
            else:
                s = s + '\"' + x[0] + '\":\"''\",'
        if s != '{':
            s = s[0:-1] + '\n\t}'
        else:
            s = '{}'
        columnComment = s
        # 得到表标注
        reResult = re.findall(r"COMMENT='([^()（）]+)[()（）A-Za-z0-9]*'", createInfo)
        if len(reResult) >= 1:
            tableComment = '\"' + reResult[0] + '\"'
        else:
            tableComment = '\"\"'
        # 得到外键
        s = '['
        reResult = re.findall(r"CONSTRAINT `.+` FOREIGN KEY \(`(.+)`\) REFERENCES `(.+)` \(`(.+)`\)",
                              createInfo)
        if len(reResult) >= 1:
            for x in reResult:
                s = s + '\n\t\t\t{\n\t\t\t\t"foreign_key\": \"' + x[
                    0] + '\",\n\t\t\t\t"foreign_table\": \"' + x[
                        1] + '\",\n\t\t\t\t"foreign_table_id\": \"' + x[2] + '\"\n\t\t\t},'
        if s != '[':
            tableForeign = s[0:-1] + '\n\t]'
        else:
            tableForeign = '\"\"'
        tmp1 = json.loads(columnKey)
        id = list(tmp1.keys())[list(tmp1.values()).index('@Id')]
        jsonstr = '''
    {
        "table": "%s",
        "class": "%s",
        "type": "mysql_jpa",
        "package": "%s",
        "id": "%s",
        "column": %s,
        "columnKey": %s,
        "columnNullable": %s,
        "columnDefault": %s,
        "columnAutoincrease": %s,
        "columnComment": %s,
        "tableComment": %s,
        "tableForeign": %s
    } 
                        ''' % (i[0], i[0].title(), self.package, id,
                               column, columnKey, columnNullable, columnDefault, columnAutoincrease, columnComment,
                               tableComment, tableForeign)
        # print(jsonstr)
        resultJson = resultJson + jsonstr + ','
        return resultJson

    # 执行sql文件
    def execsql(self, sqlfile):
        try:
            db = pymysql.connect(host=self.host,
                                 user=self.user,
                                 password=self.password,
                                 db=self.db,
                                 charset=self.charset,
                                 port=int(self.port))
            c = db.cursor()
            with open(sqlfile, encoding='utf-8', mode='r') as f:
                # 读取整个sql文件，以分号切割。[:-1]删除最后一个元素，也就是空字符串
                sql_list = f.read().split(';')[:-1]
                for x in sql_list:
                    # 判断包含空行的
                    if '\n' in x:
                        # 替换空行为1个空格
                        x = x.replace('\n', ' ')

                    # 判断多个空格时
                    if '    ' in x:
                        # 替换为空
                        x = x.replace('    ', '')

                    # sql语句添加分号结尾
                    sql_item = x + ';'
                    # print(sql_item)
                    c.execute(sql_item)
                    self.socketio.emit('server_response', {'data': '\n ' + "执行成功sql: %s" % sql_item})
        except Exception as e:
            print(e)
            self.socketio.emit('server_response', {'data': '\n ' + '执行失败sql: %s' % sql_item})
        finally:
            # 关闭mysql连接
            c.close()
            db.commit()
            db.close()

    # 插入权限记录
    def insertPermission(self, common, title):
        try:
            db = pymysql.connect(host=self.host,
                                 user=self.user,
                                 password=self.password,
                                 db=self.db,
                                 charset=self.charset,
                                 port=int(self.port))
            c = db.cursor()
            # 插入第一级权限
            result, sql_item = self.excuSqlItem(c, common, "0", title + "Controller", "", "1")
            # 插入第二级权限
            result, sql_item = self.excuSqlItem(c, common, str(result), title + "Controller", "", "2")
            # 插入第三级权限
            thirdNum = result
            result, sql_item = self.excuSqlItem(c, common + '获得全部记录', str(thirdNum), title + "Controller", "query", "3")
            result, sql_item = self.excuSqlItem(c, common + '获得分页记录标准形式', str(thirdNum), title + "Controller", "page",
                                                "3")
            result, sql_item = self.excuSqlItem(c, common + '获得单个记录', str(thirdNum), title + "Controller", "getInfo",
                                                "3")
            result, sql_item = self.excuSqlItem(c, common + '获得单个空记录', str(thirdNum), title + "Controller", "newEntity",
                                                "3")
            result, sql_item = self.excuSqlItem(c, common + '创建记录json', str(thirdNum), title + "Controller",
                                                "create_json", "3")
            result, sql_item = self.excuSqlItem(c, common + '创建记录', str(thirdNum), title + "Controller", "create", "3")
            result, sql_item = self.excuSqlItem(c, common + '更新记录json', str(thirdNum), title + "Controller",
                                                "update_json", "3")
            result, sql_item = self.excuSqlItem(c, common + '更新记录', str(thirdNum), title + "Controller", "update", "3")
            result, sql_item = self.excuSqlItem(c, common + '删除记录', str(thirdNum), title + "Controller", "delete", "3")

        except Exception as e:
            print(e)
            self.socketio.emit('server_response', {'data': '\n ' + '执行失败sql: %s' % sql_item})
        finally:
            # 关闭mysql连接
            c.close()
            db.commit()
            db.close()

    def excuSqlItem(self, c, tableName, psid, psc, psa, pslevel):
        sql_item = "INSERT INTO `us_permission` (psname,pspid,psc,psa,pslevel) VALUES ('%s','%s','%s','%s','%s')" % (
            tableName, psid, psc, psa, pslevel)
        self.socketio.emit('server_response', {'data': '\n ' + sql_item})
        c.execute(sql_item)
        self.socketio.emit('server_response', {'data': '\n ' + '执行成功sql: %s' % sql_item})
        sql_item = "SELECT LAST_INSERT_ID();"
        c.execute(sql_item)
        self.socketio.emit('server_response', {'data': '\n ' + '执行成功sql: %s' % sql_item})
        result = c.fetchall()
        return result[0][0], sql_item

    # 插入文件权限记录
    def insertFile(self):
        try:
            db = pymysql.connect(host=self.host,
                                 user=self.user,
                                 password=self.password,
                                 db=self.db,
                                 charset=self.charset,
                                 port=int(self.port))
            c = db.cursor()
            # 插入第一级权限
            result, sql_item = self.excuSqlItem(c, "文件操作", "0", "FileController", "", "1")
            # 插入第二级权限
            result, sql_item = self.excuSqlItem(c, "文件操作", str(result), "FileController", "", "2")
            # 插入第三级权限
            thirdNum = result
            result, sql_item = self.excuSqlItem(c, '文件操作获得全部文件列表', str(thirdNum), "FileController", "list", "3")
            result, sql_item = self.excuSqlItem(c, '文件操作预览一个文件', str(thirdNum), "FileController", "serveFileOnline",
                                                "3")
            result, sql_item = self.excuSqlItem(c, '根据id下载文件', str(thirdNum), "FileController", "downloadFileById",
                                                "3")
            result, sql_item = self.excuSqlItem(c, '上传文件', str(thirdNum), "FileController", "serveFileOnline",
                                                "3")
            result, sql_item = self.excuSqlItem(c, '删除一个文件', str(thirdNum), "FileController", "deleteFile",
                                                "3")

        except Exception as e:
            print(e)
            self.socketio.emit('server_response', {'data': '\n ' + '执行失败sql: %s' % sql_item})
        finally:
            # 关闭mysql连接
            c.close()
            db.commit()
            db.close()

    # 插入单记录查找记录
    def insertFindItem(self, controllerName, common, methodName, isString):
        try:
            db = pymysql.connect(host=self.host,
                                 user=self.user,
                                 password=self.password,
                                 db=self.db,
                                 charset=self.charset,
                                 port=int(self.port))
            c = db.cursor()
            # 插入第一级权限
            result, sql_item = self.querySqlItem(c, controllerName + 'Controller')
            # 插入第二级权限
            id=result
            if isString:
                result, sql_item = self.excuSqlItem(c, '根据' + common + '获取记录', str(id),
                                                    controllerName + 'Controller', 'findBy' + methodName, "3")
                result, sql_item = self.excuSqlItem(c, '根据' + common + '模糊查询获取记录', str(id),
                                                    controllerName + 'Controller', 'findBy' + methodName+'Like', "3")
            else:
                result, sql_item = self.excuSqlItem(c, '根据' + common + '获取记录', str(id),
                                                    controllerName + 'Controller', 'findBy' + methodName, "3")

        except Exception as e:
            print(e)
            self.socketio.emit('server_response', {'data': '\n ' + '执行失败sql: %s' % sql_item})
        finally:
            # 关闭mysql连接
            c.close()
            db.commit()
            db.close()

    def querySqlItem(self, c, controllerName):
        sql_item = "SELECT id from us_permission where psc='%s' and pslevel=2" % controllerName
        self.socketio.emit('server_response', {'data': '\n ' + sql_item})
        c.execute(sql_item)
        self.socketio.emit('server_response', {'data': '\n ' + '执行成功sql: %s' % sql_item})
        result = c.fetchall()
        return result[0][0], sql_item
