# RPM方式安装mysql5.7

> 实验环境为centos7

首先检查是否存在旧的mysql：

```bash
$ rpm -qa | grep -i mysql
```



如果存在就需要卸载：

```bash
$ rpm -ev [旧的mysql包名]
```



下载mysql5.7官方prm包

```bash
$ wget https://dev.mysql.com/get/Downloads/MySQL-5.7/mysql-5.7.26-1.el7.x86_64.rpm-bundle.tar
```



然后解压，可以看到解压出如下的一些安装包：

```bash
$ tar xvf mysql-5.7.26-1.el7.x86_64.rpm-bundle.tar 
mysql-community-embedded-devel-5.7.26-1.el7.x86_64.rpm
mysql-community-libs-5.7.26-1.el7.x86_64.rpm
mysql-community-embedded-5.7.26-1.el7.x86_64.rpm
mysql-community-test-5.7.26-1.el7.x86_64.rpm
mysql-community-embedded-compat-5.7.26-1.el7.x86_64.rpm
mysql-community-common-5.7.26-1.el7.x86_64.rpm
mysql-community-devel-5.7.26-1.el7.x86_64.rpm
mysql-community-client-5.7.26-1.el7.x86_64.rpm
mysql-community-server-5.7.26-1.el7.x86_64.rpm
mysql-community-libs-compat-5.7.26-1.el7.x86_64.rpm
```

- mysql-community-client：客户端的安装包；
- mysql-community-server：服务端的安装包；
- mysql-community-devel：包含开发库文件的安装包；
- mysql-community-test：包含测试的安装包；
- mysql-community-embedded：嵌入式mysql安装包；



一般情况下，只需要安装client和server安装包即可，当然其也会依赖其他库的安装包：

```bash
$ rpm -ivh mysql-community-common-5.7.26-1.el7.x86_64.rpm
$ rpm -ivh mysql-community-libs*
$ rpm -ivh mysql-community-client-5.7.26-1.el7.x86_64.rpm
$ rpm -ivh mysql-community-devel-5.7.26-1.el7.x86_64.rpm
$ yum install -y perl libaio libaio-devel numactl net-tools
$ rpm -ivh mysql-community-server-5.7.26-1.el7.x86_64.rpm
```



启动mysql服务

```bash
$ systemctl start mysqld.service
```



查看mysql日志，找到类似下面的这一行：

```bash
$ cat /var/log/mysql.log
[Note] A temporary password is generated for root@localhost: <wqB!ebdk6b4
```

> mysql第一次运行的时候会初始化一个root用户并设置一个随机密码，这一行可以找到这个密码



可以通过下面的命令修改root密码并删除测试数据库和匿名用户

```bash
# 设置root用户密码
$ mysqladmin -u root -p'<wqB!ebdk6b4' password Root123?
# 删除测试数据库和匿名用户
$ mysql_secure_installation
```

> mysql密码需要符合一定的密码规则，否则设置会失败



下面就可以连接mysql了：

```bash
$ mysql -uroot -pRoot123?
```





# 源码方式安装mysql5.7

