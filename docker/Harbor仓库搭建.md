# 环境规划



## 软件环境

|      软件      |      版本       |
| :------------: | :-------------: |
|     docker     | docker-ce-18.03 |
|     harbor     |  1.5.2-offline  |
| docker-compose |      1.9.0      |



## 硬件规划

两台服务器作为harbor服务器，配置8核16G，一个作为主服务器，另一个作为从服务器（从主服务器同步镜像数据），两个分别挂载1.5T数据盘作为镜像数据存储。





## 初始化配置



## 创建数据目录

```bash
$ mkdir /data
```



## 格式化数据盘并挂载

```bash
$ mkfs.xfs /dev/vdb1
$ echo "/dev/vdb1 /data xfs defaults 0 0" >> /etc/fstab
$ mount -a 
$ df -h | grep /data
/dev/vdb1       1.5T   33M  1.5T   1% /data
```



## 安装epel源

```bash
$ yum install -y epel-release
```





# 安装docker和docker-compose



## 添加docker源

```bash
$ yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
```



## 安装docker

```bash
$ yum install -y docker-ce-18.03.1.ce-1.el7.centos
```



## 创建docker配置文件

```bash
$ mkdir /etc/docker
$ cat > /etc/docker/daemon.json << EOF
{
      "log-driver": "json-file",
      "log-opts": {
              "max-size": "100m",
              "max-file": "5"
      },

      "default-ulimit": ["nofile=102400:102400"],
      "ipv6": false,
      "debug": true,
      "log-level": "debug",

      "selinux-enabled": false,
      "registry-mirrors": ["http://registry.xunlei.cn"]
}
EOF
```



## 启动docker

```bash
$ systemctl start docker
$ systemctl enable docker
$ systemctl status docker
```



## 安装docker-compose

harbor需要docker-compose在1.7.1及以上版本，可以从yum安装，但是需要注意版本。

```bash
$ yum list | grep docker-compose
$ yum install -y docker-compose
```





# 下载并配置harbor



## 下载harbor

```bash
$ mkdir /use/local/harbor1.5.2
$ wget https://storage.googleapis.com/harbor-releases/harbor-offline-installer-v1.5.2.tgz -P /usr/local/harbor1.5.2
$ cd /usr/local/harbor1.5.2
$ tar zxf harbor-offline-installer-v1.5.2.tgz
```



## 配置harbor

harbor配置文件为 `harbor.cfg` ，这里编辑这个文件，设置harbor相关参数：

```bash
$ cd /usr/local/harbor1.5.2/harbor

# 编辑 harbor.cfg文件，根据需要修改下面项目

// harbor管理UI地址
hostname = harbor.example.com

// UI界面协议
ui_url_protocol = https

// 最大复制工作数，默认为3，根据自身网络及机器配置调整
max_job_workers = 3

// 如果使用https协议，则修改这里为自己的证书
ssl_cert = /data/cert/server.crt
ssl_cert_key = /data/cert/server.key

// 用于在复制策略中加密或解密远程注册表的密码的密钥路径
secretkey_path = /data

// 设置邮件服务器和邮箱账户，发送邮件使用
email_server = mail.example.com
email_server_port = 25
email_username = harbor@example.com
email_password = harbor123
email_from = harbor@xunlei.com

// harbor管理员密码
harbor_admin_password = Harbor12345
```



## 编辑docker-compose.yml文件

这里需要修改该文件中 `volumes` 挂载数据卷的位置，默认是将数据存储在本机data目录下，这个刚好满足了当前的情况（data目录挂载的是大磁盘），如果大磁盘挂载在其他目录，则需要修改这里的路径。



配置样例可以参考 statics 下的 docker-compose.yml 文件。



## 安装harbor

harbor已经提供了安装脚本 `install.sh` ，改脚本安装分为4个步骤：

- 加载harbor镜像；
- 准备环境；
- 检查harbor实例；
- 启动harbor；



如果以上4个步骤都没有错误就说明harbor安装成功了，对于修改了harbor配置的情况，也需要运行这个脚本来生效配置。



```bash
$ sh install.sh
```



## 检查启动情况

```bash
$ netstat -ntlp | grep docker-proxy
tcp        0      0 127.0.0.1:1514          0.0.0.0:*               LISTEN      8498/docker-proxy   
tcp        0      0 10.15.0.164:80          0.0.0.0:*               LISTEN      9901/docker-proxy   
tcp        0      0 10.15.0.164:443         0.0.0.0:*               LISTEN      9866/docker-proxy   
tcp        0      0 10.15.0.164:4443        0.0.0.0:*               LISTEN      9809/docker-proxy  

docker ps 
CONTAINER ID        IMAGE                                  COMMAND                  CREATED             STATUS                    PORTS                                                                          NAMES
1fd5462b0933        vmware/harbor-jobservice:v1.5.2        "/harbor/start.sh"       54 seconds ago      Up 50 seconds                                                                                            harbor-jobservice
8627ade5943b        vmware/nginx-photon:v1.5.2             "nginx -g 'daemon of…"   54 seconds ago      Up 41 seconds (healthy)   10.15.0.164:80->80/tcp, 10.15.0.164:443->443/tcp, 10.15.0.164:4443->4443/tcp   nginx
5a3e9fef92a9        vmware/harbor-ui:v1.5.2                "/harbor/start.sh"       55 seconds ago      Up 53 seconds (healthy)                                                                                  harbor-ui
49481d00dae8        vmware/harbor-adminserver:v1.5.2       "/harbor/start.sh"       56 seconds ago      Up 54 seconds (healthy)                                                                                  harbor-adminserver
751bd2b620f1        vmware/registry-photon:v2.6.2-v1.5.2   "/entrypoint.sh serv…"   56 seconds ago      Up 54 seconds (healthy)   5000/tcp                                                                       registry
9e058c908747        vmware/harbor-db:v1.5.2                "/usr/local/bin/dock…"   56 seconds ago      Up 54 seconds (healthy)   3306/tcp                                                                       harbor-db
3125d3428e36        vmware/redis-photon:v1.5.2             "docker-entrypoint.s…"   56 seconds ago      Up 54 seconds             6379/tcp                                                                       redis
e4362a273d57        vmware/harbor-log:v1.5.2               "/bin/sh -c /usr/loc…"   56 seconds ago      Up 55 seconds (healthy)   127.0.0.1:1514->10514/tcp                                                      harbor-log

```





