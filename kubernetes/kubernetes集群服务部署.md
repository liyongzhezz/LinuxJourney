# 部署dashboard

dashboard是kubernetes下一个web可视化交互管理页面，提供了对k8s资源的可视化管理。



## 文件准备

相关yaml文件可以在yaml/dashboard下找到，这里也提供了dashboard证书，在yaml/dashboard/cert下。

> dashboard使用证书的原因是：若不给dashboard提供自签证书，其通过chrome访问将提示证书问题无法访问。



## 文件修改

在 /opt/kubernetes/yaml下创建目录dashboard，并将相关yaml文件下载到该目录中。

- dashboard-configmap.yaml：项目配置；
- dashboard-controller.yaml：项目控制器；
- dashboard-rbac.yaml：权限配置；
- dashboard-secret.yaml：秘钥配置；
- dashboard-service.yaml：服务配置；

 

修改dashboard-controller.yaml文件中的镜像image为国内源镜像：registry.cn-hangzhou.aliyuncs.com/google_containers/kubernetes-dashboard-amd64:v1.10.0

修改dashboard-service.yaml文件，在spec下增加service类型为nodeport，这样可以通过节点访问：type: NodePort

修改dashboard-rbac.yaml中权限配置，默认权限不足，将RoleBinding改为ClusterRoleBinding，将roleRef下的kind改为ClusterRole，将name改为cluster-admin

 

## 创建dashboard管理员

创建k8s-admin.yaml文件，设置dashboard管理员

```bash
$ cat > k8s-admin.yaml << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-admin
  namespace: kube-system
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: dashboard-admin
subjects:
  - kind: ServiceAccount
    name: dashboard-admin
    namespace: kube-system
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
EOF
```



## 修改dashboard-secret.yaml文件

可以使用我提供的证书，如果想自己生成，则使用如下命令

```bash
$ openssl genrsa -des3 -passout pass:x -out dashboard.pass.key 2048
$ openssl rsa -passin pass:x -in dashboard.pass.key -out dashboard.key
$ openssl req -new -key dashboard.key -out dashboard.csr
$ openssl x509 -req -sha256 -days 365 -in dashboard.csr -signkey dashboard.key -out dashboard.crt
$ mv dashboard.key dashboard.crt /opt/kubernetes/cert
```



然后修改dashboard-secret.yaml文件，这里先获取到这里两个证书的秘钥

```bash
$ kubectl create secret generic helloworld-tls --from-file=/opt/kubernetes/cert/dashboard.crt --from-file=/opt/kubernetes/cert/dashboard.key --dry-run -o yaml

# 获取到其中的data部分，如果使用我提供的证书，复制下面的部分即可
data:
  dashboard.crt: LS0tLS1CRUdJTi...
  dashboard.key: LS0tLS1CRUdJT...
```

> 输出内容太长省略



修改dashboard-secret.yaml文件，在kubernetes-dashboard-certs这个secret下添加上面的证书秘钥

```bash
apiVersion: v1
kind: Secret
metadata:
  labels:
    k8s-app: kubernetes-dashboard
    # Allows editing resource and makes sure it is created first.
    addonmanager.kubernetes.io/mode: EnsureExists
  name: kubernetes-dashboard-certs
  namespace: kube-system
type: Opaque
<这里替换为上边的内容>
```



## 部署

```bash
$ cd /opt/kubernetes/yaml/dashboard/
$ kubectl apply -f .
```



## 检查

检查资源运行情况

```bash
$ kubectl get pod -o wide -n kube-system

NAME                                    READY   STATUS    RESTARTS   AGE    IP            NODE         NOMINATED NODE   READINESS GATES
kubernetes-dashboard-785f8ff65c-h2hhl   1/1     Running   0          5m5s   172.21.34.2   10.10.62.5   <none>           <none>

$ kubectl get svc -n kube-system
NAME                   TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)         AGE
kubernetes-dashboard   NodePort   172.24.169.58   <none>        443:30866/TCP   88s
```

> 这里显示dashboard访问端口为node节点的30866端口。



获取登陆token在登陆的时候使用

```bash
$ kubectl get secret -n kube-system | grep dashboard-token
kubernetes-dashboard-token-92l5k                 kubernetes.io/service-account-token   3      28m

$ kubectl describe secret kubernetes-dashboard-token-92l5k -n kube-system
# 获取其中的token值并复制
```



在浏览器访问任意node节点ip的30866端口，例如：https://10.10.62.3:30866，将会进入如下的界面，选择令牌，粘贴进token并点击登录即可。![dashboard-login](statics/dashboard-login.png)





# 部署coredns

Kubernetes集群推荐使用Service Name而不是service ip作为服务的访问地址，因此需要一个Kubernetes集群范围的DNS服务实现从Service Name到Cluster Ip的解析，从Kubernetes 1.11开始，可使用CoreDNS作为Kubernetes的DNS插件进入GA状态，Kubernetes推荐使用CoreDNS作为集群内的DNS服务。kube-dns也是可选的。

 

## 文件准备

yaml配置文件可以在 yaml/coredns中找到。



## 修改yaml文件

需要修改文件的如下内容（根据自身集群情况）：

- 将第67行的cluster.local改成自己集群规划的域名后缀
- 修改115行的镜像地址为image: coredns/coredns:1.2.6（默认的镜像仓库国内无法下载）
- 将180行的clusterIP: 172.24.0.2改成规划的集群dns service的地址（可以在kubelet配置文件中看到指定的dns service地址）



## 部署coredns

执行下面的命令部署coredns

```bash
$ kubectl create -f coredns.yaml
```



## 检查

查看pod运行状态，确保服务运行正常

```bash
$ kubectl get pod -n kube-system
NAME                                    READY   STATUS    RESTARTS   AGE
coredns-dc8bbbcf9-r6nf6                 1/1     Running   0          52s

$ kubectl get svc -n kube-system
NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)         AGE
kube-dns               ClusterIP   172.24.0.2      <none>        53/UDP,53/TCP   2m11s
```



## 测试dns

首先在命令行启动并进入到一个测试pod中

```bash
$ kubectl run -ti --image=busybox:1.28.4 --rm --restart=Never sh
```



目前我已有的service（除过dns服务）是dashboard，其svc名称为kubernetes-dashboard，于是在busybox容器中检测能否通过service name解析dashboard服务。

```bash
# 查看pod内部dns配置文件已经改为core-dns的service地址
/ # cat /etc/resolv.conf 
nameserver 172.24.0.2
search default.svc.cluster.local. svc.cluster.local. cluster.local.
options ndots:5

# 解析内部kubernetes-dashboard服务，成功解析
/ # nslookup kubernetes-dashboard.kube-system.svc.cluster.local
Server:    172.24.0.2
Address 1: 172.24.0.2 kube-dns.kube-system.svc.cluster.local

Name:      kubernetes-dashboard.kube-system.svc.cluster.local
Address 1: 172.24.169.58 kubernetes-dashboard.kube-system.svc.cluster.local

# 解析外网域名，成功解析
/ # nslookup www.baidu.com
Server:    172.24.0.2
Address 1: 172.24.0.2 kube-dns.kube-system.svc.cluster.local

Name:      www.baidu.com
Address 1: 14.215.177.39
Address 2: 14.215.177.38
```

> 在集群内通过dns解析service-name时，格式为：<service-name>.<namespace>.svc.<dns域名后缀>，也可以简写为 <service-name>.<namespace>；如果是发起解析请求的pod和目标servcie在同一个namespace，那么直接使用service-name就可以解析。



