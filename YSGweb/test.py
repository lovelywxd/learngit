# coding: UTF-8
import requests

payload = {
    # "bookname": "wxd12",
    'name': 'wxd5',
    'passwd': '123126dd'
    # 'phone': '131665529',
    # 'email': '81266664@163.com',
    # 'studentNo': '1221212121',
    # 'gender': '1',
    # 'school': '电子科技大学'
    }

# URL = "http://127.0.0.1:8000/user/register/"
URL = "http://127.0.0.1:8000/user/login/"
# URL = "http://192.168.1.100:8000/favourite/delete/"
# URL = "http://192.168.1.100:8000/favourite/list/"
# Cookie app_session=wxd5-1473407507-e7b4c908d0b938e7641127ee09f9e0989b3cd43f for 127.0.0.1
# cookies = dict(app_session="wxd5-1473407507-e7b4c908d0b938e7641127ee09f9e0989b3cd43f")
res = requests.post(URL, payload)
# res = requests.post(URL, data=payload, cookies=cookies)

# print(res.cookies)
print(res.text)
