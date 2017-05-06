# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

urlpatterns = [
	url(r'^sprava/vytvorit/$', 'DesktopCreate', name='create'),
	url(r'^zoznam/(?:(?P<page>\d+)/)?$', 'DesktopList', name='list'),
	url(r'^zoznam/autor/(?P<category>\d+)/(?:(?P<page>\d+)/)?$', 'DesktopList', name='list-author'),
	url(r'^detail/(?P<pk>\d+)/$', 'DesktopDetail', name='detail'),
	url(r'^upravit/(?P<pk>\d+)/$', 'DesktopUpdate', name='update'),
	url(r'^feeds/latest/$', 'DesktopFeed', name='feed-latest'),
]
