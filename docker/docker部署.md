# 版本选择

我选择的docker-ce版本为18.06，docker在拆分为ce和ee之后，大版本例如18表示发布的年份，小版本表示的是月份。

 

系统选择的是Centos7.4系统。



# 卸载旧版docker

```bash
$ yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-selinux docker-engine-selinux docker-engine
```



# 安装依赖包

```bash
$ yum install -y yum-utils
```



# 添加docker源

```bash
$ yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
```



# 安装docker-ce

查看当前可用的版本：

```bash
$ yum list docker-ce --showduplicates|sort -r
```



安装最新版的docker-ce可以直接执行：

```bash
$ yum install -y docker-ce
```



安装指定版本的docker-ce可以执行：

```bash
$ yum install -y docker-ce-18.03.1.ce-1.el7.centos
```



# 启动docker-ce

```bash
$ systemctl start docker
$ systemctl enable docker
```



# 验证安装

启动完成后执行如下命令查看docker server和client端的版本：

```bash
$ docker version

Client:

 Version:           18.06.1-ce

 API version:       1.38

 Go version:        go1.10.3

 Git commit:        e68fc7a

 Built:             Tue Aug 21 17:23:03 2018

 OS/Arch:           linux/amd64

 Experimental:      false

 

Server:

 Engine:

  Version:          18.06.1-ce

  API version:      1.38 (minimum version 1.12)

  Go version:       go1.10.3

  Git commit:       e68fc7a

  Built:            Tue Aug 21 17:25:29 2018

  OS/Arch:          linux/amd64

  Experimental:     false
```



然后可以运行如下命令，查看docker功能是否正常：

```bash
$ docker run hello-world
# 如果出现Hello from Docker!字样则说明docker正常工作
```





# 卸载docker

首先卸载docker软件包：

```bash
$ yum remove docker-ce
```



然后需要手动删除docker镜像、容器等相关文件：

```bash
$ rm -rf /var/lib/docker
```

