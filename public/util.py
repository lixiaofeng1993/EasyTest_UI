#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020-06-18 15:00
# @Author  : lixiaofeng
# @Site    : 
# @File : util.py
# @Software: PyCharm

from django.http import HttpResponse
import json


class JsonResponse(HttpResponse):
    def __init__(self, code=200, message="ok", data=None):
        from django.core.serializers.json import json
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


def get_model(model, get=True, *args, **kwargs):
    from django.db.models.base import ModelBase
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
