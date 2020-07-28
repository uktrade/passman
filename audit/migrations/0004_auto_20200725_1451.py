# Generated by Django 3.0.8 on 2020-07-25 14:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('secret', '0005_auto_20200719_1042'),
        ('audit', '0003_audit_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audit',
            name='action',
            field=models.CharField(choices=[('created_secret', 'Created'), ('updated_secret', 'Updated'), ('viewed_secret', 'Viewed'), ('add_permission', 'Add permission'), ('remove_permission', 'Remove permission')], max_length=255),
        ),
        migrations.AlterField(
            model_name='audit',
            name='secret',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='secret.Secret'),
        ),
    ]
