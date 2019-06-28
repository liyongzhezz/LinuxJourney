# Helm基础概念



## 什么是Helm

helm是Kubernetes的一个包管理工具，用来简化Kubernetes应用的部署和管理。可以把Helm比作CentOS的yum工具。 



使用Helm可以完成以下事情：

- 管理Kubernetes manifest files
- 管理Helm安装包charts
- 基于chart的Kubernetes应用分发



## Helm有如下几个基本概念：

Chart: 是Helm管理的安装包，里面包含需要部署的安装包资源。可以把Chart比作CentOS yum使用的rpm文件。每个Chart包含下面的部分：



Chart.yaml：是包的基本描述文件



放在templates目录中的一个或多个Kubernetes manifest文件模板



Release：是chart的部署实例，一个chart在一个Kubernetes集群上可以有多个release，即这个chart可以被安装多次



Repository：chart的仓库，用于发布和存储chart



## Helm组成

Helm由两部分组成，客户端helm和服务端tiller。

- tiller运行在Kubernetes集群上，管理chart安装的release；
- Helm是一个命令行工具，可在本地运行；





# 安装Helm



## 安装helm客户端

首先下载Helm二进制文件，下载地址在 [github-Helm](https://github.com/helm/helm/releases) ，我下载的版本为 `2.14.1` 。

```bash
$ wget https://get.helm.sh/helm-v2.14.1-linux-amd64.tar.gz
$ tar zxf helm-v2.14.1-linux-amd64.tar.gz
$ cd linux-amd64
$ mv helm /usr/local/bin/
```



此时已经安装完毕helm客户端，运行下面的命令检查客户端运行情况：

```bash
$ helm version
Client: &version.Version{SemVer:"v2.14.1", GitCommit:"5270352a09c7e8b6e8c9593002a73535276507c0", GitTreeState:"clean"}
Error: could not find tiller
```

> 可以看到客户端正常，报错是因为没有安装tiller服务端，连接不上。



在安装tiller服务端之前，确保这台机器上正确配置了kubectl命令并能够连接到集群，这里我使用的是master节点，这里的kubectl是可以连接集群的。

```bash
$ kubectl get cs
NAME                 STATUS    MESSAGE             ERROR
scheduler            Healthy   ok                  
etcd-0               Healthy   {"health":"true"}   
controller-manager   Healthy   ok     
```



## 建立serviceaccount

建立一个serviceaccount，在部署服务端tiller的时候使用，再这样可以实现对tiller的权限限制，例如让helm只能在某个namespace下安装资源，这里我设置为cluster-admin权限，让其可以在任何namespace下创建资源。

> 官方说明可以参看 [helm-rbac设置](https://helm.sh/docs/using_helm/#role-based-access-control)



```bash
$ cat helm-rbac.yaml << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
    
$ kubectl create -f helm-rbac.yaml
```





## 部署服务端tiller

使用helm在集群中部署tiller：

```bash
$ kubectl create serviceaccount tiller -n kube-system
$ helm init --service-account tiller --skip-refresh
helm init --service-account tiller --skip-refresh
Creating /root/.helm 
Creating /root/.helm/repository 
Creating /root/.helm/repository/cache 
Creating /root/.helm/repository/local 
Creating /root/.helm/plugins 
Creating /root/.helm/starters 
Creating /root/.helm/cache/archive 
Creating /root/.helm/repository/repositories.yaml 
Adding stable repo with URL: https://kubernetes-charts.storage.googleapis.com 
Adding local repo with URL: http://127.0.0.1:8879/charts 
$HELM_HOME has been configured at /root/.helm.

Tiller (the Helm server-side component) has been installed into your Kubernetes Cluster.

Please note: by default, Tiller is deployed with an insecure 'allow unauthenticated users' policy.
To prevent this, run `helm init` with the --tiller-tls-verify flag.
For more information on securing your installation see: https://docs.helm.sh/using_helm/#securing-your-helm-installation
```

> 安装时可通过参数 --tiller-namespace 来指定一个namespace，默认在kube-system下



稍等片刻在集群中tiller服务将会启动，默认在kube-system这个namespace下：

```bash
$ kubectl get pod -n kube-system | grep tiller
tiller-deploy-6d65d78679-sxcnm          1/1     Running   0          2m
```





## 依赖安装

helm依赖于socat做客户端和服务端的端口转发，所以需要在node节点安装socat软件包，安装命令如下：

```bash
$ yum install -y socat
```



然后使用下面的命令，看到helm客户端和服务端都正常返回了：

```bash
$ helm version
Client: &version.Version{SemVer:"v2.14.1", GitCommit:"5270352a09c7e8b6e8c9593002a73535276507c0", GitTreeState:"clean"}
Server: &version.Version{SemVer:"v2.14.1", GitCommit:"5270352a09c7e8b6e8c9593002a73535276507c0", GitTreeState:"clean"}
```





#helm基本使用



## 查看当前源更新chart repo

安装完helm后，默认有一个google的chart repo和本地repo，使用如下命令可以查看到：

```bash
$ helm repo list
helm repo list
NAME  	URL                                             
stable	https://kubernetes-charts.storage.googleapis.com
local 	http://127.0.0.1:8879/charts 
```



使用下面的命令可以更新helm的chart源，但是前提是可以访问google。

```bash
$ helm repo update
```



## 创建第一个chart

我们可以自定义一个chart，并使用这个chart来部署服务，例如服务名称为hello-svc，则使用下面的命令可以创建这个chart：

```bash
$ helm create hello-svc
```

> 这个命令会在当前目录下创建 hello-svc 项目目录。



helm创建的chart的结构如下：

```bash
hello-svc
├── charts
├── Chart.yaml
├── templates
│   ├── deployment.yaml
│   ├── _helpers.tpl
│   ├── ingress.yaml
│   ├── NOTES.txt
│   ├── service.yaml
│   └── tests
│       └── test-connection.yaml
└── values.yaml
```

- charts：该chart依赖的其他chart；
- Chart.yaml：描述chart的基本信息如名称、版本等；
- templates：Kubernetes manifest文件模板目录，模板使用chart配置的值生成Kubernetes manifest文件。模板文件使用的Go语言模板语法；
- template/NOTES.txt：一般填写chatr的使用说明；
- values.yaml：chart配置的默认值；



通过查看 `values.yaml` 文件可以看出，默认helm安装的chart是一个nginx服务。





## 进行测试

使用helm安装chart时，实际上是将chart的模板生成Kubernetes使用的yaml文件。 在编写chart的过程中可以在chart目录下使用下面的命令来验证模板和配置。

```bash
$ helm install --dry-run --debug ./
[debug] Created tunnel using local port: '1857'

[debug] SERVER: "127.0.0.1:1857"

[debug] Original chart version: ""
[debug] CHART PATH: /opt/kubernetes/yaml/hello-svc

NAME:   jolly-sparrow
REVISION: 1
RELEASED: Thu Jun 27 19:14:42 2019
CHART: hello-svc-0.1.0
USER-SUPPLIED VALUES:
...    // 这一部分是基于yaml模板和配置生成的yaml文件
```





## 安装chart

现在通过修改默认参数文件，或者直接使用当前配置部署chart，在chart目录执行如下命令即可：

```bash
$ chart install ./
NAME:   ignoble-wolf
LAST DEPLOYED: Thu Jun 27 19:17:33 2019
NAMESPACE: default
STATUS: DEPLOYED

RESOURCES:
==> v1/Deployment
NAME                    READY  UP-TO-DATE  AVAILABLE  AGE
ignoble-wolf-hello-svc  0/1    1           0          0s

==> v1/Pod(related)
NAME                                     READY  STATUS             RESTARTS  AGE
ignoble-wolf-hello-svc-64bdfd9449-z82z2  0/1    ContainerCreating  0         0s

==> v1/Service
NAME                    TYPE       CLUSTER-IP     EXTERNAL-IP  PORT(S)  AGE
ignoble-wolf-hello-svc  ClusterIP  172.24.111.91  <none>       80/TCP   0s


NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=hello-svc,app.kubernetes.io/instance=ignoble-wolf" -o jsonpath="{.items[0].metadata.name}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl port-forward $POD_NAME 8080:80
```

> 通过上面的输出可以清楚的看出有哪些资源被创建



默认资源被创建在了default下，查看default下的资源：

```bash
$ kubectl get all
NAME                                          READY   STATUS    RESTARTS   AGE
pod/ignoble-wolf-hello-svc-64bdfd9449-z82z2   1/1     Running   0          95s

NAME                             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/ignoble-wolf-hello-svc   ClusterIP   172.24.111.91   <none>        80/TCP    95s

NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ignoble-wolf-hello-svc   1/1     1            1           95s

NAME                                                DESIRED   CURRENT   READY   AGE
replicaset.apps/ignoble-wolf-hello-svc-64bdfd9449   1         1         1       95s
```



查看release：

```bash
$ helm list
NAME        	REVISION	UPDATED                 	STATUS  	CHART          	APP VERSION	NAMESPACE
ignoble-wolf	1       	Thu Jun 27 19:17:33 2019	DEPLOYED	hello-svc-0.1.0	1.0        	default  
```



## 删除chart

想要删除这个release可以使用如下的命令：

```bash
$ helm delete ignoble-wolf
release "ignoble-wolf" deleted
```



##chart打包 

将chart打包之后便可以分发给别人使用了，打包命令如下：

```bash
$ helm package ./
Successfully packaged chart and saved it to: /opt/kubernetes/yaml/hello-svc/hello-svc-0.1.0.tgz
```

> 会在当前目录下生成该chart的压缩文件





## 添加源

可以添加其他第三方的源，例如：

```bash
# 添加fabric8库
$ helm repo add fabric8 https://fabric8.io/helm
$ help repo list
NAME   	URL                                             
stable 	https://kubernetes-charts.storage.googleapis.com
local  	http://127.0.0.1:8879/charts                    
fabric8	https://fabric8.io/helm
```



添加好了之后，可以通过下面的命令查看fabric8提供了哪些资源：

```bash
$ helm search fabric8
NAME                                	CHART VERSION	APP VERSION	DESCRIPTION                                                 
fabric8/fabric8-camel               	2.2.168      	           	Sonatype helps open source projects to set up Maven repos...
fabric8/fabric8-console             	2.2.199      	           	Sonatype helps open source projects to set up Maven repos...
fabric8/fabric8-docker-registry     	2.2.327      	           	[Docker Registry](https://github.com/docker/distribution)...
fabric8/fabric8-dsaas               	1.0.54       	           	The Fabric8 Online Platform                                 
fabric8/fabric8-forge               	2.3.90       	           	Fabric8 :: Forge                                            
fabric8/fabric8-online              	1.0.20       	           	The Fabric8 Online Platform                                 
fabric8/fabric8-online-team         	1.0.54       	           	The Fabric8 Microservices Online :: Team  
......
```



## helm命令自动补全

使用下面的命令可以实现helm命令的自动补全：

```bash
$ source <(helm completion bash)
```



