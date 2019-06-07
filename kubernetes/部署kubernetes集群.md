[TOC]

# 集群规划

## 服务器规划

|    角色     |   主机名   |     ip     |
| :---------: | :--------: | :--------: |
| master+etcd | st01009vm2 | 10.10.62.2 |
|   worker    | st01009vm3 | 10.10.62.3 |
|   worker    | st01009vm4 | 10.10.62.4 |
|   worker    | st01009vm5 | 10.10.62.5 |



## 软件版本

|    组件    |    版本    |
| :--------: | :--------: |
| kubernetes |   1.13.4   |
|   docker   | 18.03.1-ce |
|    etcd    |   3.3.10   |
|  flanneld  |   0.11.0   |

> kube-proxy使用ipvs模式



# 环境准备

## 添加环境变量

在master和node节点执行如下命令添加环境变量

```bash
echo "PATH=$PATH:/opt/kubernetes/bin" >> /etc/profile
source /etc/profile
echo $PATH
```



## 关闭swap和selinux

在master和node节点执行如下命令关闭swap分区

```bash
swapoff -a
sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab 
sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0
```



## 调整时间

在master和node节点执行如下命令设置时间同步

```bash
imedatectl set-timezone Asia/Shanghai
timedatectl set-local-rtc 0
systemctl restart rsyslog 
systemctl restart crond
```



## 安装依赖包

在master和node节点执行如下命令安装相关依赖

```bash
yum install -y epel-release
yum install -y conntrack ipvsadm ipset jq iptables iptables-services curl sysstat libseccomp
```



在master和node节点关闭firewalld启用iptables并放行内网访问

```bash
systemctl stop firewalld
systemctl disable firewalld
systemctl start iptables
systemctl enable iptables
iptables -P FORWARD ACCEPT
echo "/sbin/iptables -P FORWARD ACCEPT" >> /etc/rc.local
iptables -F
iptables -I INPUT 5 -s 10.10.62.0/24  -j ACCEPT

# 修改 /etc/sysconfig/iptables 在合适位置增加如下规则
-A INPUT -s 10.10.62.0/24  -j ACCEPT
```



## 关闭无用服务

在master和node上执行下面命令关闭无用服务

```bash
systemctl stop dnsmasq && systemctl disable dnsmasq
systemctl stop postfix && systemctl disable postfix
```

> linux 系统开启了 dnsmasq 后，将系统 DNS Server 设置为 127.0.0.1，这会导致 docker 容器无法解析域名，需要关闭



## 加载ipvs模块

在node上执行如下命令加载ipvs模块

```bash
modprobe br_netfilter
modprobe ip_vs
echo "/usr/sbin/modprobe br_netfilter" >> /etc/rc.local
echo "/usr/sbin/modprobe ip_vs" >> /etc/rc.local
```



## 设置系统参数

在node节点设置系统参数

```bash
cat > /etc/sysctl.d/kubernetes.conf <<EOF
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
net.ipv4.ip_forward=1
net.ipv4.tcp_tw_recycle=0
vm.swappiness=0
vm.panic_on_oom=0
fs.inotify.max_user_instances=8192
fs.inotify.max_user_watches=1048576
fs.file-max=52706963
fs.nr_open=52706963
net.ipv6.conf.all.disable_ipv6=1
net.netfilter.nf_conntrack_max=2310720
EOF

sysctl -p /etc/sysctl.d/kubernetes.conf
echo "/sbin/sysctl -p /etc/sysctl.d/kubernetes.conf" >> /etc/rc.local
```



## 创建相关目录

执行如下命令在master上创建相关目录结构

```bash
mkdir -p /opt/kubernetes/{bin,cert/config,conf,etcd,yaml,log}
```



执行如下命令在node上创建相关目录结构

```bash
mkdir -p /opt/kubernetes/{bin,cert,conf,log}
```



## 安装docker

在node节点上执行如下命令安装docker

```bash
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum list docker-ce --showduplicates|sort -r
yum install -y docker-ce-18.03.1.ce-1.el7.centos
mkdir /etc/docker
systemctl enable docker

cat > /etc/docker/daemon.json << EOF
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
    "registry-mirrors": ["https://hub-mirror.c.163.com", "https://docker.mirrors.ustc.edu.cn", "https://registry.docker-cn.com"],
    "max-concurrent-downloads": 20,
    "live-restore": true,
    "max-concurrent-uploads": 10
}
EOF
```



## 安装cfssl

在master节点安装证书生成攻击cfssl

```bash
wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
mv cfssl_linux-amd64 /usr/local/bin/cfssl
wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
mv cfssljson_linux-amd64 /usr/local/bin/cfssljson
wget https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
mv cfssl-certinfo_linux-amd64 /usr/local/bin/cfssl-certinfo
chmod +x /usr/local/bin/cfssl*
```



# 创建证书

