# -*- coding: UTF-8 -*-

import configparser
import os

class IniParser:
    def __init__(self,file):
        cf = configparser.ConfigParser()
        cf.read(os.getcwd() + file, encoding="utf-8")
        try:
            self.db_port = cf.get('db','db_port')
            self.db_user = cf.get('db', 'db_user')
            self.db_host = cf.get('db', 'db_host')
            self.db_pass = cf.get('db', 'db_pass')
            self.db_name = cf.get('db', 'db_name')
            self.db_charset = cf.get('db', 'db_charset')
            self.db_pre = cf.get('db', 'db_pre')
            self.db_mongohost = cf.get('db', 'db_mongohost')
            self.db_mongoport = cf.get('db', 'db_mongoport')
            self.db_mongoname = cf.get('db', 'db_mongoname')
            self.pro_groupid = cf.get('project', 'pro_groupid')
            self.pro_package = cf.get('project', 'pro_package')
            self.pro_author = cf.get('project', 'pro_author')
            self.pro_version = cf.get('project', 'pro_version')
            self.pro_path = cf.get('project', 'pro_path')
            self.pro_arti = cf.get('project', 'pro_arti')
            self.pro_zip = cf.get('project', 'pro_zip')
            self.pro_pversion = cf.get('project', 'pro_pversion')
            self.swa_name = cf.get('swagger', 'swa_name')
            self.swa_powerby = cf.get('swagger', 'swa_powerby')
            self.swa_email = cf.get('swagger', 'swa_email')
            self.swa_version = cf.get('swagger', 'swa_version')
            self.dep_dockerjdk = cf.get('deploy', 'dep_dockerjdk')
            self.dep_dockervol = cf.get('deploy', 'dep_dockervol')
            self.dep_serverport = cf.get('deploy', 'dep_serverport')
            self.dep_servletmaxreqsize = cf.get('deploy', 'dep_servletmaxreqsize')
            self.dep_servletmaxfilesize = cf.get('deploy', 'dep_servletmaxfilesize')

        except configparser.NoOptionError:
            print('不能读取配置文件！')
            os.exit(1)
