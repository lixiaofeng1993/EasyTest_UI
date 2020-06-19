# Generated by Django 3.0.7 on 2020-06-19 07:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_auto_20200619_1436'),
    ]

    operations = [
        migrations.RenameField(
            model_name='team',
            old_name='createTime',
            new_name='create_time',
        ),
        migrations.AddField(
            model_name='teamusers',
            name='create_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
