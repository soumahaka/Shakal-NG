# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-03 14:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

	dependencies = [
		('comments', '0001_initial'),
	]

	operations = [
		migrations.AlterField(
			model_name='comment',
			name='content_type',
			field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_type_set_for_comment', to='contenttypes.ContentType', verbose_name='typ obsahu'),
		),
		migrations.AlterField(
			model_name='commentflag',
			name='user',
			field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_flags', to=settings.AUTH_USER_MODEL, verbose_name='používateľ'),
		),
	]
