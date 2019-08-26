# open-falcon+接口程序

通过falcon+ api，实现程序中操作open-falcon的数据



最核心的是 login_falcon.py 文件，它通过一个用户（一般为root）登录系统，获取一个sig，这个参数作为后面程序中认证的重要参数来使用。

> 如果没有退出，这个sig值是不会变的