import time
import json
import requests

from login_falcon import login_falcon

def time_stamp_trans(format_time):
    '''时间转时间戳，接受 2019-03-11 15:23:04 格式的转换'''
    ts = time.strptime(format_time, "%Y-%m-%d %H:%M:%S")
    time_stamp = time.mktime(ts)

    return time_stamp


@login_falcon
def get_graph_history(obj):
    '''获取图表的历史记录'''
    if obj['code'] != 200:
        print('open-falcon 登陆失败')
        return obj['code']
    else:
        obj = obj['data']

    falcon_url = 'http://falcon.example.cn:8080/api/v1/graph/history'

    # 获取图表历史数据的变量
    step = 60   # 间隔
    start_time = int(time_stamp_trans('2019-08-26 18:00:00'))  # 开始时间戳
    hostnames = ['ws-gd-fs_10.10.30.253']                      # endpoint列表
    end_time = int(time_stamp_trans('2019-08-26 19:00:00'))    # 结束时间戳
    counters = ['switch1.if.OUT/ifName=G0/0/1']                # 监控项
    consol_fun = "AVERAGE"                                     # 取值方式：AVERAGE MAX MIN

    tokens = "{\"name\":\"" + obj['name'] + "\",\"sig\":\"" + obj['sig'] + "\"}"
    headers = {
        "Content-Type": "application/json",
        "Apitoken": tokens,
        'X-Forwarded-For': '127.0.0.1',
    }

    params = dict(step=step, start_time=start_time, hostnames=hostnames, end_time=end_time, counters=counters,
                  consol_fun=consol_fun)
    resp = requests.post(falcon_url, data=json.dumps(params), headers=headers)

    if resp.status_code == 200:
        return {'code': resp.status_code, 'data': resp.text}
    else:
        return {'code': resp.status_code, 'data': [], 'msg': resp.text}


if __name__ == '__main__':
    result = get_graph_history()

    if result['code'] != 200:
        print('获取历史数据失败, 原因：%s' % result['msg'])
    else:
        print(result['data'])