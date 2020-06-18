from django.db import models
import django.utils.timezone as timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class Team(models.Model):
    name = models.CharField(max_length=20, null=False)
    remark = models.TextField(null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, default='lixiaofeng')
    update_time = models.DateTimeField('更新时间', auto_now=True)
    createTime = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'team'

    def clean(self):
        name = self.name.strip() if self.name else ""
        if 0 >= len(name) or len(name) > 20:
            raise ValidationError({'error': '无效的团队名称'})


class TeamUsers(models.Model):
    team_id = models.ForeignKey(Team, on_delete=models.CASCADE, default=None)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
