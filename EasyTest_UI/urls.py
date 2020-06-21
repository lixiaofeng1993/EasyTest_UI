"""EasyTest_UI URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from base import views, urls
from team import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('team/', views.TeamIndex.as_view(), name='team'),
    path('team/go/', views.team_go, name='team_go'),
    path('team/create/', views.create_team, name='create_team'),
    path('team/join/', views.team_join, name='team_join'),
    path('team/apply/<int:tid>/', views.team_apply, name='team_apply'),
    path('team/edit/<int:tid>/', views.team_edit, name='team_edit'),
    path('team/modular/<int:tid>/', views.team_modular, name='team_modular'),
    path('base/', include(urls, 'base'), name='base'),
]
