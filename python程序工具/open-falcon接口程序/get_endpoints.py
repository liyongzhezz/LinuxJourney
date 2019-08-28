import requests

from login_falcon import login_falcon

'''
获取endpoints
'''

@login_falcon
def get_endpoint(obj):
    # 查询参数
    regx = "^ws.*$"  # 使用 regex 查询字符
    falcon_url = 'http://falcon.example.cn:8080/api/v1/graph/endpoint?q=' + regx

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
    if resp.status_code == 200:
        return {'code': resp.status_code, 'data': resp.text}
    else:
        return {'code': resp.status_code, 'data': []}

if __name__== '__main__':
    result = get_endpoint()

    if result['code'] != 200:
        print('获取endpoint列表失败')
    else:
        print(result['data'])