防火墙是工作在网络或者主机边缘，对进出的数据包根据定义的规则进行检查，并作出相应的处理的一套软件。



# 防火墙类型



## 包过滤型防火墙

功能： 在网络层和数据层处理数据包

特点：性能高，安全性不好



包过滤型防火墙又可分为：

- 简单包过滤：只根据数据包格式属性进行检测

- 带状态检测包过滤：可以根据连接状态进行检测，检查机制更安全可靠，效率较低





## 应用层网关防火墙

功能：对特定的应用层协议检查，甚至检查数据

特点：安全性高，性能不好





# Linux防火墙

Linux2.4内核内置iptables用于管理软件防火墙，其本身并不是防火墙，而是管理防火墙的用户空间工具，通过iptables进行规则的编写，并将正确的规则传递到内核控件的netfilter防火墙框架，就可以实现数据包的检测。



## 钩子函数

对于netfilter来讲有5个钩子函数（hook）或规则链，任何经过钩子函数的数据包都会被检查，没问题就放行，名字分别为：

- INPUT：到本机内部

- OUTPUT：从本机出去

- FORWARD：转发

- PREROUTING：路由前

- POSTROUTING：路由后



这几个规则链（钩子函数）都可以放置多个规则，所以写规则的时候要清楚在哪个链上做检查

 

## 防火墙功能

防火墙功能有：

- filter：过滤

- nat：转换

- mangle：更改（更改数据包的内容，ttl等）

- raw



检查顺序为：raw -->  mangle  -->  net  --> filter

 

PREROUTING支持：mangle，raw，net

INPUT支持：mangle，filter

OUTPUT支持：raw，mangel，nat，filter

FORWARD支持：mangle，filter

POSTROUTING支持：mangle，nat



filter处理动作：

- ACCEPT：通过	

- DROP：直接丢弃

- REJECT：拒绝，并返回拒绝信息



## 数据包流向

到本机：

​	prerouting -> input



转发：

​	prerouting -> forward -> postrouting



由本机发出：

​	output -> postrouting

 

## iptables命令语法格式

```bash
iptables [-t TABLE] COMMAND CHAIN [匹配标准] -j ACTION
```



-t:

​	raw

​	mangle

​	nat

​	filter：默认

 

COMMAND：对链或链中的规则进行管理操作。

​	对链中规则：

​		-A：追加

​		-I N：插入为第N条

​		-R N：替换第N条

​		-D N：删除第N条

 

​	对链：

​		-N：新建自定义链

​		-X：删除自定义的空链

​		-E：重命名一条自定义链

​		-F：清空指定链（不指定就清空表中所有链）

​		-P：设定链的默认策略

​		-Z：计数器置零（每条规则包括默认策略都有两个计数器，一个是被本规则匹配到的所有数据包的个数，另一个是被本规则匹配到的所有数据包的大小之和）

 

查看：

​	-L：查看

​		-v：详细信息

​		-vv：更详细信息

​		--line-numbers：显示规则行号

​		-x：显示计数器精确值

​		-n：不对地址和端口做名称反解，显示数字地址

 

## iptables服务

```/etc/sysconfig/iptables-config```：脚本配置文件

```/etc/sysconfig/iptables```：规则保存位置



操作iptables服务：

```bash
systemctl {start|stop|restart|save} iptables
```



## iptables 匹配

### 通用匹配

- -s：指定原地址（可以是单个ip，或者带掩码的网络地址，地址前加！表示取反）

- -d：指定目标地址（可以是单个ip，或者带掩码的网络地址，地址前加！表示取反）

- -p {icmp|tcp|udp}：指定协议

- -I INTERFACE：指定数据包流入接口

- -o INTERFACE：指定数据包流出接口



### 扩展匹配

隐式扩展

-p tcp

```--sport PORT[-PORT2]```：指定源端口

```--dport PORT[-PORT2]```：指定目标端口

```--tcp-flages```：指定tcp标志位



-p udp

```--sport PORT[-PORT2]```：指定源端口

```--dport PORT[-PORT2]```：指定目标端口



-p icmp	

```--icmp-type```：指定icmp类型

- 0：echo-reply

- 8：echo-request	

​	



显式扩展:

由netfilter扩展模块引入的新扩展，用于匹配条件，通常需要额外的专用扩展选项来定义。

​		

-m：指定模块，下边以比较知名的模块state为例，其用于状态监测：

```-m state```：状态：NEW，ESTABLISHED，RELATED（多个连接），INVALID

 

## iptables命令示例

禁ping：

```bash
iptables -t filter -A INPUT -s 172.16.0.0/16 -p icmp --icmp-type 8 -j DROP
```



拒绝除某网段外主机访问：

```bash
iptables -A INPIT -s ! 172.16.0.0/16 -d 172.16.100.1 -p tcp --dport 80 -j DROP
```



清除规则：

```bash
iptables -t filter -F INPUT
```



放行ssh服务：

```bash
iptables -t filter -A INPUT -s 0.0.0.0/0 -d 172.16.100.1 -p tcp --dport 22 -j ACCEPT

iptables -t filter -A OUTPUT -s 172.16.100.1 -d 0.0.0./0 -p tcp --sport 22 -j ACCEPT
```



修改默认策略：

```bash
iptables -t filter -P INPUT DROP
```



放行22端口只允许NEW和ESTABLISHD请求进入，ESTABLISHED请求出去：

```bash
iptables -t filter -A INPUT -s 0.0.0./0 -d 172.16.100.1 -p tcp --dport 22 -m state --state --state NEW,ESTABLISHED -j ACCEPT

iptables -t filter -A INPUT -s 0.0.0./0 -d 172.16.100.1 -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT
```

