# -*- coding: UTF-8 -*-

import wget
import zipfile
import os
import shutil

class ShellExe:
    def __init__(self,iniParser):
        self.iniParser = iniParser
        self.data_url="https://start.spring.io/starter.zip?type=maven-project&language=java&bootVersion=2.3.0.M3&" \
                      "baseDir=%s&groupId=%s&artifactId=%s&name=%s&description=description&" \
                      "packageName=%s.%s&packaging=jar&javaVersion=1.8&dependencies=web"\
                      %(self.iniParser.pro_arti,
                        self.iniParser.pro_groupid,
                        self.iniParser.pro_arti,
                        self.iniParser.pro_arti,
                        self.iniParser.pro_groupid,
                        self.iniParser.pro_arti)

        print(self.data_url)
        out_fname = self.iniParser.pro_path  + 'start_spring_io.zip'
        wget.download(self.data_url, out=out_fname)
        ShellExe.un_zip(out_fname)
        os.remove(out_fname)

    @staticmethod
    def un_zip(file_name):
        """unzip zip file"""
        zip_file = zipfile.ZipFile(file_name)
        if os.path.isdir(file_name + "_files"):
            try:
                shutil.rmtree(file_name + "_files")
            except:
                pass
            if os.path.exists(file_name + "_files"):
                os.rmdir(file_name + "_files")
            os.mkdir(file_name + "_files")
        else:
            os.mkdir(file_name + "_files")
        for names in zip_file.namelist():
            zip_file.extract(names,file_name + "_files/")
        zip_file.close()


# shellExe=ShellExe()
# shellExe.getPath()



