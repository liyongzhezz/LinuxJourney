import time
import json
import requests

from login_falcon import login_falcon

'''
自定义推送数据到open-falcon
前提是本机需要安装好falcon-agent，推送是调用falcon-agent的接口，再由falcon-agent推送到open-falcon

metric: 核心字段，代表这个采集项具体度量的是什么, 比如是cpu_idle、memory_free、qps
endpoint: 标明Metric的主体(属主)，如metric是cpu_idle，那么Endpoint就表示这是哪台机器的cpu_idle
timestamp: 表示汇报该数据时的时间戳，注意是整数，代表的是秒
value: 代表该metric在当前时间点的值，float64
step: 表示该数据采集项的汇报周期，这对于后续的配置监控策略很重要，必须明确指定。
counterType: 只能是COUNTER或者GAUGE二选一，前者表示该数据采集项为计时器类型，后者表示其为原值 (注意大小写)
    GAUGE：即用户上传什么样的值，就原封不动的存储
    COUNTER：指标在存储和展现的时候，会被计算为speed，即（当前值 - 上次值）/ 时间间隔
tags: 一组逗号分割的键值对, 对metric进一步描述和细化, 可以是空字符串. 比如idc=lg，比如service=xbox等，多个tag之间用逗号分割
'''


def push_data():
    timestamp = int(time.time())
    falcon_url = 'http://127.0.0.1:1988/v1/push'

    # 自定义推送数据

    payload = [
        {
            "endpoint": "test-push",
            "metric": "offline1",
            "timestamp": timestamp,
            "step": 60,
            "value": 1,
            "counterType": "GAUGE",
            "tags": "env=test,type=watch",
        },
        {
            "endpoint": "test-push",
            "metric": "offline2",
            "timestamp": timestamp,
            "step": 60,
            "value": 2,
            "counterType": "GAUGE",
            "tags": "env=dev,type=pc",
        },
    ]

    resp = requests.post(falcon_url, data=json.dumps(payload))
    if resp.status_code == 200:
    return {'code': resp.status_code, 'data': resp.text}


if __name__ == '__main__':
    result = push_data()

    if result['code'] != 200:
        print('推送数据失败，原因：%s' % result['data'])
    else:
        print(result['data'])
