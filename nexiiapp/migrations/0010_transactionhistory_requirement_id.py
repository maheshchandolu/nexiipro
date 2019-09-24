# Generated by Django 2.2.3 on 2019-07-23 12:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nexiiapp', '0009_transactionhistory_upload_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactionhistory',
            name='requirement_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='transaction_requirement_id', to='nexiiapp.Requirement'),
            preserve_default=False,
        ),
    ]