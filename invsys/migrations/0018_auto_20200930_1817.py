# Generated by Django 2.1.7 on 2020-09-30 10:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invsys', '0017_remove_shipping_lobby_reference_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipping_Outbound',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(blank=True, null=True)),
                ('date_received', models.DateField()),
                ('received_by', models.CharField(default='', max_length=200)),
                ('checked_by', models.CharField(default='', max_length=200)),
                ('notes', models.CharField(blank=True, default='', max_length=200, null=True)),
                ('prod_number', models.ForeignKey(blank=True, default='1', null=True, on_delete=django.db.models.deletion.CASCADE, to='invsys.Product')),
                ('prod_sched', models.ForeignKey(blank=True, default='1', null=True, on_delete=django.db.models.deletion.CASCADE, to='invsys.WO_Production_Schedule')),
            ],
            options={
                'verbose_name': 'Shipping Lobby',
                'verbose_name_plural': 'Shipping Lobbies',
            },
        ),
        migrations.RenameField(
            model_name='recproduct_item_transaction',
            old_name='item_number',
            new_name='prod_number',
        ),
        migrations.RenameField(
            model_name='recproduct_item_transaction',
            old_name='item_quantity',
            new_name='prod_quantity',
        ),
        migrations.RenameField(
            model_name='recproduct_product_transaction',
            old_name='item_number',
            new_name='prod_number',
        ),
        migrations.RenameField(
            model_name='recproduct_product_transaction',
            old_name='item_quantity',
            new_name='prod_quantity',
        ),
        migrations.RenameField(
            model_name='recproduct_producttoshiplobby_transaction',
            old_name='item_number',
            new_name='prod_number',
        ),
        migrations.RenameField(
            model_name='recproduct_producttoshiplobby_transaction',
            old_name='item_quantity',
            new_name='prod_quantity',
        ),
        migrations.RenameField(
            model_name='recproduct_producttowhse_transaction',
            old_name='item_number',
            new_name='prod_number',
        ),
        migrations.RenameField(
            model_name='recproduct_producttowhse_transaction',
            old_name='item_quantity',
            new_name='prod_quantity',
        ),
    ]
