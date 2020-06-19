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
    path('team/', views.team, name='team'),
    path('team/create/', views.create_team, name='create_team'),
    path('team/join/', views.team_join, name='team_join'),
    path('team/apply/<int:tid>/', views.team_apply, name='team_apply'),
    path('home/', views.home, name='home'),
]
