# Generated by Django 2.2.2 on 2019-09-20 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trackerapp', '0008_auto_20190920_1209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projects',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='projectusers',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='projectversions',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
