# Generated by Django 3.1.13 on 2021-11-12 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('secret', '0007_auto_20210118_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='secret',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
    ]
