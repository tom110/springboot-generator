/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

DROP TABLE IF EXISTS `us_manager`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `us_manager` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `mgname` varchar(32) NOT NULL COMMENT '名称',
  `mgpwd` varchar(64) NOT NULL COMMENT '密码',
  `mgtime` date DEFAULT NULL COMMENT '注册时间',
  `roleid` int(11) NOT NULL DEFAULT '0' COMMENT '角色id',
  `mgmobile` varchar(32) DEFAULT NULL COMMENT '电话',
  `mgmail` varchar(64) DEFAULT NULL COMMENT '邮箱',
  `mg_state` int(2) DEFAULT '1' COMMENT '1：表示启用 0:表示禁用',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=520 DEFAULT CHARSET=utf8 COMMENT='管理员表';
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `us_manager` WRITE;
/*!40000 ALTER TABLE `us_manager` DISABLE KEYS */;
INSERT INTO `us_manager` VALUES (518,'tom','7C4A8D09CA3762AF61E59520943DC26494F8941B','2020-03-25',40,'15098928330','tom@qq.com',1),(519,'admin','7C4A8D09CA3762AF61E59520943DC26494F8941B','2020-03-30',30,'15098928330','admin@qq.com',1);
/*!40000 ALTER TABLE `us_manager` ENABLE KEYS */;
UNLOCK TABLES;

DROP TABLE IF EXISTS `us_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `us_role` (
  `id` int(6) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `rolename` varchar(20) NOT NULL COMMENT '角色名称',
  `psids` varchar(512) NOT NULL DEFAULT '' COMMENT '权限ids,1,2,5',
  `psca` text COMMENT '控制器-操作,控制器-操作,控制器-操作',
  `roledesc` text COMMENT '角色描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8 COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `us_role` WRITE;
/*!40000 ALTER TABLE `us_role` DISABLE KEYS */;
INSERT INTO `us_role` VALUES (30,'主管','161,145,125,110','Goods-index,Goods-tianjia,Category-index,Order-showlist,Brand-index','技术负责人'),(40,'biggeodata','103,111,163,167,168,170,171,112,161,169,125,110,160,162,164,165,166',NULL,'biggeodata项目使用');
/*!40000 ALTER TABLE `us_role` ENABLE KEYS */;
UNLOCK TABLES;

DROP TABLE IF EXISTS `us_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `us_permission` (
  `id` int(6) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `psname` varchar(20) NOT NULL COMMENT '权限名称',
  `pspid` int(6) NOT NULL COMMENT '父id',
  `psc` varchar(32) NOT NULL DEFAULT '' COMMENT '控制器',
  `psa` varchar(32) NOT NULL DEFAULT '' COMMENT '操作方法',
  `pslevel` int(1) NOT NULL DEFAULT '0' COMMENT '权限等级',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=172 DEFAULT CHARSET=utf8 COMMENT='权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `us_permission` WRITE;
/*!40000 ALTER TABLE `us_permission` DISABLE KEYS */;
INSERT INTO `us_permission` VALUES (103,'权限管理',0,'','',1),(110,'用户列表',125,'Manager','index',3),(111,'角色列表',103,'Role','index',3),(112,'权限列表',103,'Permission','index',3),(125,'用户管理',0,'','',1),(145,'数据统计',0,'','',1),(160,'得到所有用户',110,'vertifyController','getUsers',3),(161,'获取menus',110,'vertifyController','getMenus',3),(162,'设置用户状态',110,'vertifyController','changeUserState',3),(163,'得到所有角色',111,'vertifyController','getRoles',3),(164,'修改用户角色',110,'vertifyController','saveRoleInfo',3),(165,'创建用户',110,'vertifyController','createUser',3),(166,'修改用户信息',110,'vertifyController','updateUser',3),(167,'修改角色信息',111,'vertifyController','updateRole',3),(168,'创建角色',111,'vertifyController','createRole',3),(169,'得到全部权限信息',112,'vertifyController','getPermissions',3),(170,'为角色附权限',111,'vertifyController','allotPermission',3),(171,'删除角色的权限',111,'vertifyController','removePermissionByRoleid',3);
/*!40000 ALTER TABLE `us_permission` ENABLE KEYS */;
UNLOCK TABLES;

DROP TABLE IF EXISTS `us_permissionapi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `us_permissionapi` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `psid` int(11) NOT NULL COMMENT '权限id',
  `spapiservice` varchar(255) DEFAULT NULL COMMENT 'apiservice',
  `psapiaction` varchar(255) DEFAULT NULL COMMENT 'apiaction',
  `psapipath` varchar(255) DEFAULT NULL COMMENT 'apipath',
  `psapiorder` int(4) DEFAULT NULL COMMENT 'api顺序',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=60 DEFAULT CHARSET=utf8 COMMENT='权限api表';
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `us_permissionapi` WRITE;
/*!40000 ALTER TABLE `us_permissionapi` DISABLE KEYS */;
INSERT INTO `us_permissionapi` VALUES (3,103,NULL,NULL,'rights',2),(10,110,'ManagerService','getAllManagers','users',NULL),(11,111,'RoleService','getAllRoles','roles',NULL),(12,112,'RightService','getAllRights','rights',NULL),(25,125,NULL,NULL,'users',1),(45,145,NULL,NULL,'reports',5);
/*!40000 ALTER TABLE `us_permissionapi` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
