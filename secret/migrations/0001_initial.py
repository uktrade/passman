# Generated by Django 3.0.8 on 2020-07-12 11:43

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Secret",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("url", models.URLField(blank=True)),
                ("username", models.CharField(blank=True, max_length=255)),
                ("password", models.CharField(blank=True, max_length=255)),
                ("details", models.TextField(blank=True)),
            ],
        ),
    ]
