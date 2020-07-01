from django.contrib.auth.models import User
import django.utils.timezone as timezone
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from public.helperPath import *
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from appium import webdriver as app
import subprocess

log = logging.getLogger('log')  # 初始化log


class Team(models.Model):
    name = models.CharField(max_length=20, null=False)
    remark = models.TextField(null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, default='lixiaofeng')
    update_time = models.DateTimeField('更新时间', auto_now=True)
    create_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'team'

    def clean(self):
        name = self.name.strip() if self.name else ""
        if 0 >= len(name) or len(name) > 20:
            raise ValidationError({'error': '无效的团队名称'})


class TeamUsers(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    status = models.IntegerField(default=0)  # 申请状态
    create_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'team_users'


class ModularTable(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, default=None)
    url = models.CharField(max_length=255)
    Icon = models.CharField(max_length=255)
    model_name = models.CharField(max_length=6)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = 'modular'

    def clean(self):
        name = self.model_name.strip() if self.model_name else ""
        if 0 >= len(name) or len(name) > 6:
            raise ValidationError({'error': '无效的模块名称'})


# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=20, null=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, default=None)
    remark = models.TextField(null=True)
    creator = models.CharField(max_length=20, null=False, default='lixiaofeng')
    createTime = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'project'

    def clean(self):
        name = self.name.strip() if self.name else ""
        if 0 >= len(name) or len(name) > 20:
            raise ValidationError({'name': '无效的项目名称'})


class Page(models.Model):
    # projectId = models.IntegerField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=20, null=False)
    remark = models.TextField(null=True)
    createTime = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'page'

    def clean(self):
        name = self.name.strip() if self.name else ""
        projectId = int(self.project.id) if self.project.id and str(self.project.id).isdigit() else 0
        if 0 >= len(name) or len(name) > 20:
            raise ValidationError({'name': '无效的页面名称'})
        if projectId < 1:
            raise ValidationError({'projectId': '无效的项目Id'})


class Element(models.Model):
    # projectId = models.IntegerField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, default=None)
    # pageId = models.IntegerField()
    name = models.CharField(max_length=20, null=False)
    remark = models.TextField(null=True)
    createTime = models.DateTimeField(default=timezone.now)
    BY_TYPES = ["id", "xpath", "link text", "partial link text", "name", "tag name", "class name", "css selector"]
    by = models.CharField(null=False, max_length=20)
    locator = models.CharField(max_length=200, null=False)

    class Meta:
        db_table = 'element'

    def __str__(self):
        return self.name

    def clean(self):
        name = self.name.strip() if self.name else ""
        locator = str(self.locator) if self.locator else ""
        by = str(self.by).lower() if self.by else ""
        # projectId = int(self.projectId) if str(self.projectId).isdigit() else 0
        pageId = int(self.page.id) if str(self.page.id).isdigit() else 0
        if 0 >= len(name) or len(name) > 20:
            raise ValidationError({'name': '无效的元素名称'})
        # if projectId < 1:
        #     raise ValidationError({'projectId': 'projectId'})
        if pageId < 1:
            raise ValidationError({'pageId': '无效的页面Id'})
        if not by in Element.BY_TYPES:
            raise ValidationError({'by': 'by'})
        if 0 >= len(locator) or len(locator) > 200:
            raise ValidationError({'locator': '无效的定位值'})


class Keyword(models.Model):
    __KEYWORD_TYPES = {1: "system", 2: "custom"}
    # projectId = models.IntegerField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=20)
    type = models.IntegerField(default=2)
    package = models.CharField(max_length=200, null=True)
    clazz = models.CharField(max_length=50, null=True)
    method = models.CharField(max_length=50, null=True)
    params = models.TextField(null=True)
    steps = models.TextField(null=True)
    createTime = models.DateTimeField(default=timezone.now)
    remark = models.TextField(null=True)

    class Meta:
        db_table = "keyword"

    def clean(self):
        name = self.name.strip() if self.name else ""
        projectId = int(self.project.id) if str(self.project.id).isdigit() else 0
        package = self.package
        clazz = self.clazz
        method = self.method
        if not str(self.type).isdigit():
            raise ValidationError({'type': '无效的操作类型'})
        t = int(self.type)
        step = self.steps if self.steps else []
        if 0 >= len(name) or len(name) > 20:
            raise ValidationError({'name': '无效的关键字名称'})
        if projectId < 0:
            raise ValidationError({'projectId': '无效的项目Id'})
        if t == 1:
            try:
                obj = __import__(package, fromlist=[package.split(",")[-1]])
            except:
                raise ValidationError({'package': '无效的引用包'})
            try:
                obj = getattr(obj, clazz)
            except:
                raise ValidationError({'clazz': '无效的引用类'})
            try:
                getattr(obj, method)
            except:
                raise ValidationError({'method': '无效的引用方法'})
        elif t == 2:
            if isinstance(step, str):
                import json
                step = json.loads(step)
            if not isinstance(step, list):
                raise ValidationError({'step': '无效的操作步骤 : not list'})
            for s in step:
                if not isinstance(s, dict):
                    raise ValidationError({'step': '无效的操作步骤'})
                if not "keywordId" in s:
                    raise ValidationError({'step': '无效的操作步骤 : keywordId'})
                keywordId = int(s.get("keywordId")) if str(s.get("keywordId")).isdigit() else 0
                if keywordId < 1:
                    raise ValidationError({'step': '无效的操作步骤 : keywordId'})
                if not ("values" in s and isinstance(s.get("values"), list)):
                    raise ValidationError({'step': '无效的操作步骤 : values'})
                values = s.get("values")
                for value in values:
                    try:
                        Params(value)
                    except ValueError:
                        raise ValidationError({'step': '无效的操作步骤 : value'})
        else:
            raise ValidationError({'type': '无效的操作类型'})


class TestCase(models.Model):
    # TESTCASE_TYPES = {1: "功能测试", 2: "接口测试"}
    TESTCASE_STATUS = {1: "未执行", 2: "排队中", 3: "执行中"}
    TESTCASE_LEVEL = {1: "低", 2: "中", 3: "高", }
    TESTCASE_CHECK_TYPE = {1: "url", 2: "element"}
    # projectId = models.IntegerField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    title = models.CharField(max_length=200, null=False)
    # type = models.IntegerField(null=False, default=1)
    level = models.IntegerField(default=1)
    # status = models.IntegerField(null=False)
    beforeLogin = models.TextField(null=True)
    steps = models.TextField(null=False)
    parameter = models.TextField()
    checkType = models.TextField()
    checkValue = models.TextField()
    checkText = models.TextField(null=True)
    selectText = models.TextField(null=True)
    createTime = models.DateTimeField(default=timezone.now)
    remark = models.TextField(null=True)

    class Meta:
        db_table = "testcase"

    def clean(self):
        projectId = self.project.id if self.project.id else 0
        projectId = int(self.project.id) if str(projectId).isdigit() else 0
        title = self.title.strip() if self.title else ""
        # Type = self.type
        level = self.level
        # status = self.status
        step = self.steps
        parameter = self.parameter
        checkType = self.checkType
        checkValue = self.checkValue
        checkText = self.checkText
        selectText = self.selectText
        login = self.beforeLogin
        if not isinstance(login, list):
            raise ValidationError({'beforeLogin': '无效的登录配置'})
        if not projectId or projectId < 1:
            raise ValidationError({'projectId': '无效的项目Id'})
        if not title or 0 >= len(title) or len(title) > 200:
            raise ValidationError({'title': '无效的测试用例标题'})
        if not (level and level in TestCase.TESTCASE_LEVEL):
            raise ValidationError({'level': '无效的用例优先级'})
        # if not (status and status in TestCase.TESTCASE_STATUS):
        #     raise ValidationError({'level': 'Invalid level'})

        if not isinstance(step, list):
            raise ValidationError({'step': '无效的操作步骤 : steps'})
        for s in step:
            if not isinstance(s, dict):
                raise ValidationError({'step': '无效的操作步骤 : step'})
        # if not "keywordId" in s:
        #         raise ValidationError({'step': '无效的操作步骤 1 : keywordId'})
        #     keywordId = int(s.get("keywordId")) if str(s.get("keywordId")).isdigit() else 0
        #     if keywordId < 1:
        #         raise ValidationError({'step': '无效的操作步骤 : keywordId'})
        #     if not ("values" in s and isinstance(s.get("values"), list)):
        #         raise ValidationError({'step': '无效的操作步骤 : values'})
        #     values = s.get("values")
        #     for value in values:
        #         try:
        #             Params(value)
        #         except ValueError:
        #             raise ValidationError({'step': '无效的操作步骤 : value '})
        if checkType:
            if checkValue:
                try:
                    Check(checkType, checkValue)
                except:
                    raise ValidationError({'check': '无效的断言'})
            else:
                raise ValidationError({'check': '无效的断言值'})
        if parameter:
            if isinstance(parameter, list):
                for p in parameter:
                    if 'expect' not in p:
                        raise ValidationError({'parameter': '测试数据中未找到预期结果'})
            else:
                raise ValidationError({'parameter': '无效的测试数据'})


class Environment(models.Model):
    # projectId = models.IntegerField(null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=20, null=False)
    host = models.TextField(null=False)
    remark = models.TextField(null=True)

    class Meta:
        db_table = 'Environment'

    def clean(self):
        projectId = int(self.project.id) if str(self.project.id).isdigit() and int(self.project.id) > 0 else 0
        name = self.name.strip() if self.name else ""
        host = str(self.host).strip() if self.host else ""
        if projectId < 1:
            raise ValidationError({'projectId': '无效的项目Id'})
        if not name or len(name) > 20 or len(name) < 1:
            raise ValidationError({'name': '无效的环境名称'})
        if not host or len(host) < 1:
            raise ValidationError({'host': '无效的环境域名'})


class Browser(models.Model):
    name = models.CharField(max_length=20, null=False)
    value = models.CharField(max_length=20, null=False)
    remark = models.TextField(null=True)
    status = models.IntegerField(default=0, null=True)  # 区分web和app
    installPath = models.TextField(null=True)
    driverPath = models.TextField(null=True)

    class Meta:
        db_table = 'Browser'

    def clean(self):
        name = self.name.strip() if self.name else ""
        if 0 >= len(name) or len(name) > 20:
            raise ValidationError({'name': '无效的浏览器名称'})
        value = self.value.strip() if self.value else ""
        if 0 >= len(value) or len(value) > 20:
            raise ValidationError({'value': '无效的浏览器控制器'})

    def buid(self, host):
        browser = self.value.lower().strip() if self.value else ""
        log.info("启动的浏览器名称是 : {}".format(browser))
        if browser not in ["android", "html"]:
            if browser == 'chrome-no-web':
                executable_path = check_file(os.path.join(driver_path, "chromedriver.exe"))
                options = Options()
                options.add_argument('headless')  # 不显示执行过程，不打开浏览器
                options.add_argument("disable-infobars")
                options.add_argument('no-sandbox')
                options.add_argument('disable-dev-shm-usage')
                browser = webdriver.Chrome(chrome_options=options, executable_path=executable_path)
            elif browser == 'chrome':
                executable_path = check_file(os.path.join(driver_path, "chromedriver.exe"))
                options = Options()
                # options.add_argument('headless')
                options.add_argument("disable-infobars")
                options.add_argument('no-sandbox')
                options.add_argument('disable-dev-shm-usage')
                browser = webdriver.Chrome(chrome_options=options, executable_path=executable_path)
            elif browser == 'firefox':
                executable_path = check_file(os.path.join(driver_path, "geckodriver.exe"))
                browser = webdriver.Firefox(executable_path=executable_path)
            elif browser == 'edge':
                browser = webdriver.Edge()
            elif browser == 'ie':
                executable_path = check_file(os.path.join(driver_path, "IEDriverServer.exe"))
                DesiredCapabilities.INTERNETEXPLORER['ignoreProtectedModeSettings'] = True
                browser = webdriver.Ie(executable_path=executable_path)
            else:
                browser = webdriver.Chrome()
            browser.maximize_window()
            return browser
        else:
            # host = eval(host)
            if not os.path.exists(host):
                error = "apk路径不存在！{}".format(host)
                log.error(error)
                raise Exception(error)
            if os.path.splitext(host)[-1] != ".apk":
                error = "apk文件类型错误！{}".format(host)
                log.error(error)
                raise Exception(error)
            cmd = r"aapt dump badging {}".format(host)
            try:
                with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as f:
                    text = f.communicate()[0].decode("utf-8")
            except Exception as e:
                raise Exception("apk名称可能存在问题，就确认后执行！{} {}".format(e, cmd))
            appPackage = re.compile("package: name='(.+?)' ")
            appActivity = re.compile("activity: name='(.+?)'")
            package = appPackage.findall(text)[0]
            activity = appActivity.findall(text)[0]
            with os.popen("adb shell pm list packages", "r") as f:
                all_package = f.read()
            if package not in all_package:
                log.info("当前设备未安装测试app，准备安装中~~~")
                cmd = r"adb install {}".format(host)
                os.system(cmd)
            try:
                desired_caps = {
                    # "platformName": host.get("platformName", ""),
                    "platformName": "Android",

                    "deviceName": "Android",

                    # 不重置app
                    # "noReset": host.get("noReset", ""),
                    "noReset": True,

                    # "autoLaunch": host.get("autoLaunch", True),
                    "autoLaunch": True,

                    # "udid": "" # 指定运行设备
                    # "chromeOptions": {"androidProcess": "com.tencent.mm:tools"}
                }

                if browser == "android":
                    desired_caps.update({"appPackage": package,

                                         "appActivity": activity,
                                         # 隐藏手机默认键盘
                                         # "unicodeKeyboard": host.get("unicodeKeyboard", ""),
                                         "unicodeKeyboard": True,

                                         # "resetKeyboard": host.get("unicodeKeyboard", ""),
                                         "resetKeyboard": True,

                                         "automationName": "uiautomator2",
                                         })
                elif browser == "simulator":
                    # desired_caps.update({"platformVersion": host.get("platformVersion", ""), })
                    desired_caps.update({"platformVersion": "9.0", })
                elif browser == "html":
                    executable_path = check_file(os.path.join(os.path.join(driver_path, "h5"), "chromedriver.exe"))
                    desired_caps.update({"browserName": "chrome",

                                         "chromedriverExecutable": executable_path,

                                         "showChromedriverLog": True, })

                # 关联appium
                browser = app.Remote("http://127.0.0.1:4723/wd/hub", desired_caps)
                return browser
            except Exception as e:
                raise Exception("连接 Appium 出错：{}".format(e))


class Result(models.Model):
    title = models.CharField(max_length=200, null=False)
    taskId = models.IntegerField(null=True, default=0)
    # projectId = models.IntegerField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE, default=None)
    # testcaseId = models.IntegerField()
    browsers = models.TextField(null=True)
    beforeLogin = models.TextField(null=True)
    environments = models.TextField(null=True)
    status = models.IntegerField(default=10)  # 10 排队中 20 测试中 30 成功  40 失败
    parameter = models.TextField()
    steps = models.TextField(null=False)
    checkType = models.TextField()
    checkValue = models.TextField()
    checkText = models.TextField(null=True)
    selectText = models.TextField(null=True)
    createTime = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Result'


class SplitResult(models.Model):
    # environmentId = models.IntegerField(null=True)
    # browserId = models.IntegerField(null=True)
    # resultId = models.IntegerField()
    result = models.ForeignKey(Result, on_delete=models.CASCADE, default=None)
    browser = models.ForeignKey(Browser, on_delete=models.CASCADE, default=None)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, default=None)
    loginStatus = models.IntegerField(default=0)  # 1 成功  2 失败  3 跳过
    createTime = models.DateTimeField(default=timezone.now)
    startTime = models.DateTimeField(null=True)
    finishTime = models.DateTimeField(null=True)
    parameter = models.TextField()
    expect = models.BooleanField()
    status = models.IntegerField(default=10)  # 10 排队中 20 测试中 30 成功  40 失败 50跳过
    remark = models.TextField(null=True)
    step_num = models.IntegerField(default=0)
    error_name = models.CharField(max_length=200, default="")
    again = models.IntegerField(default=0, null=True)  # 再次执行标记

    class Meta:
        db_table = 'SplitResult'


class Task(models.Model):
    name = models.CharField(max_length=200, null=False)
    testcases = models.TextField(null=False)
    browsers = models.TextField(null=True)
    status = models.IntegerField(null=True, default=1)
    timing = models.IntegerField(null=False, default=1)  # 1 定时  2 常规
    remark = models.TextField(null=True)
    createTime = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Task'

    def clean(self):
        name = self.name.strip() if self.name else ""
        testcases = self.testcases if self.testcases else []
        browsers = self.browsers if self.browsers else []
        if not name or len(name) > 20 or len(name) < 1:
            raise ValidationError({'name': '无效的任务名称'})
        if not (testcases and isinstance(testcases, list)):
            raise ValidationError({'testcases': '无效的测试用例集'})
        if not (browsers and isinstance(browsers, list)):
            raise ValidationError({'browsers': '无效的浏览器设置'})


class Params:
    TYPE_STRING = 'string'
    TYPE_INT = 'int'
    TYPE_ELEMENT = 'element'
    TYPE_FILE = 'file'
    TYPES = [TYPE_ELEMENT, TYPE_FILE, TYPE_STRING]

    def __init__(self, kwargs):
        isParameter = kwargs.get("isParameter", False)
        Type = kwargs.get("type", None)
        key = kwargs.get("key", None)
        value = kwargs.get("value", None)
        if not (Type and isinstance(Type, str)):
            raise ValueError("Params object Type must be str type")
        Type = Type.lower()
        if Type not in Params.TYPES:
            raise ValueError("Params object Type value error")
        if isParameter and (not value or str(value).strip() == 0):
            raise ValueError("Params Type parameter must has key")
        else:
            self.Type = Type
            self.key = key.strip()
            self.value = value
            self.isParameter = isParameter

    def __dict__(self):
        obj = dict()
        obj["type"] = self.Type
        obj["isParameter"] = self.isParameter
        obj["value"] = self.value
        obj["key"] = self.key
        return obj


class Check:
    TYPE_URL = 'url'
    TYPE_ELEMENT = 'element'
    TYPES = [TYPE_URL, TYPE_ELEMENT]

    def __init__(self, type_, value):
        self.type = type_
        self.value = value
        if not (self.type and self.type in Check.TYPES):
            raise ValueError("Check对象的type属性值错误")
        if self.type and (value and not self.value.strip()):
            raise ValueError("Check对象的value属性不能为空")

    def __dict__(self):
        obj = dict()
        obj['type'] = self.type
        obj['value'] = self.value


class LoginConfig(models.Model):
    # projectId = models.IntegerField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=20, null=False)
    remark = models.TextField(null=True)
    checkType = models.TextField(default='')
    checkValue = models.TextField(default='')
    checkText = models.TextField(default='')
    selectText = models.TextField(default='')
    steps = models.TextField(null=False)
    params = models.TextField()
    createTime = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'login'

    def clean(self):
        name = self.name.strip() if self.name else ""
        step = self.steps
        checkType = self.checkType
        checkValue = self.checkValue
        checkText = self.checkText
        selectText = self.selectText
        if not name or 0 >= len(name) or len(name) > 20:
            raise ValidationError({'name': '无效的登录配置名称'})
        if not isinstance(step, list):
            raise ValidationError({'step': '无效的登录步骤 : steps'})
        for s in step:
            if not isinstance(s, dict):
                raise ValidationError({'step': '无效的登录步骤 : step'})
            if not "keywordId" in s:
                raise ValidationError({'step': '无效的登录步骤 : keywordId'})
            keywordId = int(s.get("keywordId")) if str(s.get("keywordId")).isdigit() else 0
            if keywordId < 1:
                raise ValidationError({'step': '无效的登录步骤 : keywordId'})
            if not ("values" in s and isinstance(s.get("values"), list)):
                raise ValidationError({'step': '无效的登录步骤 : values'})
            values = s.get("values")
            for value in values:
                try:
                    Params(value)
                except ValueError:
                    raise ValidationError({'step': '无效的登录步骤 : value'})
        try:
            Check(checkType, checkValue)
        except:
            raise ValidationError({'check': '无效的登录断言'})


class EnvironmentLogin(models.Model):
    # loginId = models.IntegerField()
    login = models.ForeignKey(LoginConfig, on_delete=models.CASCADE, default=None)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, default=None)
    # environmentId = models.IntegerField()
    parameter = models.TextField()

    class Meta:
        db_table = 'EnvironmentLogin'


class TaskRelation(models.Model):
    result_id_list = models.CharField(max_length=200, null=True)
    result_id = models.ImageField(null=True)

    class Meta:
        db_table = 'TaskRelation'
