#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020-06-18 15:00
# @Author  : lixiaofeng
# @Site    : 
# @File : util.py
# @Software: PyCharm

from django.http import HttpResponse
from django.core.serializers.json import json
from django.db.models.base import ModelBase
from django.conf import settings
from datetime import datetime
import os, time, logging

log = logging.getLogger('log')  # 初始化log


class JsonResponse(HttpResponse):
    def __init__(self, code=200, message="ok", data=None):
        response = dict()
        response['code'] = code
        response['message'] = message
        response['data'] = data
        super(JsonResponse, self).__init__(json.dumps(response, ensure_ascii=False), content_type="application/json", )
        self["Access-Control-Allow-Origin"] = "*"
        self["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        self["Access-Control-Max-Age"] = "1000"
        self["Access-Control-Allow-Headers"] = "*"
        self["Accept"] = "*"

    @staticmethod
    def OK(message="ok", data=None):
        response = JsonResponse(200, message, data)
        return response

    @staticmethod
    def BadRequest(message="Bad request", data=None):
        response = JsonResponse(400, message, data)
        return response

    @staticmethod
    def Unauthorized(message="Unauthorized", data=None):
        return JsonResponse(401, message, data)

    @staticmethod
    def MethodNotAllowed(message="Method not allowed", data=None):
        return JsonResponse(405, message, data)

    @staticmethod
    def ServerError(message="Internal server error", data=None):
        return JsonResponse(500, message, data)

    @staticmethod
    def SkipLink(message="skip link", data=None):
        return JsonResponse(403, message, data)

    @staticmethod
    def AbnormalCheck(message="except check", data=None):
        return JsonResponse(999, message, data)


# 检查请求是否为Post请求
def post(fn):
    def request(*args, **kwargs):
        if args[0].method == 'POST':
            return fn(*args, **kwargs)
        else:
            return JsonResponse.MethodNotAllowed("请使用Post请求")

    return request


def get_request_body(request):
    try:
        content = request.body.decode()
        content = json.loads(request.body.decode("utf-8")) if content else {}
    except:
        raise ValueError
    return content


def get_model(model, get=True, *args, **kwargs):
    if isinstance(model, ModelBase):
        if get:
            try:
                return model.objects.get(*args, **kwargs)
            except:
                return None
        else:
            return model.objects.filter(*args, **kwargs)
    else:
        raise TypeError("model 没有继承 django.db.models.base.ModelBase")


def pagination_data(paginator, page, is_paginated):
    """
    牛掰的分页
    :param paginator:
    :param page:
    :param is_paginated:
    :return:
    """
    if not is_paginated:
        # 如果没有分页，则无需显示分页导航条，不用任何分页导航条的数据，因此返回一个空的字典
        return {}

    # 当前页左边连续的页码号，初始值为空
    left = []

    # 当前页右边连续的页码号，初始值为空
    right = []

    # 标示第 1 页页码后是否需要显示省略号
    left_has_more = False

    # 标示最后一页页码前是否需要显示省略号
    right_has_more = False

    # 标示是否需要显示第 1 页的页码号。
    # 因为如果当前页左边的连续页码号中已经含有第 1 页的页码号，此时就无需再显示第 1 页的页码号，
    # 其它情况下第一页的页码是始终需要显示的。
    # 初始值为 False
    first = False

    # 标示是否需要显示最后一页的页码号。
    # 需要此指示变量的理由和上面相同。
    last = False

    # 获得用户当前请求的页码号
    page_number = page.number

    # 获得分页后的总页数
    total_pages = paginator.num_pages

    # 获得整个分页页码列表，比如分了四页，那么就是 [1, 2, 3, 4]
    page_range = paginator.page_range

    if page_number == 1:
        # 如果用户请求的是第一页的数据，那么当前页左边的不需要数据，因此 left=[]（已默认为空）。
        # 此时只要获取当前页右边的连续页码号，
        # 比如分页页码列表是 [1, 2, 3, 4]，那么获取的就是 right = [2, 3]。
        # 注意这里只获取了当前页码后连续两个页码，你可以更改这个数字以获取更多页码。
        right = page_range[page_number:page_number + 2]

        # 如果最右边的页码号比最后一页的页码号减去 1 还要小，
        # 说明最右边的页码号和最后一页的页码号之间还有其它页码，因此需要显示省略号，通过 right_has_more 来指示。
        if right[-1] < total_pages - 1:
            right_has_more = True

        # 如果最右边的页码号比最后一页的页码号小，说明当前页右边的连续页码号中不包含最后一页的页码
        # 所以需要显示最后一页的页码号，通过 last 来指示
        if right[-1] < total_pages:
            last = True

    elif page_number == total_pages:
        # 如果用户请求的是最后一页的数据，那么当前页右边就不需要数据，因此 right=[]（已默认为空），
        # 此时只要获取当前页左边的连续页码号。
        # 比如分页页码列表是 [1, 2, 3, 4]，那么获取的就是 left = [2, 3]
        # 这里只获取了当前页码后连续两个页码，你可以更改这个数字以获取更多页码。
        left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]

        # 如果最左边的页码号比第 2 页页码号还大，
        # 说明最左边的页码号和第 1 页的页码号之间还有其它页码，因此需要显示省略号，通过 left_has_more 来指示。
        if left[0] > 2:
            left_has_more = True

        # 如果最左边的页码号比第 1 页的页码号大，说明当前页左边的连续页码号中不包含第一页的页码，
        # 所以需要显示第一页的页码号，通过 first 来指示
        if left[0] > 1:
            first = True
    else:
        # 用户请求的既不是最后一页，也不是第 1 页，则需要获取当前页左右两边的连续页码号，
        # 这里只获取了当前页码前后连续两个页码，你可以更改这个数字以获取更多页码。
        left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
        right = page_range[page_number:page_number + 2]

        # 是否需要显示最后一页和最后一页前的省略号
        if right[-1] < total_pages - 1:
            right_has_more = True
        if right[-1] < total_pages:
            last = True

        # 是否需要显示第 1 页和第 1 页后的省略号
        if left[0] > 2:
            left_has_more = True
        if left[0] > 1:
            first = True

    data = {
        'left': left,
        'right': right,
        'left_has_more': left_has_more,
        'right_has_more': right_has_more,
        'first': first,
        'last': last,
    }

    return data


def remove_logs(path):
    """
    到期删除日志文件
    :param path:
    :return:
    """
    if os.path.isdir(path):
        file_list = os.listdir(path)  # 返回目录下的文件list
        now_time = datetime.now()
        num = 0
        for file in file_list:
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                file_ctime = datetime(*time.localtime(os.path.getctime(file_path))[:6])
                if (now_time - file_ctime).days > 6:
                    try:
                        os.remove(file_path)
                        num += 1
                        log.info('------删除文件------->>> {}'.format(file_path))
                    except PermissionError as e:
                        log.warning('删除文件失败：{}'.format(e))
                        # if name not in file_path and "pie" in file_path:
                        #     try:
                        #         os.remove(file_path)
                        #         num += 1
                        #         log.info('------删除文件------->>> {}'.format(file_path))
                        #     except PermissionError as e:
                        #         log.warning('删除文件失败：{}'.format(e))
            else:
                log.info('文件夹跳过：{}'.format(file_path))
        return num
    else:
        pic_path = os.path.join(settings.MEDIA_ROOT, path)
        if os.path.isfile(pic_path):
            try:
                os.remove(pic_path)
                log.info('------删除文件------->>> {}'.format(pic_path))
            except PermissionError as e:
                log.warning('删除文件失败：{}'.format(e))
        else:
            log.warning('不是文件或者文件不存在：{}'.format(pic_path))
