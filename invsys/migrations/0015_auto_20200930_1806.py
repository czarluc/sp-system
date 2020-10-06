# Generated by Django 2.1.7 on 2020-09-30 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invsys', '0014_auto_20200930_1711'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shipping_outbound_transaction',
            old_name='item_number',
            new_name='prod_number',
        ),
        migrations.RenameField(
            model_name='shipping_outbound_transaction',
            old_name='item_quantity',
            new_name='prod_quantity',
        ),
        migrations.RenameField(
            model_name='shipping_whseproduct_transaction',
            old_name='item_number',
            new_name='prod_number',
        ),
        migrations.RenameField(
            model_name='shipping_whseproduct_transaction',
            old_name='item_quantity',
            new_name='prod_quantity',
        ),
        migrations.AlterField(
            model_name='shipping_lobby',
            name='notes',
            field=models.CharField(blank=True, default='', max_length=200, null=True),
        ),
    ]
