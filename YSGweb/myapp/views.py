# encoding:utf-8
import json
import re
import hashlib
import time
import logging

from django.http import HttpResponse
from models import User, Promotion, PromotionBookList, UserFavourite
# from django.core import serializers
from django.views.decorators.http import require_POST

from django.views.decorators.csrf import csrf_exempt
from crawler import search_home_list_find, search_home_detail_find
from crawler import search_promotion_list_find, search_promotion_detail_find

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# =============================================================
_COOKIE_KEY = "web_app_for_mobile_client"
COOKIE_NAME = "app_session"
_RE_EMAIL = re.compile(r'^[a-zA-Z0-9\.\-_]+@[a-zA-Z0-9\-_]+(\.[a-zA-Z0-9\-_]+){1,4}$')
_RE_PHONE = re.compile(r'^(1[345678]\d{9})$')
_RE_SHA1 = re.compile(r'[0-9a-f]{1,40}$')


def json_response(data):
    return HttpResponse(
        json.dumps(data, ensure_ascii=False, encoding='utf-8'),
        content_type="application/json;charset=utf-8"
    )


def user_auth(request):
    print("check user: %s %s" % (request.method, request.path))
    request.user = None
    print(request.COOKIES)
    if COOKIE_NAME in request.COOKIES:
        cookie_str = request.COOKIES[COOKIE_NAME]
        user = cookie2user(cookie_str)
        print(user)
        if user:
            print("set current user: %s" % user.userName)
            request.user = user
            return True
    return False


def user2cookie(username, password, max_age):
    expires = str(int(time.time() + max_age))
    cookie_str = '%s-%s-%s-%s' % (username, password, expires, _COOKIE_KEY)
    cookie_list = [username, expires, hashlib.sha1(cookie_str.encode("utf-8")).hexdigest()]
    return "-".join(cookie_list)


def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        cookie_list = cookie_str.split("-")
        print(cookie_list)
        if len(cookie_list) != 3:
            return None
        username, expires, sha1s = cookie_list
        print(username)
        if int(expires) < time.time():
            return None
        # name:email, phone, name
        if _RE_EMAIL.match(username):
            user = User.objects.get(email=username)
        elif len(username) == 11 and _RE_PHONE.match(username):
            user = User.objects.get(phone=username)
        else:
            user = User.objects.get(userName=username)
        cookie_str = "%s-%s-%s-%s" % (username, user.password, expires, _COOKIE_KEY)
        if sha1s != hashlib.sha1(cookie_str.encode("utf-8")).hexdigest():
            logging.info("invalid sha1")
            return None
        return user
    except Exception as e:
        logging.exception(e)
        return None


def check_password(db_password, username, password):
    sha1 = hashlib.sha1()
    sha1.update(username.encode("utf-8"))
    sha1.update(b":")
    sha1.update(password.encode("utf-8"))
    if db_password != sha1.hexdigest():
        return False
    return True


def authenticate(username=None, password=None):
    if username:
        if _RE_EMAIL.match(username):
            try:
                users = User.objects.get(email=username)
                if check_password(users.password, username, password):
                    return users
            except User.DoesNotExist:
                return None
        elif len(username) == 11 and _RE_PHONE.match(username):
            try:
                users = User.objects.get(phone=username)
                if check_password(users.password, username, password):
                    return users
            except User.DoesNotExist:
                return None
        else:
            try:
                users = User.objects.get(userName=username)
                if check_password(users.password, username, password):
                    return users
            except User.DoesNotExist:
                return None
    else:
        return None


@require_POST
@csrf_exempt
def user_login(request):
    username = request.POST['name']
    password = request.POST['passwd']
    if username == "" or username.isspace():
        result = {"status": '1', "data": "username can't empty"}
        return json_response(result)
    if password == "" or password.isspace():
        result = {"status": '1', "data": "password can't be empty"}
        return json_response(result)
    user = authenticate(username=username, password=password)
    if user is not None:
        result = {"status": '0', "data": "user: %s login success" % username}
        response = json_response(result)
        response.set_cookie(COOKIE_NAME, user2cookie(username, user.password, 6220800), max_age=6220800, httponly=True)
        return response
    else:
        result = {"status": '1', "data": "invalid username or password"}
        return json_response(result)


@require_POST
@csrf_exempt
def user_register(request):
    username = request.POST['name']
    password = request.POST['passwd']
    email = request.POST['email']
    result = {"status": '2', "data": "invalid parameters"}
    if not username or not username.strip():
        result["data"] = "invalid username"
        return json_response(result)
    if not password:
        result["data"] = "invalid password"
        return json_response(result)
    if not email or not _RE_EMAIL.match(email):
        result["data"] = "invalid email"
        return json_response(result)
    user = User.objects.filter(userName=username)
    # need modify
    if not user:
        sha1_passwd = '%s:%s' % (username, password)
        try:
            newuser = User(
                userName=username,
                password=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                phone=request.POST['phone'],
                email=request.POST['email'],
                studentNo=request.POST['studentNo'],
                gender=request.POST['gender'],
                school=request.POST['school']
            )
            newuser.save()
            result["status"] = '0'
            result["data"] = "register success"
            response = json_response(result)
            response.set_cookie(
                COOKIE_NAME,
                user2cookie(username, newuser.password, 6220800),
                max_age=6220800,
                httponly=True
            )
            return response
        except Exception as e:
            logging.info(e)
            result['data'] = "exception: %s" % e
            return json_response(result)
    result['data'] = "username have been registered"
    return json_response(result)


@csrf_exempt
def user_logout(request):
    result = {'status': '0', 'data': 'logout success'}
    response = HttpResponse(json.dumps(result, ensure_ascii=False), content_type="application/json")
    response.set_cookie(COOKIE_NAME, "-deleted-", max_age=0, httponly=True)
    return response


# =============================================================
def get_all_user(request):
    # res = HttpResponse(serializers.serialize("json", User.objects.all()))
    user = User.objects.all()
    user_list = []
    for u in user:
        user_list.append(u.to_dict())
    res3 = json_response(user_list)
    return res3


def promotion_list(request):
    promotion_set = Promotion.objects.all()
    promotionlist = []
    for promotion in promotion_set:
        promotionlist.append(promotion.to_dict())
    return json_response(promotionlist)


def promotion_detail(request):
    """
    首先查找收藏，若没有收藏，直接根据promotionID从数据库中查找相应书籍；
    首先只是返回前20本书。
    """
    promotion_id = request.GET["promotionID"].encode('utf-8')
    book_list = PromotionBookList.objects.filter(promotionID=promotion_id)
    res = {'promotionID': promotion_id, 'book': 'invalid promotionID or empty book list'}
    promotionbooklist = []
    if len(book_list) <= 0:
        return json_response(res)
    else:
        for book in book_list:
            temp_dict = book.to_dict()
            # 不返回promotionID，id
            del temp_dict['promotionID']
            del temp_dict['id']
            promotionbooklist.append(temp_dict)
        res['book'] = promotionbooklist
        return json_response(res)


# ===============================================================================================
# just return bookName
# problem: request.user.  to be solve.
def get_favourite(request):
    favourite_list = []
    if not user_auth(request):
        result = {"status": '1', "data": "user need login"}
        return json_response(result)
    userfavourite = UserFavourite.objects.filter(userName=request.user.userName)
    if len(userfavourite) == 0:
        result = {"status": '0', "data": "UserFavourite is empty"}
        return json_response(result)
    for favourite in userfavourite:
        favourite_list.append(dict(bookname=favourite.bookName))
    result = {"username": request.user.userName, "favourite_list": favourite_list}
    return json_response(result)


# 添加收藏列表（一本一本的添加和一个列表添加有什么区别？）
# 若添加列表，则{"book_list":{}}
@require_POST
def add_favourite(request):
    if not user_auth(request):
        result = {"status": '1', "data": "user need login"}
        return json_response(result)
    isbn = ""
    if "ISBN" in request.POST:
        isbn = request.POST['ISBN']
    bookname = request.POST['bookname']
    favourite = UserFavourite.objects.filter(userName=request.user.userName, bookName=bookname)
    if len(favourite) > 0:
        result = {"status": '1',
                  "data": "book %s have been added before by %s." % (bookname, request.user.userName)}
        return json_response(result)
    new_favourite = UserFavourite(
        userName=request.user.userName,
        bookName=bookname,
        ISBN=isbn
    )
    new_favourite.save()
    result = {"status": '0', "data": "add success"}
    return json_response(result)


@require_POST
def delete_favourite(request):
    result = {"status": "0", "data": "delete success"}
    if not user_auth(request):
        result['status'] = '1'
        result['data'] = "user need login"
        return json_response(result)
    bookname = request.POST['bookname']
    favourite = UserFavourite.objects.filter(userName=request.user.userName, bookName=bookname)
    if len(favourite) <= 0:
        result['status'] = '0'
        result['data'] = "book %s no exist" % bookname
        return json_response(result)
    favourite.delete()
    return json_response(result)


# ===============================================================================================


def search_promotion_list(request):
    bookName = request.GET["bookName"] #支持中文搜索
    promotionID = request.GET["promotionID"]
    return HttpResponse(search_promotion_list_find(bookName, promotionID))

def search_promotion_detail(request):
    promotionBookDetailLink = request.GET["promotionBookDetailLink"]
    return HttpResponse(search_promotion_detail_find(promotionBookDetailLink))

def search_home_list(request):
    bookName = request.GET["bookName"].encode("utf-8") #支持中文搜索
    return HttpResponse(search_home_list_find(bookName))

def search_home_detail(request):
    bookSubject = request.GET["bookSubject"]
    return HttpResponse(search_home_detail_find(bookSubject))


@require_POST
def delete_shopping_list(request):
    pass


def get_shopping_list(request):
    pass
