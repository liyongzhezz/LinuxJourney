

# osd盘故障更换



## 现象

ceph 集群中使用ceph osd tree 命令发现有osd的状态为down。

 

## 故障排查

很大可能性是osd的磁盘出现了故障，若是物理磁盘故障则需要更换磁盘。ceph在osd故障变为down后会将此osd踢出集群。

 

## 故障处理

首先手动激活此osd，例如：

```
$ ceph-deploy osd activate ceph-44:/dev/sdd
```



然后使用 `ceph osd tree`  命令查看此osd是否恢复为up状态。

 

若没有恢复为up状态则很大可能性是磁盘物理故障，使用touch、dd、smartctl等命令检测磁盘健康状态，若确认为物理故障，执行下列操作：

 

```bash
# 卸载磁盘，如：

$ umount /dev/sdd

# 将故障osd踢出集群，如：

$ ceph osd out osd.33

# 停止osd进程，如：

$ systemctl stop ceph-osd@33

# 从crushmap中删除此osd，如：

$ ceph osd crush remove osd.33

# 删除此osd，如：

$ ceph auth del osd.33

$ ceph osd rm osd.33

# 更换新的硬盘并初始化，如（假设新加的硬盘盘符为sdf）：

$ ceph-deploy disk zap ceph-44:/dev/sdf

$ ceph-deploy osd prepare --fs-type btrfs ceph-44:/dev/sdf:/dev/sde3		// sde3为ssd分区挂载journal

$ ceph-deploy osd activate ceph-44:/dev/sdf1
```



 

## 检测

执行上述步骤且没有出现问题后，ceph将开始进行数据重新平衡，速度取决于网络、服务器配置和数据量，最终应该达到如下的效果：

```bash
# osd状态都为up且新加的osd也已加入crushmap

$ ceph osd tree

# ceph集群状态为HEALTH

$ ceph -s
```




# too many PGs per OSD

## 现象

在添加了一个pool后，ceph集群进入和 `WARNING  `  状态，使用 `ceph -s`  查看到下面的报错：

```bash
    cluster 9dc6e787-661e-46bb-a2a3-32ad9811ea4a

     health HEALTH_WARN

​            **too many PGs per OSD (341 > max 300)**

     monmap e2: 3 mons at {tw061132=10.33.15.11:6789/0,tw061145=10.33.15.19:6789/0,tw061154=10.33.15.28:6789/0}

            election epoch 12, quorum 0,1,2 tw061132,tw061145,tw061154

        mgr active: tw061145 standbys: tw061132, tw061154

     osdmap e2426: 54 osds: 54 up, 54 in

            flags sortbitwise,require_jewel_osds,require_kraken_osds

      pgmap v671041: 6144 pgs, 3 pools, 37680 MB data, 12068 objects

            163 GB used, 100406 GB / 100569 GB avail

                6144 active+clean

    client io 361 kB/s wr, 0 op/s rd, 67 op/s wr
```



 

## 原因

这个错误的意思是：配个osd上有太多的pgs（341个），大于了当前最大的限制300。

 

通过下面的命令可以查看到当前集群中每个osd上的默认pgs个数：

```bash
$ ceph --show-config  | grep mon_pg_warn_max_per_osd

mon_pg_warn_max_per_osd = 300
```



>  可以看到当前每个osd上最大允许300个pgs，超过这个值会有warn告警。

 

因为在创建pool的时候，每个pool会占用一些pg，pool中pg数目设置不合理，导致集群 total pg 数过多。

 

## 解决办法

在一台mon节点上，修改配置文件，在  ```[global]``` 下添加如下的配置：

```bash
[global]

...

mon_pg_warn_max_per_osd = 500
```



然后将修改后的配置文件发送到其他的两个mon节点：

```bash
ceph-deploy --overwrite-conf config push tw061145 tw061154
```



 

最后在每个mon节点上，重启mon服务：

```bash
systemctl restart ceph-mon.target
```



 

完成后查看ceph状态，变成 `HEALTH_OK` 就可以了：

```bash
cluster 9dc6e787-661e-46bb-a2a3-32ad9811ea4a

​     health HEALTH_OK

​     monmap e2: 3 mons at {tw061132=10.33.15.11:6789/0,tw061145=10.33.15.19:6789/0,tw061154=10.33.15.28:6789/0}

​            election epoch 18, quorum 0,1,2 tw061132,tw061145,tw061154

​        mgr active: tw061145 standbys: tw061132, tw061154

​     osdmap e2426: 54 osds: 54 up, 54 in

​            flags sortbitwise,require_jewel_osds,require_kraken_osds

​      pgmap v671273: 6144 pgs, 3 pools, 38074 MB data, 12165 objects

​            164 GB used, 100405 GB / 100569 GB avail

​                6144 active+clean

  client io 560 kB/s wr, 0 op/s rd, 150 op/s wr
```



 

 

 

 
