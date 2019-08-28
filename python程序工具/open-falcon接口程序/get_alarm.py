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
def get_alarm(obj):
    '''获取报警信息'''
    if obj['code'] != 200:
        print('open-falcon 登陆失败')
        return obj['code']
    else:
        obj = obj['data']

    falcon_url = 'http://falcon.example.cn:8080/api/v1/alarm/eventcases'

    tokens = "{\"name\":\"" + obj['name'] + "\",\"sig\":\"" + obj['sig'] + "\"}"
    headers = {
        "Content-Type": "application/json",
        "Apitoken": tokens,
        'X-Forwarded-For': '127.0.0.1',
    }

    # 获取报警变量
    limit = 0   # 获取报警的个数，0表示不限制个数
    status = ""  # 报警状态，为空表示获取所有状态的报警
    start_tme = int(time_stamp_trans('2019-08-15 00:00:00'))   # 开始时间戳
    end_time = int(time_stamp_trans('2019-08-28 11:00:00'))    # 结束时间戳,

    tokens = "{\"name\":\"" + obj['name'] + "\",\"sig\":\"" + obj['sig'] + "\"}"
    headers = {
        "Content-Type": "application/json",
        "Apitoken": tokens,
        'X-Forwarded-For': '127.0.0.1',
    }

    params = dict(limit=limit, status=status, startTime=start_tme, endTime=end_time)
    resp = requests.post(falcon_url, data=json.dumps(params), headers=headers)

    if resp.status_code == 200:
        return {'code': resp.status_code, 'data': resp.text}
    else:
        return {'code': resp.status_code, 'data': [], 'msg': resp.text}


if __name__ == '__main__':
    result = get_alarm()

    if result['code'] != 200:
        print('获取告警数据失败, 原因：%s' % result['msg'])
    else:
        print(result['data'])
