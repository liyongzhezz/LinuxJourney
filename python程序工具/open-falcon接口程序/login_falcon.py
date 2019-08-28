import json
import requests

'''
登录open-falcon，获取sig
'''


class login_falcon(object):
    def __init__(self, func):
        self._func = func

    def __call__(self):
        open_falcon_url = "http://falcon.example.cn:8080/api/v1/user/login"
        user = 'root'
        password = 'password'
        param = dict(name=user, password=password)

        # 登录
        headers = {"Content-type": "application/json"}
        resp = requests.post(open_falcon_url, data=json.dumps(param), headers=headers)

        if resp.status_code == 200:
            data = json.loads(resp.text)
            return self._func({'code': 200, 'data': data})
        else:
            return self._func({'code': resp.status_code, 'data': []})

# 返回数据格式  {'sig': '26b54db2c4bb11e9881600163e02f2e9', 'name': 'root', 'admin': True}
