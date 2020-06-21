from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages, auth
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from base.models import Team, TeamUsers, ModularTable
from public.util import *


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
            response = HttpResponseRedirect('/team/')
            return response
        else:
            messages.add_message(request, messages.WARNING, '账户或者密码错误，请检查')
            return render(request, 'login/login.html')
    elif request.method == 'GET':
        return render(request, 'login/login.html')
    return render(request, 'login/login.html')


def register(request):
    if request.method == 'POST':
        nick = request.POST.get('nick', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm', '')
        msg = check_register(nick, email, password, confirm)
        if msg != 'ok':
            messages.add_message(request, messages.WARNING, msg)
            return render(request, 'login/register.html')
        User.objects.create_user(username=nick, password=password, email=email)
        user = auth.authenticate(username=nick, password=password)
        if user is not None:
            auth.login(request, user)
            request.session['user'] = nick  # 将session信息记录到浏览器
            user_ = User.objects.get(username=nick)
            request.session['user_id'] = user_.id  # 将session信息记录到浏览器
            response = redirect('/team/')
            return response
    return render(request, 'login/register.html')


def logout(request):
    """
    退出
    :param request:
    :return:
    """
    auth.logout(request)  # 退出登录
    response = HttpResponseRedirect('/login/')
    return response


@method_decorator(login_required, name='dispatch')
class TeamIndex(ListView):
    model = Team
    template_name = 'team/team.html'
    context_object_name = 'object_list'
    paginate_by = 5

    def dispatch(self, *args, **kwargs):
        return super(TeamIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        team_list = get_model(Team, get=False)
        return team_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        context.update({"page": self.page})
        return context


def team_go(request):
    if request.method == 'POST':
        tid = request.POST.get('tid')
        user_id = request.session['user_id']
        t = TeamUsers.objects.filter(team_id=tid).filter(user_id=user_id)
        status = 0
        if len(t) == 1:
            status = t[0].status
        return JsonResponse.AbnormalCheck('要先加入团队才能进入撒~~~', data={'status': status})


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
        tu = TeamUsers()
        tu.team_id = t.id
        tu.user_id = t.creator.id
        tu.status = 1
        try:
            tu.save()
        except Exception as e:
            return render(request, 'team/create.html', {'error': e.args})
        return HttpResponseRedirect('/team/')
    return render(request, 'team/create.html')


def team_edit(request, tid):
    if request.method == 'POST':
        t = get_model(Team, id=tid)
        t.name = request.POST.get('name', '')
        t.remark = request.POST.get('remarks', '')
        user_id = request.session['user_id']
        t.creator = get_model(User, id=user_id)
        try:
            t.clean()
        except ValidationError as error:
            return render(request, 'team/edit.html', error.message_dict)
        try:
            t.save()
        except Exception as e:
            return render(request, 'team/edit.html', {'error': e.args})
    te = get_model(Team, id=tid)
    user_id = request.session['user_id']
    mt = get_model(ModularTable, get=False)
    info = {'te': te, 'status': False, 'tid': tid, 'mt': mt}
    if te.creator.id == user_id:
        info['status'] = True
        return render(request, 'team/edit.html', info)
    else:
        return render(request, 'team/edit.html', info)


def team_modular(request, tid):
    if request.method == 'POST':
        mt = ModularTable()
        mt.id = request.POST.get('id', '')
        mt.model_name = request.POST.get('name', '')
        mt.url = request.POST.get('url', '')
        mt.Icon = request.POST.get('icon', '')
        mt.team_id = tid
        try:
            mt.clean()
        except ValidationError as error:
            return render(request, 'team/edit.html', error.message_dict)
        try:
            mt.save()
        except Exception as e:
            return render(request, 'team/edit.html', {'error': e.args})
    return redirect('/team/edit/{}/'.format(tid))


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
            status = 0
            tus = TeamUsers.objects.filter(team_id=tid).filter(user_id=user_id)
            if tus:
                for t in tus:
                    status = t.status
                if status == 0:
                    return JsonResponse.AbnormalCheck('申请已提交，等待管理员审核中~~~')
                else:
                    return JsonResponse.OK('申请已通过，赶快进入体验吧~~~')
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
