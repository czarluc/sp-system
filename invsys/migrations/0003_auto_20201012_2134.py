# Generated by Django 2.1.7 on 2020-10-12 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invsys', '0002_auto_20201006_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request_item',
            name='refnum',
            field=models.CharField(blank=True, default='', max_length=200, null=True),
        ),
    ]
