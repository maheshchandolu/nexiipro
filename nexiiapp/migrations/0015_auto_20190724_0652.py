# Generated by Django 2.2.3 on 2019-07-24 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nexiiapp', '0014_auto_20190724_0635'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requirement',
            name='score',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=100),
        ),
        migrations.AlterField(
            model_name='transactionhistory',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=100),
        ),
        migrations.AlterField(
            model_name='upload',
            name='score',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=100),
        ),
    ]
