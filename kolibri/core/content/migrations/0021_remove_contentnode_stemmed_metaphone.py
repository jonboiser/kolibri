# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-21 17:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("content", "0020_le_utils_0_20_upgrade_migration")]

    operations = [
        migrations.RemoveField(model_name="contentnode", name="stemmed_metaphone")
    ]