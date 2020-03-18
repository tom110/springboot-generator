# -*- coding: utf-8 -*-

import pymysql.cursors
import json
import re


class AnalyseMysql:
    def __init__(self, iniParser):
        self.host = iniParser.db_host
        self.user = iniParser.db_user
        self.password = iniParser.db_pass
        self.port = iniParser.db_port
        self.db = iniParser.db_name
        self.charset = iniParser.db_charset
        self.prefix = iniParser.db_pre
        self.package = iniParser.pro_package

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
                    if i[0][0:3] == self.prefix:
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
                return resultJson[0:-1] + ']'
                # print(resultJson[0:-1] + ']')

        finally:
            connection.close()
