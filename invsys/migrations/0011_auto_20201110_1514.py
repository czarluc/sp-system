# Generated by Django 2.1.7 on 2020-11-10 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invsys', '0010_auto_20201108_0326'),
    ]

    operations = [
        migrations.AddField(
            model_name='work_order',
            name='finished',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='work_order',
            name='shipped',
            field=models.BooleanField(default=False),
        ),
    ]
