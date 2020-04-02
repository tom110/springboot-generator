# -*- coding: UTF-8 -*-

import os
import json
import time
import tarfile
from mysql.AnalyseMysql import AnalyseMysql
from flask import Flask, render_template, send_from_directory, request, session
from flask_socketio import SocketIO, emit
from ini.IniParser import IniParser
from shell.ShellExe import ShellExe
from subprocess import Popen, PIPE, STDOUT
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

iniParser = IniParser("/ini/config.ini")
ALLOWED_EXTENSIONS = set(['txt', 'bpmn', 'xml'])
UPLOAD_FOLDER = '.'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ----------------------------------------------------------------------- util相关类
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def lowerFirstWord(s):
    return s[0].lower() + s[1:]


# 设置信息输出
def sys_print(msg):
    print(str(msg))
    socketio.emit('server_response', {'data': '\n ' + str(msg)})


# 通过外键详情得到外键名集合
def getForeigns(foreigns_detail):
    foreigns = []
    for f_d in foreigns_detail:
        foreigns.append(f_d['foreign_key'])
    return foreigns


def getForeignsClassMap(foreigns_detail):
    foreignClassMap = {}
    for f_d in foreigns_detail:
        foreignClassMap[f_d['foreign_key']] = f_d['foreign_table']
    return foreignClassMap


# 把dict的key变为小写
def lowerDictkey(columns):
    newColumns = {}
    for key in columns:
        newKey = key.lower()
        newColumns[newKey] = columns[key]

    return newColumns


# 将首字母转换为小写
def small_str(s):
    if len(s) <= 1:
        return s
    return (s[0:1]).lower() + s[1:]


# 用bat执行mvn转docker镜像
def cmdRun():
    fold_address = iniParser.pro_path + 'start_spring_io.zip_files/' + iniParser.pro_arti
    bat_name = 'mvn2docker.bat'
    os.chdir(fold_address)

    p = Popen("cmd.exe /c" + fold_address + '/' + bat_name, stdout=PIPE, stderr=STDOUT)
    curline = p.stdout.readline()
    while (curline != b''):
        str1 = str(curline)[2:-1].replace("\\r\\n", "\n")
        msg = {'data': str1}
        socketio.emit('server_response', msg)
        sys_print(str)
        curline = p.stdout.readline()

    p.wait()
    sys_print(p.returncode)


# 生成tar.gz压缩包
def make_targz():
    file_name = iniParser.pro_zip
    source_dir = iniParser.pro_path + 'start_spring_io.zip_files/' + iniParser.pro_arti + '/'
    with tarfile.open(file_name, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    return file_name


# 创建java文件
def create_java_file(class_name, package, text, suffix='.java', fileType="java"):
    if fileType == "java":
        dirs = iniParser.pro_path + 'start_spring_io.zip_files/' + iniParser.pro_arti + '/src/main/java/' + package.replace(
            '.', '/') + '/'
    elif fileType == "pom":
        dirs = iniParser.pro_path + 'start_spring_io.zip_files/' + iniParser.pro_arti + '/'
    elif fileType == "docker":
        dirs = iniParser.pro_path + 'start_spring_io.zip_files/' + iniParser.pro_arti + '/src/main/docker/'
    elif fileType == "mvn2docker":
        dirs = iniParser.pro_path + 'start_spring_io.zip_files/' + iniParser.pro_arti + '/'
    elif fileType == "application":
        dirs = iniParser.pro_path + 'start_spring_io.zip_files/' + iniParser.pro_arti + '/src/main/resources/'
        if os.path.exists(dirs + 'application.properties'):
            os.remove(dirs + 'application.properties')
    if not os.path.exists(dirs):
        os.makedirs(dirs, 0o777)
    if os._exists(dirs + class_name + suffix):
        os.remove(dirs + class_name + suffix)
    fd = os.open(dirs + class_name + suffix, os.O_WRONLY | os.O_CREAT)
    os.write(fd, text.encode(encoding="utf-8", errors="strict"))
    os.close(fd)


# 在java文件制定标志添加内容
def insert_java_file(class_name, package, insertText, insertFlag):
    dirs = iniParser.pro_path + 'start_spring_io.zip_files/' + iniParser.pro_arti + '/src/main/java/' + package.replace(
        '.', '/') + '/'
    fd = open(dirs + class_name + '.java', 'r', encoding='utf-8')
    lines = []
    count = 0
    insertLine = 2
    filelines = fd.readlines()
    for line in filelines:
        if line != insertFlag:
            count = count + 1
        else:
            insertLine = count
        lines.append(line)
    fd.close()

    lines.insert(insertLine, insertText)
    s = ''
    for l in lines:
        s = s + l
    fp = open(dirs + class_name + '.java', 'w', encoding='utf8')
    fp.write(s)
    fp.close()


# 更新initparser
def updateInitparser(inis):
    global iniParser
    newFile = "ini/" + str(uuid.uuid1()) + '_ini.ini'
    fd = os.open(newFile, os.O_WRONLY | os.O_CREAT)
    os.write(fd, inis.encode(encoding="utf-8", errors="strict"))
    os.close(fd)
    iniParser = IniParser("/" + newFile)
    os.remove(newFile)


# ----------------------------------------------------------------------- web相关类
@socketio.on('connect_event')
def connected_msg(msg):
    socketio.emit('server_response', {'data': msg['data']})


@app.route('/')
def index():
    # mysql_info= mysql.getMysqlInfo()
    with open(r'ini/config.ini', 'rt', encoding='utf-8') as f:
        data = f.read()
    return render_template('create_class.html', mysql_info='', ini_info=data)


@app.route('/mysql_info')
def mysql_info():
    inis = request.args.get("inis")
    permission = request.args.get("permission")
    updateInitparser(inis)
    # 通过新的ini文件获取数据库信息
    mysql = AnalyseMysql(iniParser, socketio, permission=permission)
    # 执行permission.sql，添加us_manager us_role us_permission us_permissionapi四个表和数据
    if permission == "true":
        mysql.execsql('permission.sql')

    mysql_info = mysql.getMysqlInfo()

    socketio.emit('server_response', {'data': '\n生成数据库信息成功！'})
    return json.dumps(mysql_info, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ':'))


@app.route("/download/<filename>", methods=['GET'])
def downloader(filename):
    # 指定文件下载目录，默认为当前项目根路径
    dirpath = os.path.join(app.root_path, '')
    # as_attachment=True 表示下载
    return send_from_directory(dirpath, filename, as_attachment=True)


@app.route('/createClass', methods=['GET', 'POST'])
def create_class():
    # 初始化项目基本结构
    shellExe = ShellExe(iniParser)
    file_name = msg = None
    tables = request.form['tables']
    ini_info = request.form['inis']
    if len(tables) <= 0:
        sys_print('request data json is null!')
        msg = 'request data json is null!'
    tables = json.loads(tables, encoding='utf-8')
    sys_print('--- 修改application.yml')

    docker = request.form.get('docker')
    files = request.form.get('files')
    configuration = request.form.get('configuration')
    permission = request.form.get("permission")

    # 通过新的ini文件获取数据库信息
    mysql = AnalyseMysql(iniParser, socketio, permission=permission)

    update_applicationyml(docker=docker, files=files)
    if docker and len(docker) >= 1:
        sys_print('--- 创建Dockerfile')
        create_Dockerfile(iniParser, docker=docker)
    sys_print('--- 修改pom.xml')
    update_pom(iniParser, docker=docker, files=files, permission=permission)
    for fields in tables:
        # print(fields)
        j = fields
        class_name = j['class']
        package = j['package']
        db_type = j['type']
        foreigns_detail = j['tableForeign']
        if len(class_name) <= 0:
            sys_print('className is null!')
            msg = 'className is null!'
        if len(package) <= 0:
            sys_print('package is null')
            msg = 'package is null'
        if len(db_type) <= 0:
            sys_print('type is null')
            msg = 'type is null'
        sys_print('类名：' + class_name + '\n' + '包名：' + package)
        if not msg or len(msg) <= 0:
            d = time.strftime("%Y-%m-%d", time.localtime())
            author = iniParser.pro_author
            version = iniParser.pro_version
            entity = request.form.get('entity')
            if entity and len(entity) >= 1:
                sys_print('--- 开始创建Entity类文件')
                create_entity(class_name, package,
                              j['tableComment'], j['id'], j['table'], j['column'], j['columnNullable'],
                              j['columnKey'], j['columnAutoincrease'], j['columnComment'], db_type,
                              d, author, version)
                sys_print('--- 创建Entity类成功')
            repository = request.form.get('repository')
            if repository and len(repository) >= 1:
                sys_print('--- 开始创建repository类文件')
                create_repository(class_name, package, j['id'], j['column'], d, author, version, db_type,
                                  permission=permission)
                sys_print('--- 创建repository类成功')
            service = request.form.get('service')
            if service and len(service) >= 1:
                sys_print('--- 开始创建service类文件')
                create_service(class_name, package, j['id'], j['column'], d, author, version)
                sys_print('--- 创建service类成功')
            controller = request.form.get('controller')
            if controller and len(controller) >= 1:
                sys_print('--- 开始创建controller类文件')
                create_controller(class_name, package, j['tableComment'], j['id'], j['column'], d, author, version,
                                  db_type, permission=permission)
                if permission and len(permission)>0:
                    mysql.insertPermission(j['tableComment'], class_name)
                    sys_print('--- 插入controller基本权限完成')
                sys_print('--- 创建controller类成功')

    msg = None
    for fields in tables:
        j = fields
        class_name = j['class']
        package = j['package']
        db_type = j['type']
        foreigns_detail = j['tableForeign']
        column = j['column']
        columnComment = j['columnComment']
        columnKey = j['columnKey']
        if len(class_name) <= 0:
            msg = 'className is null!'
        if len(package) <= 0:
            msg = 'package is null'
        if len(db_type) <= 0:
            msg = 'type is null'
        if not msg or len(msg) <= 0:
            if entity and len(entity) >= 1:
                sys_print('--- 开始修改Entity类文件外键')
                create_entity_foreign_key(class_name, package, foreigns_detail)
                sys_print('--- 修改Entity类文件外键成功')
                sys_print('--- 开始创建单项查找Repository接口函数')
                # create_repository_findBy_singleValue(class_name, package, column, columnComment, columnKey,
                #                                     foreigns_detail, permission=permission)
                create_repository_findBy_singleValue_page(class_name, package, column, columnComment, columnKey,
                                                          permission=permission, mysql=mysql)
                sys_print('--- 创建单项查找Repository-Controller接口函数成功')

    if configuration and len(configuration) >= 1:
        sys_print('--- 开始创建configuration类文件')
        create_configuration('Swagger', package, iniParser, files=files)
        sys_print('--- 创建configuration类文件成功')

    if files and len(files) >= 1:
        sys_print('--- 开始创建文件存储相关类文件')
        create_files(package, files=files, permission=permission)
        if permission and len(permission) >= 1:
            mysql.insertFile()
        sys_print('--- 创建文件存储相关类文件成功')

    if permission and len(permission) >= 1:
        sys_print('--- 开始创建权限模块相关类文件')
        create_permission(package, permission=permission)
        sys_print('--- 创建权限模块相关文件成功')

    file_name = make_targz()

    if docker and len(docker) >= 1:
        sys_print('--- 生成docker镜像开始，mvn启动')
        cmdRun()  # 生成docker image

    tables = json.dumps(tables, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ':'))
    return file_name


@app.route('/createFlowableClass', methods=['GET', 'POST'])
def create_flowable_class():
    flowableInis = request.form['flowableInis']
    files = request.files.getlist('bpmns')

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return "success"


# ----------------------------------------------------------------------- 具体操作函数
# 替换application.yml
def update_applicationyml(**params):
    c = {'iniParser': iniParser, 'params': params}
    s = render_template('application_yml_templates.html', **c)
    create_java_file('application', '', s, ".yml", "application")


# 创建Dockerfile
def create_Dockerfile(iniParser, **params):
    c = {'iniParser': iniParser, 'params': params}
    s = render_template('docker_templates.html', **c)
    create_java_file('Dockerfile', '', s, "", "docker")
    s = render_template('create_docker_mvn_templates.html', **c)
    create_java_file('mvn2docker', '', s, '.bat', 'mvn2docker')


# 替换pom.xml文件
def update_pom(iniParser, **params):
    c = {'iniParser': iniParser, 'params': params}
    s = render_template('pom_templates.html', **c)
    create_java_file('pom', '', s, ".xml", "pom")


# 创建entity
def create_entity(class_name, package, tableComment, id, table_name, columns_raw, columnsNullable, columnKey,
                  columnAutoincrease, columnComment, db_type, date, author, version):
    columns = lowerDictkey(columns_raw)
    propertys = ''
    methods = ''
    if columns:
        for key in columns_raw.keys():
            propertys += '\t@ApiModelProperty("%s")\n\tprivate %s %s;' % (
                columnComment[key],
                columns_raw[key],
                lowerFirstWord(key.title().replace('_', '')) + '\n')
            p0 = ''
            key_lower = key.lower()
            if id == key:
                if db_type == 'mysql_jpa':
                    p0 += '\n\t%s\n\t%s' % (columnKey[key], columnAutoincrease[key])
                elif db_type == 'mongodb':
                    p0 += '\n\t%s' % (columnKey[key])
            if db_type == 'mysql_jpa':
                p0 += '\n\t@Column(name = \"%s\",%s)' % (key, columnsNullable[key])
            elif db_type == 'mongodb' and key != id:
                p0 += '\n\t@Field(\"%s\")' % (key)
            p1 = '\tpublic %s get%s() {\n\t\treturn this.%s;\n\t}' % (
                columns_raw[key],
                key_lower.title().replace('_', ''),
                lowerFirstWord(key_lower.title().replace('_', '')))
            p2 = '\tpublic void set%s(%s %s) {\n\t\tthis.%s = %s;\n\t}' % (
                key_lower.title().replace('_', ''),
                columns_raw[key],
                lowerFirstWord(key_lower.title().replace('_', '')),
                lowerFirstWord(key_lower.title().replace('_', '')),
                lowerFirstWord(key_lower.title().replace('_', ''))
            )
            methods += p0 + '\n' + p1 + '\n' + p2
    c = {'package': package + '.entity',
         'entity_package': package + '.entity.' + class_name,
         'class_name': class_name,
         'table_name': table_name,
         'propertys': propertys,
         'methods': methods,
         'table_comment': tableComment,
         'date': date, 'author': author, 'version': version}
    if db_type == 'mongodb':
        s = render_template('entity_mongodb_templates.html', **c)
        create_java_file(class_name, package + '.entity', s)
    elif db_type == 'mysql':
        s = render_template('entity_mysql_templates.html', **c)
        create_java_file(class_name, package + '.entity', s)
        s = render_template('entity_mysql_mapper_templates.html', **c)
        create_java_file(class_name, package + '.entity', s, 'Mapper.xml')
    elif db_type == 'mysql_jpa':
        s = render_template('entity_mysql_jpa_templates.html', **c)
        create_java_file(class_name, package + '.entity', s)


# 创建entity外键
def create_entity_foreign_key(class_name, package, foreigns_detail):
    # 根据外键信息为类添加外键集合
    for foreigns_info in foreigns_detail:
        s = '''
\tprivate Set<%s> %ss=new HashSet<%s>();
\t@OneToMany(cascade = CascadeType.ALL,fetch = FetchType.LAZY)
\t@JoinColumn(name = "%s")
\tpublic Set<%s> get%ss() {
\t	return %ss;
\t}
\tpublic void set%ss(Set<%s> %ss) {
\t	this.%ss = %ss;
\t}
    ''' % (class_name,
           class_name.lower(),
           class_name,
           foreigns_info['foreign_key'].lower(),
           class_name,
           class_name,
           class_name.lower(),
           class_name,
           class_name,
           class_name.lower(),
           class_name.lower(),
           class_name.lower())
        insert_java_file(foreigns_info['foreign_table'].title(), package + '.entity', '\n' + s + '\n', '    //外键位置\n')


# 创建repository-controller单值查询函数（外键根据主表查询）
def create_repository_findBy_singleValue(class_name, package, columns, columnComment, columnKey, foreigns_detail,
                                         **params):
    foreigns = getForeigns(foreigns_detail)
    foreignClassMap = getForeignsClassMap(foreigns_detail)
    # 根据column元素添加接口函数
    for key in columns.keys():
        if columnKey[key] != '@Id':
            if key not in foreigns:
                s = '''
\t//根据%s查找对象
\tList<%s> findBy%s(%s %s);
                ''' % (
                    columnComment[key],
                    class_name,
                    key.title().replace('_', ''),
                    columns[key],
                    key.title()
                )
                insert_java_file(class_name.title() + 'Repository', package + '.repository', '\n' + s + '\n',
                                 '    //按单项查找\n')

                s = '''
\t@ApiOperation(value = "根据%s获取记录", notes = "根据%s获取记录", httpMethod = "GET", produces = MediaType.APPLICATION_JSON_VALUE)
\t@GetMapping("/findBy%s/{%s}")
\tpublic List<%s> findBy%s(@PathVariable %s %s){
\t	return %sRepository.findBy%s(%s);
\t}
                ''' % (
                    columnComment[key],
                    columnComment[key],
                    key.title(),
                    key.lower(),
                    class_name,
                    key.title(),
                    columns[key],
                    key.lower(),
                    class_name.lower(),
                    key.title().replace('_', ''),
                    key.lower()
                )
                insert_java_file(class_name.title() + 'Controller', package + '.controller', '\n' + s + '\n',
                                 '    //按单项查找\n')
            else:
                s = '''
import %s.service.%sService;
                ''' % (
                    package, foreignClassMap[key].title()
                )
                insert_java_file(class_name.title() + 'Controller', package + '.controller', '\n' + s + '\n',
                                 '//import可选\n')
                if params.get("permission") and len(params.get("permission")) >= 1:
                    s = '''
\t@Autowired
\tprivate %sService %sService;
\t@ApiOperation(value = "根据%s获取记录", notes = "根据%s获取记录", httpMethod = "GET", produces = MediaType.APPLICATION_JSON_VALUE)
\t@GetMapping("/findBy%s/{%s}")
\t@CheckToken
\tpublic Set<%s> findBy%s(@PathVariable %s %s){
\t	return %sService.getById(%s).get%ss();
\t}
                                ''' % (
                        foreignClassMap[key].title(),
                        foreignClassMap[key],
                        columnComment[key],
                        columnComment[key],
                        key.title(),
                        key.lower(),
                        class_name,
                        key.title(),
                        columns[key],
                        key.lower(),
                        foreignClassMap[key],
                        key.lower(),
                        class_name
                    )
                else:
                    s = '''
\t@Autowired
\tprivate %sService %sService;
\t@ApiOperation(value = "根据%s获取记录", notes = "根据%s获取记录", httpMethod = "GET", produces = MediaType.APPLICATION_JSON_VALUE)
\t@GetMapping("/findBy%s/{%s}")
\tpublic Set<%s> findBy%s(@PathVariable %s %s){
\t	return %sService.getById(%s).get%ss();
\t}
                                                    ''' % (
                        foreignClassMap[key].title(),
                        foreignClassMap[key],
                        columnComment[key],
                        columnComment[key],
                        key.title(),
                        key.lower(),
                        class_name,
                        key.title(),
                        columns[key],
                        key.lower(),
                        foreignClassMap[key],
                        key.lower(),
                        class_name
                    )
                insert_java_file(class_name.title() + 'Controller', package + '.controller', '\n' + s + '\n',
                                 '    //按单项查找\n')


# 创建repository-controller单值查询函数并排序
def create_repository_findBy_singleValue_page(class_name, package, columns, columnComment, columnKey, **params):
    # 根据column元素添加接口函数
    for key in columns.keys():
        if columnKey[key] != '@Id':
            s = '''
\t//根据%s查找对象
\tList<%s> findBy%s(%s %s,Pageable pageable);
             ''' % (
                columnComment[key],
                class_name,
                key.title().replace('_', ''),
                columns[key],
                key.title()
            )
            if columns[key] == "String":
                s = s + '''
\t//根据%s查找对象
\tList<%s> findBy%sLike(%s %s,Pageable pageable);
                ''' % (
                    columnComment[key],
                    class_name,
                    key.title().replace('_', ''),
                    columns[key],
                    key.title()
                )
            insert_java_file(class_name.title() + 'Repository', package + '.repository', '\n' + s + '\n',
                             '    //按单项查找\n')

            if params.get("permission") and len(params.get("permission")) >= 1:
                s = '''
\t@ApiImplicitParams({
\t			@ApiImplicitParam(name = "page", dataType = "integer", paramType = "query",
\t					value = "您想获取的页数 (0..N)"),
\t			@ApiImplicitParam(name = "size", dataType = "integer", paramType = "query",
\t					value = "每页的记录数."),
\t			@ApiImplicitParam(name = "sort", allowMultiple = true, dataType = "string", paramType = "query",
\t					value = "严格排序格式: property(,asc|desc). " +
\t							"默认排序是asc. " )
\t})
\t@ApiOperation(value = "根据%s获取记录", notes = "根据%s获取记录", httpMethod = "GET", produces = MediaType.APPLICATION_JSON_VALUE)
\t@GetMapping("/findBy%s/{%s}")
\t@CheckToken
\tpublic List<%s> findBy%s(@PathVariable %s %s,@PageableDefault(page = 0,size=10,sort = {"id"},direction = Sort.Direction.ASC) Pageable pageable){
\t	return %sRepository.findBy%s(%s,pageable);
\t}
                    ''' % (
                    columnComment[key],
                    columnComment[key],
                    key.title(),
                    key.lower(),
                    class_name,
                    key.title(),
                    columns[key],
                    key.lower(),
                    class_name.lower(),
                    key.title().replace('_', ''),
                    key.lower()
                )
                if columns[key] == "String":
                    s = s + '''
\t@ApiImplicitParams({
\t			@ApiImplicitParam(name = "page", dataType = "integer", paramType = "query",
\t					value = "您想获取的页数 (0..N)"),
\t			@ApiImplicitParam(name = "size", dataType = "integer", paramType = "query",
\t					value = "每页的记录数."),
\t			@ApiImplicitParam(name = "sort", allowMultiple = true, dataType = "string", paramType = "query",
\t					value = "严格排序格式: property(,asc|desc). " +
\t							"默认排序是asc. " )
\t})
\t@ApiOperation(value = "根据%s获取记录", notes = "根据%s获取记录", httpMethod = "GET", produces = MediaType.APPLICATION_JSON_VALUE)
\t@GetMapping("/findBy%sLike/{%s}")
\t@CheckToken
\tpublic List<%s> findBy%sLike(@PathVariable %s %s,@PageableDefault(page = 0,size=10,sort = {"id"},direction = Sort.Direction.ASC) Pageable pageable){
\t	return %sRepository.findBy%sLike(%s,pageable);
\t}
                        ''' % (
                        columnComment[key],
                        columnComment[key],
                        key.title(),
                        key.lower(),
                        class_name,
                        key.title(),
                        columns[key],
                        key.lower(),
                        class_name.lower(),
                        key.title().replace('_', ''),
                        key.lower()
                    )
            else:
                s = '''
\t@ApiImplicitParams({
\t			@ApiImplicitParam(name = "page", dataType = "integer", paramType = "query",
\t					value = "您想获取的页数 (0..N)"),
\t			@ApiImplicitParam(name = "size", dataType = "integer", paramType = "query",
\t					value = "每页的记录数."),
\t			@ApiImplicitParam(name = "sort", allowMultiple = true, dataType = "string", paramType = "query",
\t					value = "严格排序格式: property(,asc|desc). " +
\t							"默认排序是asc. " )
\t})
\t@ApiOperation(value = "根据%s获取记录", notes = "根据%s获取记录", httpMethod = "GET", produces = MediaType.APPLICATION_JSON_VALUE)
\t@GetMapping("/findBy%s/{%s}")
\tpublic List<%s> findBy%s(@PathVariable %s %s,@PageableDefault(page = 0,size=10,sort = {"id"},direction = Sort.Direction.ASC) Pageable pageable){
\t	return %sRepository.findBy%s(%s,pageable);
\t}
                                    ''' % (
                    columnComment[key],
                    columnComment[key],
                    key.title(),
                    key.lower(),
                    class_name,
                    key.title(),
                    columns[key],
                    key.lower(),
                    class_name.lower(),
                    key.title().replace('_', ''),
                    key.lower()
                )
                if columns[key] == "String":
                    s = s + '''
\t@ApiImplicitParams({
\t			@ApiImplicitParam(name = "page", dataType = "integer", paramType = "query",
\t					value = "您想获取的页数 (0..N)"),
\t			@ApiImplicitParam(name = "size", dataType = "integer", paramType = "query",
\t					value = "每页的记录数."),
\t			@ApiImplicitParam(name = "sort", allowMultiple = true, dataType = "string", paramType = "query",
\t					value = "严格排序格式: property(,asc|desc). " +
\t							"默认排序是asc. " )
\t})
\t@ApiOperation(value = "根据%s获取记录", notes = "根据%s获取记录", httpMethod = "GET", produces = MediaType.APPLICATION_JSON_VALUE)
\t@GetMapping("/findBy%sLike/{%s}")
\tpublic List<%s> findBy%sLike(@PathVariable %s %s,@PageableDefault(page = 0,size=10,sort = {"id"},direction = Sort.Direction.ASC) Pageable pageable){
\t	return %sRepository.findBy%sLike(%s,pageable);
\t}
                                        ''' % (
                        columnComment[key],
                        columnComment[key],
                        key.title(),
                        key.lower(),
                        class_name,
                        key.title(),
                        columns[key],
                        key.lower(),
                        class_name.lower(),
                        key.title().replace('_', ''),
                        key.lower()
                    )

            insert_java_file(class_name.title() + 'Controller', package + '.controller', '\n' + s + '\n',
                             '    //按单项查找\n')
            if params.get("permission") and len(params.get("permission")) >= 1:
                if columns[key] == "String":
                    params.get("mysql").insertFindItem(class_name.title(),
                                                       columnComment[key],
                                                       key.title(), True)
                else:
                    params.get("mysql").insertFindItem(class_name.title(),
                                                       columnComment[key],
                                                       key.title(), False)


# 创建Repository
def create_repository(class_name, package, id, columns, date, author, version, db_type, **params):
    c = {'repository_package': package + '.repository',
         'package': package,
         'class_name': class_name,
         'entity_package': package + '.entity.' + class_name,
         'date': date,
         'id': id.lower(),
         'id_type': columns[id], 'author': author, 'version': version, 'params': params}
    if db_type == 'mysql_jpa':
        s = render_template('repository_jpa_templates.html', **c)
    elif db_type == 'mongodb':
        s = render_template('repository_mongodb_templates.html', **c)
    create_java_file(class_name + 'Repository', package + '.repository', s)


# 创建Service
def create_service(class_name, package, id, columns, date, author, version):
    # 创建CRUD接口
    c = {'package': package + '.service.common', 'date': date, 'author': author, 'version': version}
    s = render_template('service_common_jpa_templates.html', **c)
    create_java_file('CRUDService', package + '.service.common', s)
    # 创建service接口
    c = {'service_package': package + '.service',
         'package': package,
         'class_name': class_name,
         'small_class_name': small_str(class_name),
         'entity_package': package + '.entity.' + class_name,
         'date': date, 'id': id.lower(), 'id_type': columns[id], 'author': author, 'version': version}
    s = render_template('service_jpa_templates.html', **c)
    create_java_file(class_name + 'Service', package + '.service', s)
    # 创建实现
    c = {'impl_package': package + '.service.impl',
         'package': package,
         'class_name': class_name,
         'id': id.lower(),
         'id_type': columns[id],
         'class_name_lower': class_name.lower(), 'author': author, 'version': version}
    s = render_template('service_impl_jpa_templates.html', **c)
    create_java_file(class_name + 'ServiceImpl', package + '.service.impl', s)


# 创建controller
def create_controller(class_name, package, tableComment, id, columns, date, author, version, db_type, **params):
    c = {'package': package,
         'table_comment': tableComment,
         'class_name': class_name, 'id_title': id.lower().title(), 'id': id.lower(), 'id_type': columns[id],
         'class_name_lower': class_name.lower(), 'date': date, 'author': author, 'version': version, 'params': params}
    s = ''
    if db_type == 'mysql_jpa':
        s = render_template('controller_jpa_templates.html', **c)
    elif db_type == 'mongodb':
        s = render_template('controller_mongodb_templates.html', **c)
    create_java_file(class_name + 'Controller', package + '.controller', s)


# 创建configration类
def create_configuration(class_name, package, iniParser, **params):
    c = {'package': package, 'iniParser': iniParser, 'params': params}
    s = render_template('swagger_templates.html', **c)
    create_java_file(class_name + 'Configuration', package + '.configuration', s)
    c = {'package': package}
    s = render_template('convert_configration_templates.html', **c)
    create_java_file('ConvertConfiguration', package + '.configuration', s)


# 创建files相关类
def create_files(package, **params):
    # 写entity里的两个类
    c = {'package': package, 'params': params}
    s = render_template('files_FileDocument_templates.html', **c)
    create_java_file('FileDocument', package + '.entity', s)
    s = render_template('files_ResponseModel_templates.html', **c)
    create_java_file('ResponseModel', package + '.entity', s)
    # 写controller的FileController类
    s = render_template('files_FileController_templates.html', **c)
    create_java_file('FileController', package + '.controller', s)
    # 写工具类的FileContentTypeUtils
    s = render_template('files_FileContentTypeUtils_templates.html', **c)
    create_java_file('FileContentTypeUtils', package + '.util', s)
    # 写service类
    s = render_template('files_IFileService_templates.html', **c)
    create_java_file('IFileService', package + '.service', s)
    s = render_template('files_FileServiceImpl_templates.html', **c)
    create_java_file('FileServiceImpl', package + '.service.impl', s)


# 创建权限相关类
def create_permission(package, **params):
    # 写annotation里的两个类
    c = {'package': package, 'params': params}
    s = render_template('permission_annotation_checkout_template.html', **c)
    create_java_file('CheckToken', package + '.annotation', s)
    s = render_template('permission_annotation_login_template.html', **c)
    create_java_file('LoginToken', package + '.annotation', s)
    # 写configuration里的配置类
    c = {'package': package}
    s = render_template('permission_configuration_template.html', **c)
    create_java_file('InterceptorConfiguration', package + '.configuration', s)
    # 写interceptor里的权限拦截类
    c = {'package': package}
    s = render_template('permission_interceptor_template.html', **c)
    create_java_file('AuthenticationInterceptor', package + '.interceptor', s)
    # 写service类
    s = render_template('permission_service_vertify_template.html', **c)
    create_java_file('VertifyService', package + '.service', s)
    s = render_template('permission_serviceImpl_vertify_template.html', **c)
    create_java_file('VertifyServiceImpl', package + '.service.impl', s)
    # 写工具util类
    s = render_template('permission_util_jwt_template.html', **c)
    create_java_file('JwtUtil', package + '.util', s)
    # 写controller类
    s = render_template('permission_controller_vertify_template.html', **c)
    create_java_file('VertifyController', package + '.controller', s)
    # 修改Us_permissionRepository类
    s = '''
\t@Query(value = "SELECT p FROM Us_Permission p WHERE p.id in (:permissionids)")
\tList<Us_Permission> findInIds(@Param("permissionids") List<Integer> ids);

\t@Query(value = "SELECT p FROM Us_Permission p WHERE p.psc=:psc AND p.psa=:psa")
\tList<Us_Permission> findInIdBySM(@Param("psc") String psc,@Param("psa") String psa);
    '''
    insert_java_file('Us_PermissionRepository', package + '.repository', '\n' + s + '\n',
                     '    //按单项查找\n')


# ********************************************************************* 具体操作函数


if __name__ == '__main__':
    app.run()
    socketio.run(app, host='0.0.0.0')
