# Generated by Django 3.0.8 on 2020-08-12 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0004_auto_20200725_1451"),
    ]

    operations = [
        migrations.AlterField(
            model_name="audit",
            name="action",
            field=models.CharField(
                choices=[
                    ("imported", "Imported"),
                    ("create_secret", "Created"),
                    ("update_secret", "Updated"),
                    ("view_secret", "Viewed"),
                    ("add_permission", "Added permission"),
                    ("remove_permission", "Removed permission"),
                ],
                max_length=255,
            ),
        ),
    ]
