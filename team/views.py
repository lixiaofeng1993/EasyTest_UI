from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from base.models import Team, TeamUsers, ValidationError, ModularTable
from base.models import Project as projects
from base.models import Keyword as keyword
from public.util import *
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.models import User
from public.helperPath import register_info_logic, change_info_logic
import logging

log = logging.getLogger('log')  # 初始化log


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


def register(request):
    if request.method == 'GET':
        return render(request, 'login/register.html')
    else:
        nick = request.POST.get('nick', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm', '')
        msg = register_info_logic(nick, email, password, confirm)
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


@login_required
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


@login_required
def team_go(request):
    if request.method == 'POST':
        tid = request.POST.get('tid')
        user_id = request.session['user_id']
        t = TeamUsers.objects.filter(team_id=tid).filter(user_id=user_id)
        status = 0
        if len(t) == 1:
            status = t[0].status
        return JsonResponse.AbnormalCheck('要先加入团队才能进入撒~~~', data={'status': status})


@login_required
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


@login_required
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


@login_required
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


@login_required
def team_apply(request, tid):
    if request.method == 'POST':
        apply_id = request.POST.get('apply_id')
        tu = get_model(TeamUsers, get=False, id=apply_id)
        tu.update(status=1)
        return JsonResponse.OK()
    tu = TeamUsers.objects.filter(team_id=tid).filter(status=0)
    return render(request, 'team/apply.html', {'join': tu, 'tid': tid})


@login_required
def team_join(request):
    if request.method == 'GET':
        return render(request, 'team/apply.html')
    else:
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


@login_required
def index(request, tid):
    request.session['tid'] = tid
    return render(request, "page/首页.html", {'tid': tid})


@login_required
def project(request):
    tid = request.session.get('tid', '')
    return render(request, "page/2项目管理.html", {'tid': tid})


@login_required
def project_config(request, project_id):
    p = get_model(projects, id=project_id)
    name = p.name if p else ""
    tid = request.session.get('tid', '')
    return render(request, "page/2项目管理--环境配置.html", {"projectId": project_id, "projectName": name, 'tid': tid})


@login_required
def page(request):
    tid = request.session.get('tid', '')
    return render(request, "page/3页面管理.html", {'tid': tid})


@login_required
def element(request):
    projectId = request.GET.get("projectId", "false")
    pageId = request.GET.get("pageId", "false")
    tid = request.session.get('tid', '')
    info = {"projectId": projectId, "pageId": pageId, 'tid': tid}
    return render(request, "page/4页面元素.html", info)


@login_required
def keyword(request):
    tid = request.session.get('tid', '')
    return render(request, "page/5关键字库.html", {'tid': tid})


@login_required
def keyword_create(request):
    tid = request.session.get('tid', '')
    return render(request, "page/5-1新建关键字.html")


@login_required
def keyword_edit(request, keyword_id):
    kw = get_model(keyword, id=keyword_id)
    projectId = kw.projectId if kw else 0
    p = get_model(project, id=projectId)
    projectName = p.name if projectId > 0 and p else "通用关键字封装"
    keywordName = kw.name if kw else ""
    tid = request.session.get('tid', '')
    return render(request, "page/5-2编辑关键字.html",
                  {"id": projectId, "projectName": projectName, "keywordId": keyword_id, "keywordName": keywordName,
                   'tid': tid})


@login_required
def testcase(request):
    tid = request.session.get('tid', '')
    return render(request, "page/6测试用例.html", {'tid': tid})


@login_required
def testcase_create(request):
    tid = request.session.get('tid', '')
    return render(request, "page/6-1新建测试用例.html", {'tid': tid})


@login_required
def testcase_edit(request, testcase_id):
    tid = request.session.get('tid', '')
    return render(request, "page/6-1编辑测试用例.html", {"testcaseId": testcase_id, 'tid': tid})


@login_required
def result(request):
    tid = request.session.get('tid', '')
    return render(request, "page/7测试结果.html", {'tid': tid})


@login_required
def result_see(request, result_id):
    tid = request.session.get('tid', '')
    return render(request, "page/7-1查看测试结果.html", {"id": result_id, 'tid': tid})


@login_required
def task(request):
    tid = request.session.get('tid', '')
    return render(request, "page/9任务管理.html", {'tid': tid})


@login_required
def loginConfig(request):
    tid = request.session.get('tid', '')
    return render(request, "page/8登录配置.html", {'tid': tid})


@login_required
def loginConfig_create(request):
    tid = request.session.get('tid', '')
    return render(request, "page/8-1新建登录配置.html", {'tid': tid})


@login_required
def loginConfig_edit(request, login_id):
    tid = request.session.get('tid', '')
    return render(request, "page/8-1编辑登录配置.html", {"id": login_id, 'tid': tid})


# @login_required
# def report(request, report_id):
#
#     return render(request, "page/report.html", {"report_id": report_id})


# 400
def bad_request(request, exception, template_name='error_page/400.html'):
    log.error('-------------------->400 error<--------------------')
    return render(request, template_name)


# 403
def permission_denied(request, exception, template_name='error_page/403.html'):
    log.error('-------------------->403 error<--------------------')
    return render(request, template_name)


# 404
def page_not_found(request, exception, template_name='error_page/404.html'):
    log.error('-------------------->404 error<--------------------')
    return render(request, template_name)


# 500
def server_error(exception, template_name='error_page/500.html'):
    log.error('-------------------->500 error<--------------------')
    return render(exception, template_name)


@login_required
def change_password(request):
    """
    修改密码
    :param request:
    :return:
    """
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        user = request.POST.get('user', '')

        msg = change_info_logic(new_password)
        if msg != 'ok':
            log.error('change password error：{}'.format(msg))
            return JsonResponse.BadRequest(msg)
        else:
            user = User.objects.get(username=user)
            user.set_password(new_password)
            user.save()
            log.info('用户：{} 修改密码为 {}'.format(user, new_password))
            return JsonResponse.OK('修改密码成功！')
