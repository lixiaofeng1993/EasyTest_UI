from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages, auth
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Team
from public.get_model import get_model


def index(request):
    return render(request, 'base.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)  # 认证给出的用户名和密码
        if user is not None and user.is_active:  # 判断用户名和密码是否有效
            auth.login(request, user)
            request.session['user'] = username  # 跨请求的保持user参数
            response = HttpResponseRedirect('/base/team/')
            return response
        else:
            messages.add_message(request, messages.WARNING, '账户或者密码错误，请检查')
            return render(request, 'login/login.html')
    elif request.method == 'GET':
        return render(request, 'login/login.html')
    return render(request, 'login/login.html')


def team(request):
    te = get_model(Team, get=False)
    return render(request, 'team/team.html', {'tram': te})


def create_team(request):
    if request.method == 'POST':
        t = Team()
        t.name = request.POST.get('name', '')
        t.remark = request.POST.get('remarks', '')
        username = request.session['user']
        t.creator = get_model(User, username=username)
        try:
            t.clean()
        except ValidationError as error:
            return render(request, 'team/create.html', error.message_dict)
        try:
            t.save()
        except Exception as e:
            return render(request, 'team/create.html', {'error': e.args})
        return HttpResponseRedirect('/base/team/')
    return render(request, 'team/create.html')


def home(request):
    return render(request, 'base/home.html')
