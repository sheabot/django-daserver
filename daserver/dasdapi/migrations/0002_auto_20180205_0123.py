# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dasdapi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='packagefile',
            name='filesize',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='packagefile',
            name='sha256',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
