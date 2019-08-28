import requests

from login_falcon import login_falcon


@login_falcon
def get_user_list(obj):
    '''获取系统中的用户列表'''
    if obj['code'] != 200:
        print('open-falcon 登陆失败')
        return obj['code']
    else:
        obj = obj['data']

    falcon_url = 'http://falcon.example.cn:8080/api/v1/user/users'

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


if __name__ == '__main__':
    result = get_user_list()

    if result['code'] != 200:
        print('获取用户列表失败')
    else:
        print(result['data'])
