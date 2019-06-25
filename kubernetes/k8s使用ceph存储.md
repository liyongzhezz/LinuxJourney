# pv、pvc方式

管理员需要预先创建相关的pv和pvc，然后开发人员在创建容器的时候对pvc进行消费而无需关注后端存储。



## 准备

kubernetes集群的搭建不再赘述。再使用ceph存储之前，需要在master和node节点安装ceph-common（版本不能太低）然后然后将ceph.client.admin.keyring  ceph.conf复制到节点ceph目录下。



## 在ceph中创建image

这里创建一个10G大小的名为k8s的image用于测试

```bash
$ rbd create k8s --size 10G
$ rbd list
k8s
```



## 关闭image不支持的特性

```bash
$ rbd feature disable k8s object-map exclusive-lock fast-diff deep-flatten
$ rbd info k8s
rbd image 'k8s':
	size 10240 MB in 2560 objects
	order 22 (4096 kB objects)
	block_name_prefix: rbd_data.10f6238e1f29
	format: 2
	features: layering
	flags: 
```



## 在k8s上创建ceph secret

```bash
$ grep key /etc/ceph/ceph.client.admin.keyring |awk '{printf "%s", $NF}'|base64

QVFBVlduRmJ5Nm93T1JBQUwvdFc4c1JBUFFnV2dRWUkzUnJYUXc9PQ==
```



创建secret文件，将key替换为上边命令的输出

```bash
$ cat > ceph-secret.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: ceph-secret
type: "kubernetes.io/rbd"
data:
  key: QVFBVlduRmJ5Nm93T1JBQUwvdFc4c1JBUFFnV2dRWUkzUnJYUXc9PQ==
EOF

$ kubectl create -f ceph-secret.yaml
```

> 注意，secret所在的namespace要和pvc所在的namespace相同



## 创建pv

```bash
$ cat > rbd-pv-5G.yaml << EOF 
apiVersion: v1
kind: PersistentVolume
metadata:
  name: ceph-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  rbd:
    monitors:
      - 10.10.97.32:6789
      - 10.10.97.33:6789
      - 10.10.97.34:6789
    pool: rbd
    image: k8s
    user: admin
    secretRef:
      name: ceph-secret
    fsType: ext4
    readOnly: false
  persistentVolumeReclaimPolicy: Recycle
EOF

$ kubectl create -f rbd-pv-5G.yaml
```



> 注意将monitors修改为你的ceph mon节点地址



## 创建pvc

```bash
$ cat > rbd-pvc-5G.yaml << EOF 
apiVersion: v1
kind: PersistentVolumeClaim
metadata: 
  name: ceph-pvc
spec:
  accessModes: 
    - ReadWriteOnce
  resources:
    requests:
      storage: 5G
EOF

$ kubectl create -f rbd-pvc-5G.yaml
```



## 查看创建结果

```bash
$ kubectl get pv,pvc

NAME         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS    CLAIM              STORAGECLASS   REASON    AGE

pv/ceph-pv   5Gi        RWO            Recycle          Bound     default/ceph-pvc                            3m

 

NAME           STATUS    VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE

pvc/ceph-pvc   Bound     ceph-pv   5Gi        RWO                           6s
```

pvc和pv已经处于绑定状态，下面就可以使用pvc进行挂载了。



## 创建pod挂载pvc

```bash
$ cat > nginx.yaml << EOF 
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
    - name: nginx
      image: nginx
      volumeMounts:
      - mountPath: "/usr/share/nginx/html"
        name: wwwroot
  volumes:
    - name: wwwroot
      persistentVolumeClaim:
        claimName: ceph-pvc
EOF

$ kubectl create -f nginx.yaml
```





# StorageClass方式

pv和pvc方式的不便之处在于管理员需要预先生成一些定额的pv和pvc来供开发人员使用，StorageClass方式可以动态的分配存储卷大小，无需配置固定大小的pv。



## 准备

kubernetes集群的搭建不再赘述。再使用ceph存储之前，需要在node节点安装ceph-common然后然后将ceph.client.admin.keyring  ceph.conf复制到node节点ceph下



## 创建存储池

这里和pv/pvc方式不同的是，pv/pvc方式需要在pool中创建image，而StorageClass方式则是对pool直接操作，所以可以创建不同的pool并进行相应的配额限制。这里就以默认的rbd池为例。



## 创建secret

创建方式和上边的方法相同，这里不再赘述。



## 创建storage class

```bash
$ cat > storageclass.yaml << EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-storageclass
provisioner: kubernetes.io/rbd
parameters:
  monitors: 10.10.97.32:6789,10.10.97.33:6789,10.10.97.34:6789
  adminId: admin
  adminSecretName: ceph-secret
  adminSecretNamespace: default
  pool: rbd
  userId: admin
  userSecretName: ceph-secret
  userSecretNamespace: default
  fsType: ext4
EOF

$ kubectl create -f storageclass.yaml
```

- `adminId`: ceph 客户端ID，能够在pool中创建image, 默认是admin
- `adminSecretName`: ceph客户端秘钥名(第一步中创建的秘钥)
- `adminSecretNamespace`: 秘钥所在的namespace
- `pool`: ceph集群中的pool, 可以通过命令 ceph osd pool ls查看
- `userId`: 使用rbd的用户ID，默认admin
- `userSecretName`: 同上



## 创建pvc

```bash
$ cat > sc-pvc.yaml  <<  EOF
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: ceph-sc-pvc
spec:
  storageClassName: ceph-storageclass
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF
```



或者

```bash
$ cat > sc-pvc.yaml  <<  EOF
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: ceph-sc-pvc
  annotations:
    volume.beta.kubernetes.io/storage-class: ceph-storageclass 
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF
```



## 查看pvc

```bash
$ kubectl get pv,pvc
NAME                                          CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS    CLAIM                 STORAGECLASS        REASON    AGE
pv/ceph-pv                                    5Gi        RWO            Recycle          Bound     default/ceph-pvc                                    4h
pv/pvc-1d580fac-9f87-11e8-a0f1-005056a5946d   10Gi       RWO            Delete           Bound     default/ceph-sc-pvc   ceph-storageclass             1h

NAME              STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS        AGE
pvc/ceph-pvc      Bound     ceph-pv                                    5Gi        RWO                                3h
pvc/ceph-sc-pvc   Bound     pvc-1d580fac-9f87-11e8-a0f1-005056a5946d   10Gi       RWO            ceph-storageclass   1h
```

> 可以看到ceph-sc-pvc已经创建且为绑定状态了



## 创建测试pod

```bash
$ cat > nginx-sc.yaml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: mypod-pvc
spec:
  containers:
    - name: nginx
      image: nginx
      volumeMounts:
      - mountPath: "/usr/share/nginx/html"
        name: wwwroot
  volumes:
    - name: wwwroot
      persistentVolumeClaim:
        claimName: ceph-sc-pvc
EOF

$ kubectl create -f nginx-sc.yaml
```



