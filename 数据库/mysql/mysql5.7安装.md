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

首先下载mysql5.7源码包：

```bash
$ wget https://dev.mysql.com/get/Downloads/MySQL-5.7/mysql-boost-5.7.26.tar.gz
```



安装依赖包：

```bash
$ yum install -y make gcc gcc-c++ cmake bison-devel ncurses ncurses-devel
```



创建安装目录和数据目录，安装目录一般放在 `/usr/local/` 下，数据目录使用单独的磁盘：

```bash
$ mkdir /usr/local/mysql
$ mkdir -p /data/3306/data
$ mkdir -p /data/3306/binlog
```



安装boost库：

> 从mysql5.7开始，boost库是必须依赖的

```bash
$ mkdir /usr/local/boost
$ cd /usr/local/boost
$ wget http://www.sourceforge.net/projects/boost/files/boost/1.59.0/boost_1_59_0.tar.gz
$ tar zxf boost_1_59_0.tar.gz
```



编译源码：

```bash
$ tar zxf mysql-boost-5.7.26.tar.gz
$ cd mysql-5.7.26/
$ cmake \
-DCMAKE_INSTALL_PREFIX=/usr/local/mysql \   
-DMYSQL_DATADIR=/data/3306/data \
-DSYSCONFDIR=/data/3306 \
-DWITH_MYISAM_STORAGE_ENGINE=1 \
-DWITH_INNOBASE_STORAGE_ENGINE=1 \
-DWITH_MEMORY_STORAGE_ENGINE=1 \
-DWITH_READLINE=1 \
-DMYSQL_UNIX_ADDR=/data/3306/mysql.sock \
-DMYSQL_TCP_PORT=3306 \
-DENABLED_LOCAL_INFILE=1 \
-DWITH_PARTITION_STORAGE_ENGINE=1 \
-DEXTRA_CHARSETS=all \
-DDEFAULT_CHARSET=utf8mb4 \
-DDEFAULT_COLLATION=utf8mb4_general_ci \
-DWITH_BOOST=/usr/local/boost
```

- `DCMAKE_INSTALL_PREFIX` ：安装的根目录；
- `DMYSQL_DATADIR`：数据目录；
- `DSYSCONFDIR`：配置文件目录；
- `DWITH_MYISAM_STORAGE_ENGINE=1`：编译myisam存储引擎，默认的存储引擎，不加也可以；
- `DWITH_INNOBASE_STORAGE_ENGINE=1`：支持InnoDB存储引擎，这个也是默认安装的；
- `DWITH_MEMORY_STORAGE_ENGINE=1`： 持MEMORY引擎；
- `DWITH_READLINE=1`：使用readline功能；
- `DMYSQL_UNIX_ADDR`：sock文件存放目录；
- `DMYSQL_TCP_PORT=3306` ：数据库端口；
- `DENABLED_LOCAL_INFILE=1`：可以使用load data infile命令从本地导入文件；
- `DWITH_PARTITION_STORAGE_ENGINE=1`： 安装数据库分区；
- `DEXTRA_CHARSETS=all`： 支持所有字符集；
- `DDEFAULT_CHARSET=utf8mb4`：默认字符集；
- `DDEFAULT_COLLATION=utf8mb4_general_ci` ：默认效验字符集排序规则，要和`DDEFAULT_CHARSET`一起用；
- `DWITH_BOOST=/usr/local/boost`：指定boost库位置，从5.7.5开始Boost库是必需的；



编译成功后进行安装：

```bash
$ make && make install
$ make clean
```



添加mysql用户：

```bash
$ groupadd mysql
$ useradd -g mysql mysql
$ chown -R mysql:mysql /usr/local/mysql
$ chown -R mysql:mysql /data/3306
```



初始化mysql：

```bash
$ cd /usr/local/mysql
$ ./bin/mysqld --initialize --user=mysql --basedir=/usr/local/mysql --datadir=/data/3306/data/ 
```



观察初始化输出，找到类似于如下的一行：

```
2019-06-29T11:32:37.238756Z 1 [Note] A temporary password is generated for root@localhost: &leFGSPpM4sC
```

这个是初始化设置的mysql默认root密码，需要暂时记住。



设置环境变量：

```bash
$ echo "export PATH=$PATH:/usr/local/mysql/bin" >> /etc/profile
$ source /etc/profile
```



设置mysql启动文件：

```bash
$ cd /usr/local/mysql/support-files
$ cp mysql.server /etc/init.d/mysqld
$ chmod 755 /etc/init.d/mysqld
```



修改mysql启动脚本，设置数据目录和根目录：

```bash
$ vim /etc/init.d/mysqld

// 修改下面的项目指定根目录
basedir=/usr/local/mysql/
datadir=/data/3306/data/
```



修改配置文件：

```bash
$ vim /etc/my.cnf

// 修改为如下的形式
[mysqld]
basedir=/usr/local/mysql
datadir=/data/3306/data/
socket=/data/3306/mysql.sock
user=mysql
tmpdir=/data/3306/
# Disabling symbolic-links is recommended to prevent assorted security risks
symbolic-links=0
# Settings user and group are ignored when systemd is used.
# If you need to run mysqld under a different user or group,
# customize your systemd unit file for mariadb according to the
# instructions in http://fedoraproject.org/wiki/Systemd

[mysqld_safe]
log-error=/data/3306/data/error.log
pid-file=/data/3306/data/mysql.pid

#
# include all files from the config directory
#
!includedir /etc/my.cnf.d
```



启动mysql：

```bash
$ service mysqld start 
$ netstat -ntlp | grep mysqld
tcp6       0      0 :::3306                 :::*                    LISTEN      18471/mysqld        
```



现在就可以使用前面获取到的默认密码登录数据库了，不过也可以使用下面的命令来重新设置密码及删除匿名用户和库：

```bash
# 设置root用户密码
$ mysqladmin -u root -p'&leFGSPpM4sC' password Root123?
# 删除测试数据库和匿名用户
$ mysql_secure_installation
$ mysql -uroot -pRoot123?
```

