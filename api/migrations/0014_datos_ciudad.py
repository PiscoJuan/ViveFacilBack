# Generated by Django 3.1 on 2020-10-13 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_auto_20201013_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='datos',
            name='ciudad',
            field=models.CharField(max_length=20, null=True),
        ),
    ]