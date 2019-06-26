## 检查集群健康情况

```bash
ceph -s	//显示详细信息
cepg status
ceph health 	//返回健康结果
ceph health detail		// 返回不健康原因
```



## ceph命令指定配置文件和keyring

用于配置文件或keyring不在默认路径下的情况

```bash
ceph -c /path/to/conf -k /path/to/keyring health
```



## 观察集群事件

```bash
ceph -w
```



## 集群数据使用量及其在pool内分布情况

```bash
ceph df
```



## 检查osd状态

```bash
ceph osd stat		
ceph osd dump	// 输出osd详细信息
```



## 查看每个osd使用情况

```bash
ceph osd df
```



## 打印crush树

```bash
ceph osd tree
```



## 检查mon状态

```bash
ceph mon dump	// 输出mon详细信息 

ceph mon stat
```



 

## 检查监视器法定人数

```bash
ceph quorum_status -f json-pretty
```



 

## 检查mds状态

```bash
ceph mds stat

ceph mds dump
```



 

## 获取pg列表

```bash
ceph pg dump

ceph pg dump -o {filename} -f json-pretty	// 以json格式输出到文件中
```



 

## 查看指定pg的acting set或up set中包含的osd

```bash
ceph pg map {pg-num}	// up set 和 acting set一般相同
```



 

## 查看所有pg状态

```bash
ceph pg stat	// 所有pg应该都处于clean+active状态
```



 

## 找出故障pg

```bash
ceph pg dump_stuck [unclean|inactive|stale|undersized|degraded]
```



 

## 创建对象

```bash
rados put {object-name} {file-path} --pool={pool-name}
```



 

## 确认已存储此对象

```bash
rados -p {pool-name} ls
```



 

## 定位对象位置

```bash
ceph osd map {pool-name} {object-name}
```



 

## 删除对象

```bash
rados rm {object-name} --pool={pool-name}
```



 

## 授权

<https://lihaijing.gitbooks.io/ceph-handbook/content/Operation/user_management.html>

 

## 罗列用户

```bash
ceph auth list
```



 

## 获取特定用户的信息

```bash
ceph auth get {TYPE.ID}
```



 

## 新增用户

```bash
ceph auth add		// 最权威的方式，新增用户和key并赋予任何给定的权限

ceph auth get-or-create		// 最便捷，返回用户名和秘钥格式

ceph auth get-or-create-key		// 只返回秘钥
```



 

## 删除用户

```bash
ceph auth del {TYPE.ID}
```



 

## 查看crush map，输出包括集群存储设备信息、故障域层次结构、失败域规则

```bash
ceph osd crush dump
```



 

## 增加和删除mon

<https://lihaijing.gitbooks.io/ceph-handbook/content/Operation/add_rm_mon.html>

 

## 增减和删除osd

<https://lihaijing.gitbooks.io/ceph-handbook/content/Operation/add_rm_osd.html>

 

## 列出pool

```bash
ceph osd lspools

rados lspools	// 只有pool-name没有pool-id
```



 

## 创建存储池

<https://lihaijing.gitbooks.io/ceph-handbook/content/Operation/operate_pool.html#>

 

## 删除存储池

```bash
ceph osd pool delete {pool-name} [{pool-name} --yes-i-really-really-mean-it]
```



 

## 重命名存储池

```bash
ceph osd pool rename {old_name} {new_name}
```



 

## 查看存储池统计信息

```bash
rados df 
```



 

## 给存储池快照

```bash
ceph osd pool mksnap {pool-name} {snap_name}
```



 

## 删除存储池快照

```bash
ceph osd pool rmsnap {pool-name} {snap-name}
```



 

## 获取存储池选项值

```bash
ceph osd pool get {pool_name} {key}
```



 


## 调整存储池选项值

```bash
ceph osd pool set {pool-name} {key} {value}
```



 

## 获取对象副本数

```bash
ceph osd dump | grep 'replicated size'
```



 

## 获取crush map

```bash
ceph osd getcrushmap -o crushmap_complied_file	// 从任意monitor获取，需要反编译
crushtool -d crushmap_complied_file -o crushmap_decomplied_file  //  反编译crush map
crushtool -c crushmap_decomplied_file -o newcrushmap  // 编译修改后的crushmap
ceph osd setcrushmap -i newcrushmap   // 将新编译的crushmap注入集群
```



## 增加桶和移动osd

<https://blog.csdn.net/signmem/article/details/78602374>

 

## 删除桶

```bash
ceph osd crush remove {bucket-name}		// 必须是空桶
```



 

## 查看运行时配置

```bash
ceph daemon {daemon-type}.{id} config show | less

如：ceph daemon osd.0 config show | less
```



 

## 查看rbd镜像大小

```bash
rbd du <pool>/<image>		// 需要开启layering, exclusive-lock, object-map, fast-diff属性
```



 

## 查看使用rbd的主机

```bash
rbd status <pool>/<image>
```



 

## 查看创建的image

```bash
rbd ls pool
```



 

## 查看image信息

```bash
rbd info pool/image1
```



 

## 删除image

```bash
rbd rm pool/image1
```



 

## 为image创建快照，名为image1_snap

```bash
rbd snap create pool/image1@image1_snap
```



 

## 查看快照

```bash
rbd snap list pool/image1bash
```



 

## 长格式查看

```bash
rbd ls pool -l
```



 

## 查看快照更新的详细信息

```bash
rbd info pool/image1@image1_snap
```



 

## 克隆快照，克隆前快照必须处于保护状态

```bash
rbd snap protect pool/image1@image1_snap

rbd clone pool/image1@image1_snap rbd/image2	// 克隆快照到另一个pool并成为新的image2，新的image2依赖父image
```



 

## 查看快照的子（children）

```bash
rbd clildren pool/image@image1_snap
```



 

## 将rbd image变为扁平的没有层级的image

```bash
rbd flatten rbd/image2		// 再次查看rbd/image2已经没有父image存在了，断开了依赖关系（rbd ls rbd -l）
```



 

## 导出rbd image

```bash
rbd export pool/image1 tmpimage1_export
```



