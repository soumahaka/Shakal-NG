# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from haystack import indexes

from tweets.models import Tweet


class TweetIndex(indexes.SearchIndex, indexes.Indexable):
	created = indexes.DateTimeField(model_attr='created')
	updated = indexes.DateTimeField(model_attr='updated')
	title = indexes.CharField(model_attr='title')
	text = indexes.CharField(document=True, use_template=True)

	def get_updated_field(self):
		return "updated"

	def get_model(self):
		return Tweet

	def index_queryset(self, using=None):
		return self.get_model().objects.all()

