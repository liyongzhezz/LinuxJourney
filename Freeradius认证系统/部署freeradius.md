# 源码部署freeradius

## 下载最新的源码包

freeradius源码包可以在 http://freeradius.org/releases/ 找到。这里我使用的是3.0.19版本：

```bash
wget ftp://ftp.freeradius.org/pub/freeradius/freeradius-server-3.0.19.tar.gz -P /usr/local/src
cd /usr/local/src
tar zxf freeradius-server-3.0.19.tar.gz
```



## 安装依赖

执行下面的命令安装相关依赖包：

```bash
yum install –y wget gcc gcc-c++ make libtalloc libtalloc-devel openssl openssl-devel
```



如果需要连接mysql，则还需要安装如下依赖包：

```bash
yum install -y mysql-devel freeradius-mysql
```



## 编译安装

```bash
cd freeradius-server-3.0.19
./configure --prefix=/usr/local/freeadius --with-logdir=/usr/local/freeadius/log/
make 
make install 
```



## 开放防火墙端口

udp 1812是授权认证端口，udp 1813是计费端口

```bash
iptables -A INPUT -p udp --dport 1812 -j ACCEPT
iptables -A INPUT -p udp --dport 1813 -j ACCEPT
```



## 启动并测试

将相关命令所在目录添加到环境变量：

```bash
echo "PATH=$PATH:/usr/local/freeadius/bin:/usr/local/freeadius/sbin" > /etc/profile
source /etc/profile
```



编辑下面的文件，创建一个测试用例：

```bash
vim /usr/local/freeadius/etc/raddb/mods-config/files/authorize
// 在第一行添加如下内容
test Cleartext-Password := "password"
```



执行下面的命令以debug模式启动radius server：

```bash
radiusd -X
```



向radius server发送一个请求，如果radius server正常，则应该会收到一个响应：

```bash
radtest test password localhost 0 testing123

Sent Access-Request Id 148 from 0.0.0.0:26233 to 127.0.0.1:1812 length 74
	User-Name = "test"
	User-Password = "password"
	NAS-IP-Address = 10.10.62.6
	NAS-Port = 0
	Message-Authenticator = 0x00
	Cleartext-Password = "password"
Received Access-Accept Id 148 from 127.0.0.1:1812 to 127.0.0.1:26233 length 20
```

> 看到服务端响应 Access-Accept 说明认证成功



# yum方式安装

## 安装镜像源

执行下面的命令安装epel镜像源

```bash
yum install -y epel-release
```



## 安装依赖

执行下面的命令安装相关依赖：

```bash
yum install –y wget gcc gcc-c++ make libtalloc libtalloc-devel openssl openssl-devel freeradius-utils 
```



如果需要连接mysql，则还需要安装如下依赖包：

```bash
yum install -y mysql-devel freeradius-mysql
```



## 安装freeradius server端

执行下面的命令安装freeradius server端服务：

```bash
yum install -y freeradius 
```



## 开放防火墙端口

udp 1812是授权认证端口，udp 1813是计费端口

```bash
iptables -A INPUT -p udp --dport 1812 -j ACCEPT
iptables -A INPUT -p udp --dport 1813 -j ACCEPT
```



## 测试

通过yum安装后，freeradius的相关配置文件位于/etc/raddb下。freeradius包含一个默认客户端localhost，这个客户端可以帮助排查问题和测试。

 

首先编辑clients.conf文件，确保文件包含如下的内容：

```bash
client localhost {
    ipaddr = 127.0.0.1
    secret = testing123
    require_message_authenticator = no
    nastype = other
}
```

> 这些morning已经有了，其实不用修改。



然后编辑user文件，在顶部添加如下内容创建一个测试用户alice，并确保第2和3行以一个tab键开头：

```bash
"alice" Cleartext-Password := "passme"
    Framed-IP-Address = 192.168.1.65,
    Reply-Message = "Hello, %{User-Name}"
```



启动debug模式：

```bash
radiusd -X
```

> 当出现Ready to process requests时表示debug模式启动成功。



然后执行下面的命令发送测试请求：

```bash
radtest alice passme 127.0.0.1 100 testing123

Sent Access-Request Id 194 from 0.0.0.0:13061 to 127.0.0.1:1812 length 75
	User-Name = "alice"
	User-Password = "passme"
	NAS-IP-Address = 10.10.46.9
	NAS-Port = 100
	Message-Authenticator = 0x00
	Cleartext-Password = "passme"
Received Access-Accept Id 194 from 127.0.0.1:1812 to 0.0.0.0:0 length 40
	Framed-IP-Address = 192.168.1.65
	Reply-Message = "Hello, alice"
```

> 显示上边的内容表示成功





# 配置freeradius

## 配置文件

freeradius服务器配置被划分为不同的文件，其中主配置文件为radiusd.conf，其包含各种子配置文件；clients.conf用来定义到freeradius服务器的客户端。

 

**在一个NAS可以使用FreeRADIUS服务器之前, 他必须被定义为在FreeRADIUS服务器上的一个客户端.** 



## **客户端定义**

### sections

一个客户端通过一个client section定义，freeradius通过section来定义和分组，一个section以一个关键字开始表示section名称，然后跟一个大括号，在括号内可以有许多配置指定到这个section，section可以被嵌套。

 

例如：

```bash
client localhost {
    ....
}
```



### 客户端标识

freeradius通过ip地址标识一个客户端，如果一个不知道的客户端发起请求则这个请求会被忽略。

 

### 共享秘钥（shared secret）

客户端和服务器端也需要有一个共享的密钥，将会用来加密和解密某些AVPs。User-Password AVP的值使用这个共享密钥加密。当共享密钥在客户端和服务器端不同时， FreeRADIUS服务器将会检测到他并且当运行的debug模式时警告你。

 ```
Failed to authenticate the user.

​    WARNING: Unprintable characters in the password. Double-check the shared secret on the serve

 
 ```



### Message-Authenticator

当定义一个客户端你可以强制在所有请求中出现Message-Authenticator AVP.。由于我们将会使用radtest程序没有包含他，所以对于localhost禁用他，通过设置require_message_authenticator为no。

 


# 关联mysql

## 安装mysql并设置密码

```bash
yum install -y mariadb mariadb-server

systemctl enable mariadb

systemctl start mariadb
```



设置密码：

```mysql
MariaDB [(none)]> set password for 'root'@'localhost' = password('test');
```



## 创建数据库

首先创建radius数据库：

```mysql
mysql -uroot -ptest

MariaDB [(none)]> create database radius character set utf8 collate utf8_general_ci;
MariaDB [(none)]> grant all on radius.* to radius@localhost identified by 'radius33630976';
MariaDB [(none)]> flush privileges;
```



## 导入freeradius的sql文件

```bash
cd /etc/raddb/mods-config/sql/main/mysql

mysql -uradius -pradiustest radius < schema.sql

mysql -uroot -ptest

MariaDB [(none)]> use radius;

MariaDB [radius]> show tables;

+------------------+

| Tables_in_radius |

+------------------+

| nas              |

| radacct          |

| radcheck         |

| radgroupcheck    |

| radgroupreply    |

| radpostauth      |

| radreply         |

| radusergroup     |

+------------------+
```



其中，每个表的功能如下：

- radcheck：用户检查信息表；
- radreply：用户回复信息表；
- radgroupcheck：用户组检查信息表；
- radgroupreply：用户组回复信息表；
- radusergroup：用户和组的关系表；
- radacct：计费情况表；
- radpostauth：认证后处理信息，可以包括认证请求成功和拒绝的记录；

 

## 加入组信息

这里组名为user

```mysql
MariaDB [(none)]> use radius;

MariaDB [radius]> insert into radgroupreply (groupname,attribute,op,value) values ('user','Auth-Type',':=','Local');

MariaDB [radius]> insert into radgroupreply (groupname,attribute,op,value) values ('user','Service-Type','=','Framed-User');

MariaDB [radius]> insert into radgroupreply (groupname,attribute,op,value) values ('user','Framed-IP-Netmask',':=','255.255.255.0');

MariaDB [radius]> select * from radgroupreply;

+----+-----------+-------------------+----+---------------+

| id | groupname | attribute         | op | value         |

+----+-----------+-------------------+----+---------------+

|  1 | user      | Auth-Type         | := | Local         |

|  2 | user      | Service-Type      | =  | Framed-User   |

|  3 | user      | Framed-IP-Netmask | := | 255.255.255.0 |

+----+-----------+-------------------+----+---------------+

# 插入用户信息

MariaDB [radius]> insert into radcheck(id,username,attribute,op,value) values('2','test','Cleartext-Password',':=','test123');

MariaDB [radius]> select * from radcheck;

+----+----------+--------------------+----+---------+

| id | username | attribute          | op | value   |

+----+----------+--------------------+----+---------+

|  2 | test     | Cleartext-Password | := | test123 |

+----+----------+--------------------+----+---------+

# 用户加入组

MariaDB [radius]> insert into radusergroup(username,groupname) values('test','user');

MariaDB [radius]> select * from radusergroup;

+----------+-----------+----------+

| username | groupname | priority |

+----------+-----------+----------+

| test     | user      |        1 |

+----------+-----------+----------+

 
```



## 配置freeradius和mysql关联

```bash
cd /etc/raddb/mods-available

# 编辑sql文件

vim sql

driver = "rlm_sql_mysql"  # 将31行的driver = "rlm_sql_null"替换为driver = "rlm_sql_mysql"

# 打开下面的注释（大概在92行），并修改mysql地址、端口、用户和密码

dialect = "mysql"

server = "localhost"

port = 3306

login = "radius"

password = "radiustest"

radius_db = "radius"
```



给mods-enabled文件夹和mods-available文件夹下的sql文件做个软链接

```bash
cd /etc/raddb/mods-enabled

ln -s /etc/raddb/mods-available/sql ./
```

 

修改sites-enable目录下的default文件

```bash
cd /etc/raddb/sites-enabled

vim default

# 分别将authorize {}、accounting{}下的sql去掉注释，并且将file注释掉。
```



## 测试

打开调试模式

```bash
radiusd -X
```



然后在另一终端输入下面格式的命令：`radtest [user] [passwd] [主机] [nas port] [secret]`

```bash
radtest test test123 localhost 1812 testing123


Sent Access-Request Id 240 from 0.0.0.0:26642 to 127.0.0.1:1812 length 74

​	User-Name = "test"

​	User-Password = "test123"

​	NAS-IP-Address = 10.10.46.9

​	NAS-Port = 1812

​	Message-Authenticator = 0x00

​	Cleartext-Password = "test123"

Received Access-Accept Id 240 from 127.0.0.1:1812 to 0.0.0.0:0 length 32

​	Service-Type = Framed-User

​	Framed-IP-Netmask = 255.255.255.0
```

**secret这里是testing123为默认值，设置在clients.conf中**

