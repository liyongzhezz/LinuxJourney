# 通过dockerfile构建镜像



## 【实例】构建一个C语言镜像

这里使用c语言编写一个hello-world程序，然后编译成为一个可执行的程序用于构建镜像。



首先创建一个项目目录hello-world：

```bash
$ mkdir hello-world

$ cd hello-world
```



然后在目录中创建C语言程序：

```c
// vim hello.c

#include<stdio.h>
int main()
{
​    printf("hello docker\n");
}
```



下面编译C程序：

```bash
$ yum install -y gcc glibc-static glibc

$ gcc -static hello.c -o hello

# 执行结束后在当前目录多了一个可执行文件hello
```



通过Dockerfile创建image：

```dockerfile
// vim Dockerfile

FROM scratch

ADD hello /

CMD ["/hello"]
```

**注意这里FROM是scratch表明这是一个base image，即这个image没有基于任何镜像构建。**



```bash
$ docker build -t lyz/hello-world .

Sending build context to Docker daemon  868.9kB
Step 1/3 : FROM scratch
 ---> 
Step 2/3 : ADD hello /
 ---> b8cace4abdf5
Step 3/3 : CMD ["/hello"]
 ---> Running in 0a76cd9fe539
Removing intermediate container 0a76cd9fe539
 ---> 4f84297bebd6
Successfully built 4f84297bebd6
Successfully tagged lyz/hello-world:latest

$ docker image ls 

REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
lyz/hello-world     latest              4f84297bebd6        32 seconds ago      865kB
```



**可以看到，创建的docker image已经成功了。**

 

运行测试：

```bash
$ docker run lyz/hello-world

hello docker
```

> 通过这个镜像运行了一个容器，输出了hello docker，表名自己构建的容器成功了。

