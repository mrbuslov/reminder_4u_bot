# Generated by Django 5.1.1 on 2024-09-14 09:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reminder", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reminder",
            name="user_specified_date_time",
            field=models.DateTimeField(
                default=datetime.datetime.now,
                verbose_name="User specified date and time to remind in his timezone",
            ),
        ),
    ]
