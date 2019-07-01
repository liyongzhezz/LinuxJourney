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
mkdir /var/lib/docker
```

在node节点，给docker数据目录挂载一个数据盘，推荐使用SSD（我用的是700Gssd），这里对数据盘的分区和格式化过程就略过了
```bash
echo "/dev/vdb1    /var/lib/container/     ext4    defaults        0 0" >> /etc/fstab
echo "/var/lib/container/docker /var/lib/docker none defaults,bind 0 0" >> /etc/fstab
echo "/var/lib/container/kubelet /var/lib/kubelet none defaults,bind 0 0" >> /etc/fstab
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

证书统一在master上创建后，分发到各node节点



## 创建CA证书

在master上执行如下命令创建创建ca证书

```bash
cat > /opt/kubernetes/cert/config/ca-config.json <<EOF
{
  "signing": {
    "default": {
      "expiry": "87600h"
    },
    "profiles": {
      "kubernetes": {
         "expiry": "87600h",
         "usages": [
            "signing",
            "key encipherment",
            "server auth",
            "client auth"
        ]
      }
    }
  }
}
EOF
```

- signing：表示该证书可以用于签名其他证书；
- server auth：表示client可以用该证书对server提供的证书进行验证；
- client auth：表示server可以用该证书对client提供的证书进行验证；



```bash
cat > /opt/kubernetes/cert/config/ca-csr.json <<EOF
{
    "CN": "kubernetes",
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "L": "ShenZhen",
            "ST": "GuangZhou",
            "O": "k8s",
            "OU": "System"
        }
    ]
}
EOF

cfssl gencert -initca /opt/kubernetes/cert/config/ca-csr.json | cfssljson -bare /opt/kubernetes/cert/ca
```

- CN：从证书中提取该字段作为请求的用户名，浏览器使用该字段验证网站是否合法；
- O：从证书中提取该字段作为请求的用户组；
- kube-apiserver将提取的User、Group作为RBAC授权的用户标识；



## 生成节点server证书

```bash
cat > /opt/kubernetes/cert/config/server-csr.json <<EOF
{
    "CN": "kubernetes",
    "hosts": [
      "127.0.0.1",
      "${HOST-IP}",
      "172.24.0.1",
      "kubernetes",
      "kubernetes.default",
      "kubernetes.default.svc",
      "kubernetes.default.svc.cluster",
      "kubernetes.default.svc.cluster.local"
    ],
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "L": "ShenZhen",
            "ST": "GuangZhou",
            "O": "k8s",
            "OU": "System"

        }
    ]
}
EOF

cfssl gencert -ca=/opt/kubernetes/cert/ca.pem -ca-key=/opt/kubernetes/cert/ca-key.pem -config=/opt/kubernetes/cert/config/ca-config.json -profile=kubernetes /opt/kubernetes/cert/config/server-csr.json | cfssljson -bare /opt/kubernetes/cert/${HOSTNAME}
```

- HOST-IP变量应该被替换为所有master节点的ip；
- 172.24.0.1是server-ip段的第一个ip；
- 如果前端使用了vip做apiserver的负载均衡，vip也需要加入；
- 域名最后字符不能是 ```.``` (如不能为 `kubernetes.default.svc.cluster.local.`)，否则解析时失败，提示： `x509: cannot parse dnsName "kubernetes.default.svc.cluster.local."`；
- 如果使用非 `cluster.local `域名，如 `test.com`，则需要修改域名列表中的最后两个域名为：`kubernetes.default.svc.test`、`kubernetes.default.svc.test.com`；
- 为每一个节点生成后将server证书和ca公钥证书发送到节点对应目录下；



## 生成admin证书

admin证书是用于kubectl工具和apiserver通信使用

```bash
cat > /opt/kubernetes/cert/config/admin-csr.json <<EOF
{
  "CN": "admin",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
       "C": "CN",
       "L": "ShenZhen",
       "ST": "GuangZhou",
       "O": "k8s",
       "OU": "System"
    }
  ]
}
EOF

cfssl gencert -ca=/opt/kubernetes/cert/ca.pem -ca-key=/opt/kubernetes/cert/ca-key.pem -config=/opt/kubernetes/cert/config/ca-config.json -profile=kubernetes /opt/kubernetes/cert/config/admin-csr.json | cfssljson -bare /opt/kubernetes/cert/admin
```



## 生成kube-proxy证书

```bash
cat > /opt/kubernetes/cert/config/kube-proxy-csr.json <<EOF
{
  "CN": "system:kube-proxy",
  "hosts": [],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
       "C": "CN",
       "L": "ShenZhen",
       "ST": "GuangZhou",
       "O": "k8s",
       "OU": "System"
    }
  ]
}
EOF

cfssl gencert -ca=/opt/kubernetes/cert/ca.pem -ca-key=/opt/kubernetes/cert/ca-key.pem -config=/opt/kubernetes/cert/config/ca-config.json -profile=kubernetes /opt/kubernetes/cert/config/kube-proxy-csr.json | cfssljson -bare /opt/kubernetes/cert/kube-proxy
```

- 生成kkube-proxy证书后将其发送到node节点，供kube-proxy使用；



## 生成bootstrap-token

```bash
BOOTSTRAP_TOKEN=$(head -c 16 /dev/urandom | od -An -t x | tr -d ' ')
cat > /opt/kubernetes/cert/token.csv <<EOF
${BOOTSTRAP_TOKEN},kubelet-bootstrap,10001,"system:kubelet-bootstrap"
EOF
```



## 生成kubelet bootstrap kubeconfig文件

```bash
KUBE_APISERVER="https://10.10.62.2:6443"

# 设置集群参数
kubectl config set-cluster kubernetes --certificate-authority=/opt/kubernetes/cert/ca.pem --embed-certs=true --server=${KUBE_APISERVER} --kubeconfig=/opt/kubernetes/cert/bootstrap.kubeconfig
# 设置客户端认证参数
kubectl config set-credentials kubelet-bootstrap --token=${BOOTSTRAP_TOKEN} --kubeconfig=/opt/kubernetes/cert/bootstrap.kubeconfig
# 设置上下文参数
kubectl config set-context default --cluster=kubernetes --user=kubelet-bootstrap --kubeconfig=/opt/kubernetes/cert/bootstrap.kubeconfig
# 设置默认上下文
kubectl config use-context default --kubeconfig=/opt/kubernetes/cert/bootstrap.kubeconfig
```

- 这里需要安装kubectl命令，可以参照后面内容先安装kubectl二进制文件；
- 生成好后将文件发送到node节点；



## 创建kube-proxy kubeconfig文件

```bash
kubectl config set-cluster kubernetes --certificate-authority=/opt/kubernetes/cert/ca.pem --embed-certs=true --server=${KUBE_APISERVER} --kubeconfig=/opt/kubernetes/cert/kube-proxy.kubeconfig
kubectl config set-credentials kube-proxy --client-certificate=/opt/kubernetes/cert/kube-proxy.pem --client-key=/opt/kubernetes/cert/kube-proxy-key.pem --embed-certs=true --kubeconfig=/opt/kubernetes/cert/kube-proxy.kubeconfig
kubectl config set-context default --cluster=kubernetes --user=kube-proxy --kubeconfig=/opt/kubernetes/cert/kube-proxy.kubeconfig
kubectl config use-context default --kubeconfig=/opt/kubernetes/cert/kube-proxy.kubeconfig
```



# 部署etcd

在规划的etcd节点进行部署，这里我的etcd节点和master复用一台。



## 下载etcd

```bash
wget https://github.com/etcd-io/etcd/releases/download/v3.3.10/etcd-v3.3.10-linux-amd64.tar.gz -P /usr/local/src
cd /usr/local/src
tar zxf etcd-v3.3.10-linux-amd64.tar.gz
mv etcd-v3.3.10-linux-amd64/etcd* /opt/kubernetes/bin/
```



## 创建etcd配置文件

```bash
ETCD_NODE_NAME="etcd01"
ETCD_NODE_IP=10.10.62.2

cat > /opt/kubernetes/conf/etcd << EOF
#[Member]
ETCD_NAME="${ETCD_NODE_NAME}"
ETCD_DATA_DIR="/opt/kubernetes/etcd/default.etcd"
ETCD_LISTEN_PEER_URLS="https://${ETCD_NODE_IP}:2380"
ETCD_LISTEN_CLIENT_URLS="https://${ETCD_NODE_IP}:2379"

#[Clustering]
ETCD_INITIAL_ADVERTISE_PEER_URLS="https://${ETCD_NODE_IP}:2380"
ETCD_ADVERTISE_CLIENT_URLS="https://${ETCD_NODE_IP}:2379"
ETCD_INITIAL_CLUSTER="etcd01=https://${ETCD_NODE_IP}:2380"
ETCD_INITIAL_CLUSTER_TOKEN="etcd-cluster"
ETCD_INITIAL_CLUSTER_STATE="new"
EOF
```

- 注意修改前面的etcd相关变量；
- 如果有多个etcd节点，各节点的 ETCD_NODE_NAME 应该不一样；
- 如果有多个etcd节点，ETCD_INITIAL_CLUSTER 应该加上所有的节点；
- 如果有多个etcd节点，每个etcd配置文件中ETCD_INITIAL_CLUSTER 的顺序要一致；



## 创建etcd.service文件

```bash
cat > /usr/lib/systemd/system/etcd.service << EOF
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
EnvironmentFile=-/opt/kubernetes/conf/etcd
ExecStart=/opt/kubernetes/bin/etcd \\
--name=\${ETCD_NAME} \\
--data-dir=\${ETCD_DATA_DIR} \\
--listen-peer-urls=\${ETCD_LISTEN_PEER_URLS} \\
--listen-client-urls=\${ETCD_LISTEN_CLIENT_URLS},http://127.0.0.1:2379 \\
--advertise-client-urls=\${ETCD_ADVERTISE_CLIENT_URLS} \\
--initial-advertise-peer-urls=\${ETCD_INITIAL_ADVERTISE_PEER_URLS} \\
--initial-cluster=\${ETCD_INITIAL_CLUSTER} \\
--initial-cluster-token=\${ETCD_INITIAL_CLUSTER} \\
--initial-cluster-state=new \\
--cert-file=/opt/kubernetes/cert/${HOSTNAME}.pem \\
--key-file=/opt/kubernetes/cert/${HOSTNAME}-key.pem \\
--peer-cert-file=/opt/kubernetes/cert/${HOSTNAME}.pem \\
--peer-key-file=/opt/kubernetes/cert/${HOSTNAME}-key.pem \\
--trusted-ca-file=/opt/kubernetes/cert/ca.pem \\
--peer-trusted-ca-file=/opt/kubernetes/cert/ca.pem
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```



## 启动服务

```bash
systemctl daemon-reload
systemctl enable etcd
systemctl start etcd
```



## 检查etcd状态

使用如下命令查看etcd集群状态

```bash
etcdctl -ca-file=/opt/kubernetes/cert/ca.pem --cert-file=/opt/kubernetes/cert/${HOSTNAME}.pem --key-file=/opt/kubernetes/cert/${HOSTNAME}-key.pem --endpoints="https://10.10.62.2:2379" cluster-health
```

- 如果多个etcd节点，endpoints里需要指明所有节点；



这里我的输出为

```
member c9d008b78bd0dcc is healthy: got healthy result from https://10.10.62.2:2379
cluster is healthy
```

> 输出为 `cluster is healthy` 则说明etcd正常。



使用如下命令查看etcd集群当前leader节点

```bash
ETCDCTL_API=3 /opt/kubernetes/bin/etcdctl -w table --cacert=/opt/kubernetes/cert/ca.pem --cert=/opt/kubernetes/cert/${HOSTNAME}.pem --key=/opt/kubernetes/cert/${HOSTNAME}-key.pem \
--endpoints="https://10.10.62.2:2379" endpoint status 
```

- 注意修改 endpoints 中的地址；



## 分配pod网络

后面pod的ip需要flanneld从etcd中获取，这里需要在etcd中为pod划分网段

```bash
etcdctl -ca-file=/opt/kubernetes/cert/ca.pem --cert-file=/opt/kubernetes/cert/${HOSTNAME}.pem --key-file=/opt/kubernetes/cert/${HOSTNAME}-key.pem --endpoints="https://10.10.62.2:2379" \
set /coreos.com/network/config '{"Network":"172.21.0.0/16","Backend":{"Type":"vxlan","VNI":1,"DirectRouting":true}}'
```

- 在一个etcd节点执行即可，数据会同步到其他节点；
- 这里设定了flanneld的工作方式为vxlan+directrouting；



查看划分结果

```bash
etcdctl -ca-file=/opt/kubernetes/cert/ca.pem --cert-file=/opt/kubernetes/cert/${HOSTNAME}.pem --key-file=/opt/kubernetes/cert/${HOSTNAME}-key.pem --endpoints="https://10.10.62.2:2379" \
get /coreos.com/network/config
```

> 输出的结果和设置的一致就可以。



应该在master和node的iptables中对分配的pod网段放开访问

```bash
iptables -I INPUT 5 -s 172.21.0.0/16  -j ACCEPT

# 修改 /etc/sysconfig/iptables 在合适位置增加如下规则
-A INPUT -s 172.21.0.0/16  -j ACCEPT
```



# 部署flannel

在master和node上都部署flanneld网络插件，这是因为后面metrics-server会通过master上连接pod



## 下载flanneld

```bash
wget https://github.com/coreos/flannel/releases/download/v0.11.0/flannel-v0.11.0-linux-amd64.tar.gz -P /usr/local/src
cd /usr/local/src
tar zxf flannel-v0.11.0-linux-amd64.tar.gz
cp -p flanneld mk-docker-opts.sh /opt/kubernetes/bin
```

- mk-docker-opts.sh脚本将分配给 flanneld 的 Pod 子网网段信息写入 /run/flannel/docker 文件，后续 docker 启动时使用这个文件中的环境变量配置 docker0 网桥；



## 创建flanneld配置文件

```bash
ETCD_ENDPOINTS="https://10.10.62.2:2379"

cat > /opt/kubernetes/conf/flanneld << EOF
FLANNEL_OPTIONS="--etcd-endpoints=${ETCD_ENDPOINTS} \
-etcd-cafile=/opt/kubernetes/cert/ca.pem \
-etcd-certfile=/opt/kubernetes/cert/st01009vm2.pem \
-etcd-keyfile=/opt/kubernetes/cert/st01009vm2-key.pem"
EOF
```



这里需要将etcd相关证书发送到所有部署有flanneld的节点，包括server公私钥和ca公钥。



## 创建flanneld.service文件

```bash
cat > /usr/lib/systemd/system/flanneld.service << EOF
[Unit] 
Description=Flanneld overlay address etcd agent 
After=network-online.target network.target 
Before=docker.service 

[Service] 
Type=notify 
EnvironmentFile=/opt/kubernetes/conf/flanneld 
ExecStart=/opt/kubernetes/bin/flanneld --ip-masq \$FLANNEL_OPTIONS 
ExecStartPost=/opt/kubernetes/bin/mk-docker-opts.sh -k DOCKER_NETWORK_OPTIONS -d /run/flannel/subnet.env
Restart=on-failure 

[Install] 
WantedBy=multi-user.target 
EOF
```

- mk-docker-opts.sh 脚本将分配给 flanneld 的 Pod 子网网段信息写入 /run/flannel/docker 文件，后续 docker 启动时使用这个文件中的环境变量配置 docker0 网桥；
- -ip-masq: flanneld 为访问 Pod 网络外的流量设置 SNAT 规则，同时将传递给 Docker 的变量 --ip-masq（/run/flannel/docker 文件中）设置为 false，这样 Docker 将不再创建 SNAT 规则；



**Docker 的 --ip-masq 为 true 时，创建的 SNAT 规则比较“暴力”：将所有本节点 Pod 发起的、访问非 docker0 接口的请求做 SNAT，这样访问其他节点 Pod 的请求来源 IP 会被设置为 flannel.1 接口的 IP，导致目的 Pod 看不到真实的来源 Pod IP。 flanneld 创建的 SNAT 规则比较温和，只对访问非 Pod 网段的请求做 SNAT。**



## 重新设置docker.service文件

重新设置该文件的目的是为了让docker在启动时加载flanneld分配的网段；由于master没有安装docker，这一步在所有node节点上执行即可。

```bash
cp -p /usr/lib/systemd/system/docker.service /usr/lib/systemd/system/docker.service.old
cat > /usr/lib/systemd/system/docker.service << EOF 
[Unit] 
Description=Docker Application Container Engine 
Documentation=https://docs.docker.com 
After=network-online.target firewalld.service 
Wants=network-online.target 

[Service] 
Type=notify 
EnvironmentFile=/run/flannel/subnet.env 
ExecStart=/usr/bin/dockerd \$DOCKER_NETWORK_OPTIONS 
ExecReload=/bin/kill -s HUP \$MAINPID 
LimitNOFILE=infinity 
LimitNPROC=infinity 
LimitCORE=infinity 
TimeoutStartSec=0 
Delegate=yes 
KillMode=process 
Restart=on-failure 
StartLimitBurst=3 
StartLimitInterval=60s 

[Install] 
WantedBy=multi-user.target 
EOF
```



## 启动flanneld

```bash
systemctl daemon-reload
systemctl enable flanneld
systemctl restart flanneld
```



## 启动docker

启动docker要在启动flanneld之后，否则docker无法加载flanneld分配的网络。master节点由于没有安装docker这一步就跳过。

```bash
systemctl restart docker
```



## 检查

docker和flanneld启动后会分别生成docker0和flannel.1虚拟网卡，首先应该检查这两个网卡应该是同一个段的；

在部署有flanneld的节点互相ping其他节点的docker0网桥应该是通的，这说明k8s集群网络打通了。

 

flanneld分配的网络会存储在etcd中，在etcd节点使用下面的命令可以查看分配情况：

```bash
etcdctl -ca-file=/opt/kubernetes/cert/ca.pem --cert-file=/opt/kubernetes/cert/${HOSTNAME}.pem --key-file=/opt/kubernetes/cert/${HOSTNAME}-key.pem --endpoints="https://10.10.62.2:2379" \
ls /coreos.com/network/subnets
```



我的输出为：

```
/coreos.com/network/subnets/172.21.24.0-24
/coreos.com/network/subnets/172.21.33.0-24
/coreos.com/network/subnets/172.21.82.0-24
/coreos.com/network/subnets/172.21.34.0-24
```



# 部署master节点

## 下载kubernetes

在master节点下载kubernetes

```bash
wget https://dl.k8s.io/v1.14.1/kubernetes-server-linux-amd64.tar.gz -P /usr/local/src
cd /usr/local/src
tar zxf kubernetes-server-linux-amd64.tar.gz
cd kubernetes/server/bin
cp -p kube-apiserver kube-scheduler kube-controller-manager kubectl/opt/kubernetes/bin/
```



## 创建kube-apiserver配置文件

```bash
MASTER_ADDRESS=10.10.62.2
ETCD_SERVERS="https://10.10.62.2:2379"

cat > /opt/kubernetes/conf/kube-apiserver << EOF
KUBE_APISERVER_OPTS="--enable-admission-plugins=Initializers,NamespaceLifecycle,NodeRestriction,LimitRanger,ServiceAccount,DefaultStorageClass,ResourceQuota \\
--anonymous-auth=true \\
--advertise-address=${MASTER_ADDRESS} \\
--bind-address=${MASTER_ADDRESS} \\
--insecure-port=8080 \\
--secure-port=6443 \\
--authorization-mode=RBAC,Node \\
--runtime-config=api/all \\
--enable-bootstrap-token-auth \\
--token-auth-file=/opt/kubernetes/cert/k8s/token.csv \\
--service-cluster-ip-range=172.24.0.0/16 \\
--service-node-port-range=30000-50000 \\
--tls-cert-file=/opt/kubernetes/cert/k8s/server.pem  \\
--tls-private-key-file=/opt/kubernetes/cert/k8s/server-key.pem \\
--client-ca-file=/opt/kubernetes/cert/k8s/ca.pem \\
--kubelet-client-certificate=/opt/kubernetes/cert/k8s/server.pem \\
--kubelet-client-key=/opt/kubernetes/cert/k8s/server-key.pem \\
--service-account-key-file=/opt/kubernetes/cert/k8s/ca-key.pem \\
--etcd-cafile=/opt/kubernetes/cert/etcd/ca.pem \\
--etcd-certfile=/opt/kubernetes/cert/etcd/etcd-st01009vm2.pem \\
--etcd-keyfile=/opt/kubernetes/cert/etcd/etcd-st01009vm2-key.pem \\
--etcd-servers=${ETCD_SERVERS} \\
--enable-swagger-ui=true \\
--enable-aggregator-routing=true \\
--proxy-client-key-file=/opt/kubernetes/cert/etcd/etcd-st01009vm2-key.pem \\
--proxy-client-cert-file=/opt/kubernetes/cert/etcd/etcd-st01009vm2.pem \\
--requestheader-client-ca-file=/opt/kubernetes/cert/k8s/ca-key.pem \\
--requestheader-username-headers=X-Remote-User \\
--requestheader-group-headers=X-Remote-Group \\
--requestheader-extra-headers-prefix=X-Remote-Extra- \\
--requestheader-allowed-names="" \\
--allow-privileged=true \\
--log-dir=/opt/kubernetes/log/ \\
--event-ttl=1h \\
--v=2 \\
--kubelet-https=true \\
--logtostderr=false"
EOF
```

- 如果有多个etcd应该写上所有的etcd节点；
- --service-cluster-ip-range： 指定 Service Cluster IP 地址段；
- --service-node-port-range： 指定 NodePort 的端口范围；



## 创建kube-apiserver.service文件

```bash
cat > /usr/lib/systemd/system/kube-apiserver.service << EOF 
[Unit] 
Description=Kubernetes API Server 
Documentation=https://github.com/kubernetes/kubernetes 

[Service] 
EnvironmentFile=-/opt/kubernetes/conf/kube-apiserver 
ExecStart=/opt/kubernetes/bin/kube-apiserver \$KUBE_APISERVER_OPTS 
Restart=on-failure 

[Install] 
WantedBy=multi-user.target 
EOF
```



## 启动kube-apiserver

```bash
systemctl daemon-reload
systemctl enable kube-apiserver
systemctl restart kube-apiserver
```



## 创建kube-controller-manager配置文件

```bash
cat > /opt/kubernetes/conf/kube-controller-manager << EOF
KUBE_CONTROLLER_MANAGER_OPTS="--logtostderr=false \\
--v=2 \\
--master=127.0.0.1:8080 \\
--leader-elect=true \\
--address=127.0.0.1 \\
--service-cluster-ip-range=172.24.0.0/16 \\
--cluster-name=kubernetes \\
--cluster-signing-cert-file=/opt/kubernetes/cert/ca.pem \\
--cluster-signing-key-file=/opt/kubernetes/cert/ca-key.pem  \\
--service-account-private-key-file=/opt/kubernetes/cert/ca-key.pem \\
--root-ca-file=/opt/kubernetes/cert/ca.pem \\
--experimental-cluster-signing-duration=8760h \\
--feature-gates=RotateKubeletServerCertificate=true \\
--controllers=*,bootstrapsigner,tokencleaner \\
--horizontal-pod-autoscaler-use-rest-clients=true \\
--horizontal-pod-autoscaler-sync-period=10s \\
--tls-cert-file=/opt/kubernetes/cert/${HOSTNAME}.pem \\
--tls-private-key-file=/opt/kubernetes/cert/${HOSTNAME}-key.pem \\
--use-service-account-credentials=true \\
--log-dir=/opt/kubernetes/log"
EOF
```

- --experimental-cluster-signing-duration指定 TLS Bootstrap 证书的有效期；
- --service-cluster-ip-range 指定 Service Cluster IP 网段，必须和 kube-apiserver 中的同名参数一致
- --leader-elect=true集群运行模式，启用选举功能；被选为 leader 的节点负责处理工作，其它节点为阻塞状态；
- --feature-gates=RotateKubeletServerCertificate=true开启 kublet server 证书的自动更新特性；
- --controllers=*,bootstrapsigner,tokencleaner启用的控制器列表，tokencleaner用于自动清理过期的 Bootstrap token；*
- --horizontal-pod-autoscaler-*custom metrics 相关参数，支持 autoscaling/v2alpha1；
- --tls-cert-file、--tls-private-key-file使用 https 输出 metrics 时使用的 Server 证书和秘钥；
- --use-service-account-credentials=trueClusteRole: system:kube-controller-manager 的权限很小，只能创建 secret、serviceaccount 等资源对象，各 controller 的权限分散到 ClusterRole system:controller:XXX 中。需要在 kube-controller-manager 的启动参数中添加 --use-service-account-credentials=true 参数，这样 main controller 会为各 controller 创建对应的 ServiceAccount XXX-controller。内置的 ClusterRoleBinding system:controller:XXX 将赋予各 XXX-controller ServiceAccount 对应的 ClusterRole system:controller:XXX 权限。



## 创建kube-controller-manager.service文件

```bash
cat > /usr/lib/systemd/system/kube-controller-manager.service << EOF
[Unit]
Description=Kubernetes Controller Manager
Documentation=https://github.com/kubernetes/kubernetes

[Service]
EnvironmentFile=-/opt/kubernetes/conf/kube-controller-manager
ExecStart=/opt/kubernetes/bin/kube-controller-manager \$KUBE_CONTROLLER_MANAGER_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```



## 启动kube-controller-manager

```bash
systemctl daemon-reload
systemctl enable kube-controller-manager
systemctl restart kube-controller-manager
```



## 设置kube-scheduler配置文件

```bash
cat > /opt/kubernetes/conf/kube-scheduler << EOF
KUBE_SCHEDULER_OPTS="--v=4 \\
--master=127.0.0.1:8080 \\
--leader-elect \\
--logtostderr=false \\
--log-dir=/opt/kubernetes/log/"
EOF
```



## 设置kube-scheduler.service文件

```bash
cat > /usr/lib/systemd/system/kube-scheduler.service << EOF
[Unit] 
Description=Kubernetes Scheduler 
Documentation=https://github.com/kubernetes/kubernetes 

[Service] 
EnvironmentFile=-/opt/kubernetes/conf/kube-scheduler 
ExecStart=/opt/kubernetes/bin/kube-scheduler \$KUBE_SCHEDULER_OPTS 
Restart=on-failure 

[Install] 
WantedBy=multi-user.target 
EOF
```



## 启动kube-scheduler

```bash
systemctl daemon-reload
systemctl enable kube-scheduler
systemctl restart kube-scheduler
```



## 查看集群状态

使用如下命令可以查看当前集群主要组件的一些状态

```bash
kubectl get cs

NAME                 STATUS    MESSAGE             ERROR
controller-manager   Healthy   ok                  
scheduler            Healthy   ok                  
etcd-0               Healthy   {"health":"true"} 
```



## 更新iptables规则

增加iptables规则，在master和node节点放开service网段

```bash
iptables -I INPUT 5 -s 172.24.0.0/16  -j ACCEPT

# 编辑/etc/sysconfig/iptables，增加如下规则
-A INPUT -s 172.24.0.0/16  -j ACCEPT
```



## 设置kubectl命令补全

kubectl命令用来管理k8s集群，其下的资源很多，不容易记住，可以设置bash变量来实现kubectl自动补全

```bash
echo "source <(kubectl completion bash)" >> ~/.bashrc
source ~/.bashrc
```

> 这样就可以使用tab键自动补全kubectl命令了



# 部署node节点

## 为kubelet-bootstrap用户授予权限

在master上执行如下命令为kubelet-bootstrap授予权限，否则无法颁发kubelet证书

```bash
kubectl create clusterrolebinding kubelet-bootstrap --clusterrole=system:node-bootstrapper --user=kubelet:bootstrap
```



## 下载node节点程序

node节点程序是kubelet和kube-proxy，这两个二进制文件可以在master节点的 /usr/local/src/kubernetes/server/bin下找到，在master将这些二进制文件发送到node节点的/opt/kubernetes/bin下。



## 创建kubelet配置文件

```bash
NODE_IP=10.10.62.3

cat > /opt/kubernetes/conf/kubelet <<EOF
KUBELET_OPTS="--logtostderr=false \\
--v=4 \\
--hostname-override=${NODE_IP} \\
--anonymous-auth \\
--kubeconfig=/opt/kubernetes/cert/kubelet.kubeconfig \\
--bootstrap-kubeconfig=/opt/kubernetes/cert/bootstrap.kubeconfig \\
--cert-dir=/opt/kubernetes/cert \\
--allow-privileged=true \\
--log-dir=/opt/kubernetes/log \\
--config=/opt/kubernetes/conf/kubelet.config \\
--pod-infra-container-image=registry.cn-hangzhou.aliyuncs.com/google-containers/pause-amd64:3.0"
EOF

cat > /opt/kubernetes/conf/kubelet.config << EOF
kind: KubeletConfiguration
apiVersion: kubelet.config.k8s.io/v1beta1
address: ${NODE_IP}
port: 10250
cgroupDriver: cgroupfs
clusterDNS:
- 172.24.0.2 
clusterDomain: cluster.local.
failSwapOn: false
EOF
```

- --cluster-dns指定集群dns的service地址（kubedns或coredns），这里规划为172.24.0.2；
- --cluster-domain指定集群服务域名的后缀；
- 注意修改node节点的名称和IP；
- --anonymous-auth允许匿名访问，否则kubectl无法连接pod；



## 创建kubelet.service文件

```bash
cat > /usr/lib/systemd/system/kubelet.service << EOF
[Unit]
Description=Kubernetes Kubelet
After=docker.service
Requires=docker.service

[Service]
EnvironmentFile=/opt/kubernetes/conf/kubelet
ExecStart=/opt/kubernetes/bin/kubelet \$KUBELET_OPTS
Restart=on-failure
KillMode=process

[Install]
WantedBy=multi-user.target
EOF
```



## 启动kubelet

```bash
systemctl daemon-reload
systemctl enable kubelet
systemctl restart kubelet
```



## node加入集群

启动kubelet后，在master节点执行如下命令查看node节点申请加入集群的请求

```bash
kubectl get csr

NAME                                                   AGE   REQUESTOR           CONDITION
node-csr-iqeoN3IuycS6N55r9l8HTaDYPUjxvumz2dDpMfkinPE   10s   kubelet-bootstrap   Pending
```



针对这个请求，执行如下命令加入集群

```bash
kubectl certificate approve node-csr-iqeoN3IuycS6N55r9l8HTaDYPUjxvumz2dDpMfkinPE
```



在master上查看node节点，已经加入

```bash
kubectl get node 

NAME         STATUS   ROLES    AGE   VERSION
10.10.62.3   Ready    <none>   6s    v1.13.4
```

> 其他节点也是同样的操作



## 创建kube-proxy配置文件

```bash
NODE_IP=10.10.62.3

cat > /opt/kubernetes/conf/kube-proxy <<EOF
KUBE_PROXY_OPTS="--logtostderr=false \\
--v=4 \\
--hostname-override=${NODE_IP} \\
--cluster-cidr=172.21.0.0/16 \\
--proxy-mode=ipvs \\
--masquerade-all \\
--ipvs-min-sync-period=5s \\
--ipvs-sync-period=5s \\
--ipvs-scheduler=rr \\
--kubeconfig=/opt/kubernetes/cert/kube-proxy.kubeconfig"
```



## 创建kube-proxy.service文件

```bash
cat > /usr/lib/systemd/system/kube-proxy.service <<EOF
[Unit]
Description=Kubernetes Proxy
After=network.target

[Service]
EnvironmentFile=-/opt/kubernetes/conf/kube-proxy
ExecStart=/opt/kubernetes/bin/kube-proxy \$KUBE_PROXY_OPTS
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```



## 启动 kube-proxy

```bash
systemctl daemon-reload
systemctl enable kube-proxy
systemctl restart kube-proxy
```



## 匿名用户授权

需要给匿名用户授权，否则无法通过kubectl连接pod。

