#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020-06-16 17:24
# @Author  : lixiaofeng
# @Site    : 
# @File : urls.py
# @Software: PyCharm

from django.urls import path
from base import views

app_name = "base"
urlpatterns = [
    path('home/<int:tid>/', views.home, name='home'),
]
