# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models.expressions import DateTime, Date
from django.utils import timezone

from common_utils import get_meta


DATETIME_SERIES = set(['minutes', 'hours'])
DATE_SERIES = set(['days', 'weeks', 'months', 'years'])


def time_series(qs, date_field, aggregate, interval):
	field = get_meta(qs.model).get_field(date_field)
	field_is_datetime = isinstance(field, models.DateTimeField)
	if not isinstance(aggregate, dict):
		aggregate = {'agg': aggregate}

	if field_is_datetime:
		db_interval = DateTime(date_field, interval, timezone.get_current_timezone())
	else:
		db_interval = Date(date_field, interval)

	qs = (qs
		.annotate(interval=db_interval))
	return qs