# 集群规划

## 部署方式

采用ceph-deploy方式部署，ceph-deploy作为管理端单独在一个服务器上。



## 服务器规划

总计11台服务器，每个服务器有一个ssd盘作为journal挂载点，其余机械硬盘作为osd节点。mon节点由三台服务器组成，复用osd节点。

![](statics/servers.jpg)

