import json
import requests

from login_falcon import login_falcon

'''
获取所有dashboard信息
'''

@login_falcon
def get_dashboard(obj):
    falcon_url = 'http://falcon.example.cn:8080/api/v1/dashboard/screens'

    if obj['code'] != 200:
        print('open-falcon 登陆失败')
        return obj['code']
    else:
        obj = obj['data']

    tokens = "{\"name\":\"" + obj['name'] + "\",\"sig\":\"" + obj['sig'] + "\"}"
    headers = {
        "Content-Type": "application/json",
        "Apitoken": tokens,
        'X-Forwarded-For': '127.0.0.1',
    }
    resp = requests.get(falcon_url, headers=headers)
    return {'code': resp.status_code, 'data': resp.text}


if __name__== '__main__':
    result = get_dashboard()

    if result['code'] != 200:
        print('获取dashboard列表失败')
    else:
        print(result['data'])
