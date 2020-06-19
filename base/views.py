from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages, auth
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Team, TeamUsers
from public.util import *


def index(request):
    return render(request, 'base.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)  # 认证给出的用户名和密码
        if user is not None and user.is_active:  # 判断用户名和密码是否有效
            auth.login(request, user)
            user_id = get_model(User, username=username).id
            request.session['user'] = username  # 跨请求的保持user参数
            request.session['user_id'] = user_id
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
        user_id = request.session['user_id']
        t.creator = get_model(User, id=user_id)
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


def team_apply(request, tid):
    if request.method == 'POST':
        apply_id = request.POST.get('apply_id')
        tu = get_model(TeamUsers, get=False, id=apply_id)
        tu.update(status=1)
        return JsonResponse.OK()
    tu = TeamUsers.objects.filter(team_id=tid).filter(status=0)
    return render(request, 'team/apply.html', {'join': tu, 'tid': tid})


def team_join(request):
    if request.method == 'POST':
        tid = request.POST.get('tid', '')
        super_id = get_model(Team, id=tid).creator_id
        user_id = request.session['user_id']
        if super_id != user_id:
            if TeamUsers.objects.filter(team_id=tid).filter(user_id=user_id):
                return JsonResponse.AbnormalCheck('申请已提交，等待管理员审核中~~~')
            else:
                tu = TeamUsers()
                tu.team = get_model(Team, id=tid)
                tu.user = get_model(User, id=user_id)
                try:
                    tu.save()
                except Exception as e:
                    return JsonResponse.AbnormalCheck('申请失败！{}'.format(e))
                return JsonResponse.OK('申请成功，等待管理员审核中~~~')
        else:
            return JsonResponse.SkipLink()


def home(request):
    return render(request, 'base/home.html')
