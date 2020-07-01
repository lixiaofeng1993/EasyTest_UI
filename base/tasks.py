import json
import random
from datetime import datetime
from faker import Faker
from celery.task import task
from djcelery.models import PeriodicTask
from EasyTest_UI.PageObject.base_page import PageObject
from public.util import get_model
from public.util import remove_logs
from base.models import *

faker = Faker('zh_CN')


# 自定义要执行的task任务


@task
def SplitTask(result_id, status=False):
    result = Result.objects.get(id=result_id)
    result.status = 20
    result.save()
    parameter = json.loads(result.parameter) if result.parameter else []
    browsers = json.loads(result.browsers) if result.environments else [1]
    environments = json.loads(result.environments) if result.environments else []
    for browser in browsers:
        if environments:
            for environmentId in environments:
                if parameter:
                    for params in parameter:
                        for k, v in params.items():
                            if v and isinstance(v, str):
                                if '#time#' in v:
                                    v = v.replace('#time#',
                                                  time.strftime('%Y%m%d', time.localtime(time.time())))
                                if '#random_num#' in v:
                                    v = v.replace('#random_num#', str(random.randint(100000, 99999999)))
                                if '#null#' == v:
                                    v = None
                                if '#logo#' == v:
                                    v = "/home/Atp/logo.png"
                                if '#random_text#' in v:
                                    v = v.replace('#random_text#', faker.text(5))
                                params[k] = v
                        if status:
                            sr = SplitResult.objects.create(environmentId=environmentId, browserId=browser,
                                                            resultId=result.id, again=1,
                                                            parameter=json.dumps(params, ensure_ascii=False),
                                                            expect=params.get('expect', True))
                        else:
                            sr = SplitResult.objects.create(environmentId=environmentId, browserId=browser,
                                                            resultId=result.id,
                                                            parameter=json.dumps(params, ensure_ascii=False),
                                                            expect=params.get('expect', True))
                        SplitTaskRunning.delay(sr.id)
                else:
                    if status:
                        sr = SplitResult.objects.create(environmentId=environmentId, browserId=browser,
                                                        resultId=result.id, again=1,
                                                        parameter={}, expect=True)
                    else:
                        sr = SplitResult.objects.create(environmentId=environmentId, browserId=browser,
                                                        resultId=result.id,
                                                        parameter={}, expect=True)
                    SplitTaskRunning.delay(sr.id)
        else:
            if parameter:
                for params in parameter:
                    for k, v in params.items():
                        if v and isinstance(v, str):
                            if '#time#' in v:
                                v = v.replace('#time#',
                                              time.strftime('%Y%m%d', time.localtime(time.time())))
                            if '#random_num#' in v:
                                v = v.replace('#random_num#', str(random.randint(100000, 99999999)))
                            if '#null#' == v:
                                v = None
                            if '#logo#' == v:
                                v = "/home/Atp/logo.png"
                            if '#random_text#' in v:
                                v = v.replace('#random_text#', faker.text(5))
                            params[k] = v
                    if status:
                        sr = SplitResult.objects.create(environmentId=0, browserId=browser, resultId=result.id,
                                                        parameter=json.dumps(params, ensure_ascii=False), again=1,
                                                        expect=params.get('expect', True))
                    else:
                        sr = SplitResult.objects.create(environmentId=0, browserId=browser, resultId=result.id,
                                                        parameter=json.dumps(params, ensure_ascii=False),
                                                        expect=params.get('expect', True))
                    SplitTaskRunning.delay(sr.id)
            else:
                if status:
                    sr = SplitResult.objects.create(environmentId=0, browserId=browser, resultId=result.id, again=1,
                                                    parameter={}, expect=True)
                else:
                    sr = SplitResult.objects.create(environmentId=0, browserId=browser, resultId=result.id,
                                                    parameter={}, expect=True)
                SplitTaskRunning.delay(sr.id)
    SplitTaskRan.delay(result_id)


@task
def SplitTaskRan(result_id):
    result = Result.objects.get(id=result_id)
    while len(SplitResult.objects.filter(resultId=result.id, status__in=[10, 20])) > 0:
        time.sleep(1)
    split_list = SplitResult.objects.filter(resultId=result.id)
    for split in split_list:
        expect = split.expect
        result_ = True if split.status == 30 else False
        if expect != result_:
            result.status = 40
            result.save()
            return
    result.status = 30
    result.save()
    return


@task
def SplitTaskRunning(splitResult_id):
    split = SplitResult.objects.get(id=splitResult_id)
    result_ = Result.objects.get(id=split.resultId)
    steps = json.loads(result_.steps) if result_.steps else []
    parameter = json.loads(split.parameter) if split.parameter else {}
    checkType = result_.checkType
    checkValue = result_.checkValue
    checkText = result_.checkText
    selectText = result_.selectText
    beforeLogin = json.loads(result_.beforeLogin) if result_.beforeLogin else []
    split.status = 20
    split.save()
    split.startTime = timezone.now()
    environment = get_model(Environment, id=split.environmentId)
    host = environment.host if environment and environment.host else ''
    driver = None
    make_params = {}
    step_num = 0
    error_name = ""
    now = datetime.utcnow().strftime('%Y-%m-%d %H-%M-%S-%f')[:-1]
    img_path = os.path.join(settings.MEDIA_ROOT, now + ".png")
    try:
        driver = Browser.objects.get(id=split.browserId).buid(host)
    except Exception as e:
        split.status = 40
        split.remark = '浏览器初始化失败！{}'.format(e)
        split.finishTime = timezone.now()
        split.save()
        if driver:
            driver.quit()
        return
    if beforeLogin and len(beforeLogin) > 0:
        for bl in beforeLogin:
            login = get_model(LoginConfig, id=bl)
            loginCheckType = login.checkType
            loginCheckValue = login.checkValue
            loginCheckText = login.checkText
            loginSelectText = login.selectText
            if not login:
                split.loginStatus = 3
                split.status = 50
                split.remark = "找不到登陆配置,id=" + str(bl)
                split.finishTime = timezone.now()
                split.save()
                if driver:
                    driver.quit()
                log.error(split.remark)
                return
            loginSteps = json.loads(login.steps) if login.steps else []
            loginParameter = {}
            if environment:
                environmentLogin = get_model(EnvironmentLogin, loginId=bl, environmentId=environment.id)
                if environmentLogin:
                    loginParameter = json.loads(environmentLogin.parameter) if environmentLogin.parameter else {}
            for loginStep in loginSteps:
                try:
                    Step(loginStep.get("keywordId"), loginStep.get("values")).perform(driver, loginParameter, host)
                except Exception as e:
                    split.loginStatus = 2
                    split.status = 40
                    try:
                        driver.save_screenshot(img_path)
                        split.error_name = now + ".png"
                    except Exception as msg:
                        log.warning("页面加载超时：{}".format(msg))
                    split.step_num = 777  # 页面加载超时异常，无法截图
                    split.remark = "初始化登陆失败</br>登陆名称={}, </br>错误信息={}".format(login.name, e)
                    split.finishTime = timezone.now()
                    split.save()
                    if driver:
                        driver.quit()
                    log.error(split.remark)
                    return
            if loginCheckType:
                time.sleep(2)
                if loginCheckType == Check.TYPE_URL:
                    if not driver.current_url.endswith(str(loginCheckValue)):
                        split.loginStatus = 2
                        split.status = 40
                        driver.save_screenshot(img_path)
                        split.step_num = 888
                        split.error_name = now + ".png"
                        split.remark = "初始化登陆失败</br>登陆名称=" + login.name + " , </br>错误信息=登录断言不通过"
                        split.finishTime = timezone.now()
                        split.save()
                        if driver:
                            driver.quit()
                        log.error(split.remark)
                        return
                elif loginCheckType == Check.TYPE_ELEMENT:
                    element = loginCheckValue
                    if str(loginCheckValue).isdigit():
                        element = get_model(Element, id=loginCheckValue)
                    try:
                        PageObject().find_element(driver, element)
                    except:
                        split.loginStatus = 2
                        split.status = 40
                        driver.save_screenshot(img_path)
                        split.step_num = 888
                        split.error_name = now + ".png"
                        split.remark = "初始化登陆失败[ 登陆名称:" + login.name + " , 错误信息：断言不通过"
                        split.finishTime = timezone.now()
                        split.save()
                        if driver:
                            driver.quit()
                        log.error(split.remark)
                        return
        else:
            split.loginStatus = 1
    index = 1
    for step in steps:
        values = step.get("values", [])
        keyword_id = step.get("keywordId")
        try:
            if "make" in str(values):
                for key in values:
                    if key.get("value", "").isdigit():
                        element = key["value"]
                        element = get_model(Element, id=int(element))
                    if key.get("key", "") == "make":
                        PageObject().find_element(driver, element)
                        make_text = PageObject().get_text(element)
                        log.info("提取的文本是：{}".format(make_text))
                        make_key = key.get("value")
                        make_params.update({make_key: make_text})
            for key in values:
                if key.get("value", "") in make_params.keys():
                    log.info("把提取的文本，赋值给需要输入的值：{}".format(make_params[key["value"]]))
                    key["value"] = make_params[key["value"]]
            Step(keyword_id, values).perform(driver, parameter, host)
            index = index + 1
        except RuntimeError as re:
            split.status = 40
            driver.save_screenshot(img_path)
            split.step_num = index
            split.error_name = now + ".png"
            split.remark = "测试用例执行第" + str(index) + "步失败，错误信息:" + str(re.args)
            split.finishTime = timezone.now()
            split.save()
            if driver:
                driver.quit()
            log.error(split.remark)
            return
        except Exception as info:
            split.status = 40
            driver.save_screenshot(img_path)
            split.step_num = index
            split.error_name = now + ".png"
            split.remark = "执行测试用例第" + str(index) + "步发生错误，请检查测试用例:" + str(info.args)
            split.finishTime = timezone.now()
            split.save()
            if driver:
                driver.quit()
            log.error(split.remark)
            return
    remark = '测试用例未设置断言,建议设置'
    time.sleep(2)
    if checkType:
        if checkType == Check.TYPE_URL:
            TestResult = driver.current_url.endswith(checkValue)
            if not TestResult:
                if not split.expect:
                    remark = '测试通过'
                else:
                    driver.save_screenshot(img_path)
                    step_num = 999
                    error_name = now + ".png"
                    remark = '测试不通过,预期结果为["' + checkValue + '"], 但实际结果为["' + driver.current_url + '"]'
            else:
                if split.expect:
                    remark = '测试通过'
                else:
                    driver.save_screenshot(img_path)
                    step_num = 999
                    error_name = now + ".png"
                    remark = '测试不通过,预期结果为["' + checkValue + '"], 但实际结果为["' + driver.current_url + '"]'
        elif checkType == Check.TYPE_ELEMENT:
            element = checkValue
            expect_text = checkText
            select_text = selectText
            if str(checkValue).isdigit():
                element = get_model(Element, id=int(element))
            try:
                PageObject().find_element(driver, element)
                actual_text = PageObject().find_element(driver, element).text
                if select_text == 'all':
                    if expect_text == actual_text:
                        TestResult = True
                    else:
                        TestResult = False
                    if TestResult:
                        if split.expect:
                            remark = '测试通过，预期断言值完全匹配实际断言值。'
                        else:
                            driver.save_screenshot(img_path)
                            step_num = 999
                            error_name = now + ".png"
                            remark = '测试不通过，预期结果失败，但实际结果是成功。'
                    else:
                        driver.save_screenshot(img_path)
                        step_num = 999
                        error_name = now + ".png"
                        if not split.expect:
                            remark = '测试通过，预期结果失败，实际结果也是失败。'
                        else:
                            remark = '测试不通过，预期结果为["' + expect_text + '"]，但实际结果为["' + actual_text + '"]'
                else:
                    if expect_text in actual_text:
                        TestResult = True
                    else:
                        TestResult = False
                    if TestResult:
                        if split.expect:
                            remark = '测试通过，预期断言值包含匹配实际断言值。'
                        else:
                            driver.save_screenshot(img_path)
                            step_num = 999
                            error_name = now + ".png"
                            remark = '测试不通过，预期结果失败，但实际结果是成功。'
                    else:
                        driver.save_screenshot(img_path)
                        step_num = 999
                        error_name = now + ".png"
                        if not split.expect:
                            remark = '测试通过，预期结果失败，实际结果也是失败。'
                        else:
                            remark = '测试不通过，预期结果为["' + expect_text + '"]，但实际结果为["' + actual_text + '"]'
            except:
                TestResult = False
                driver.save_screenshot(img_path)
                step_num = 999
                error_name = now + ".png"
                remark = '当前元素定位已改变，请及时更新定位！'

    if driver:
        driver.quit()
    split.status = 30 if TestResult else 40
    split.remark = remark
    split.finishTime = timezone.now()
    split.step_num = step_num
    split.error_name = error_name
    split.save()
    log.error(remark)
    return


@task
def timingRunning(*args, **kwargs):
    if kwargs:
        name = kwargs["name"] if kwargs["name"] else None
        periodic = PeriodicTask.objects.get(name__exact=name)
        browsers = kwargs["browsers"] if kwargs["browsers"] else []
        testcases = kwargs["testcases"] if kwargs["testcases"] else []
        result_id_list = []
        for tc in testcases:
            environments = tc.get("environments", [])
            tc = get_model(TestCase, id=tc.get("id", 0))
            r = Result.objects.create(projectId=tc.projectId, testcaseId=tc.id, checkValue=tc.checkValue,
                                      checkType=tc.checkType, checkText=tc.checkText, selectText=tc.selectText,
                                      title=name, beforeLogin=tc.beforeLogin,
                                      steps=tc.steps, parameter=tc.parameter,
                                      browsers=json.dumps(browsers, ensure_ascii=False),
                                      environments=json.dumps(environments, ensure_ascii=False), taskId=periodic.id)
            result_id_list.append(str(r.id))
            SplitTask.delay(r.id)
        tr = TaskRelation.objects.create(result_id_list=json.dumps(result_id_list), result_id=result_id_list[0])
        tr.save()


class Step:
    def __init__(self, keyword_id, values):
        self.keyword = get_model(Keyword, id=keyword_id)
        self.params = [Params(value) for value in values]

    def perform(self, driver, parameter, host):
        if self.keyword.type == 1:
            values = list()
            for p in self.params:
                if p.isParameter:
                    if p.Type == Params.TYPE_ELEMENT:
                        v = Element.objects.get(id=parameter.get(p.value, None))
                    else:
                        v = parameter.get(p.value, None)
                elif p.Type == Params.TYPE_ELEMENT:
                    v = Element.objects.get(id=p.value)
                else:
                    v = p.value
                if self.keyword.method == 'open_url' and not ('http://' in v or 'https://' in v):
                    v = host + v
                values.append(v)
            try:
                self.sys_method__run(driver, tuple(values))
            except:
                raise
        elif self.keyword.type == 2:
            steps = json.loads(self.keyword.steps)
            for pa in self.params:
                if not pa.isParameter:
                    if pa.Type == Params.TYPE_ELEMENT:
                        parameter[pa.key] = Element.objects.get(id=pa.value)
                    else:
                        parameter[pa.key] = pa.value
            for step in steps:
                try:
                    Step(step.get("keywordId"), step.get("values")).perform(driver, parameter, host)
                except:
                    raise

    def sys_method__run(self, driver, value):
        package = __import__(self.keyword.package, fromlist=True)
        clazz = getattr(package, self.keyword.clazz)
        setattr(clazz, "driver", driver)
        method = getattr(clazz, self.keyword.method)

        def running(*args):
            try:
                c = clazz()
                para = (c,)
                args = para + args[0]
                method(*args)
            except:
                raise

        try:
            running(value)
        except Exception as e:
            log.error(e)
            raise


@task
def delete_logs():
    log.info('remove logs------->删除过期日志中<--------------')
    logs_path = os.path.join(settings.BASE_DIR, 'logs')
    pic_path = os.path.join(settings.MEDIA_ROOT)
    logs_num = remove_logs(logs_path)
    pic_num = remove_logs(pic_path)
    total_num = logs_num + pic_num
    if total_num == 0:
        log.info('remove logs------->没有要删除的文件.<--------------')
    else:
        log.info('remove logs------->删除过期日志文件数量：{}<--------------'.format(total_num))
