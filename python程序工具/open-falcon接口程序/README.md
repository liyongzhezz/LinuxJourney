# open-falcon+接口程序

通过falcon+ api，实现程序中操作open-falcon的数据



最核心的是 [login_falcon.py](https://github.com/liyongzhezz/LinuxJourney/blob/master/python%E7%A8%8B%E5%BA%8F%E5%B7%A5%E5%85%B7/open-falcon%E6%8E%A5%E5%8F%A3%E7%A8%8B%E5%BA%8F/%E7%99%BB%E5%BD%95%E7%9B%B8%E5%85%B3.md#%E7%99%BB%E5%BD%95open-falcon) 文件，它通过一个用户（一般为root）登录系统，获取一个sig，这个参数作为后面程序中认证的重要参数来使用。

> 如果没有退出，这个sig值是不会变的



- login_falcon.py：登录falcon
- get_user_list.py：获取用户列表
- get_graph_history.py：获取图表历史数据
- get_endpoints.py：获取endpoint
- get_alarm.py：获取历史报警
- push_data.py：推送数据到open-falcon