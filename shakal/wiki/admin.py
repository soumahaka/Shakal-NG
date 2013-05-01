# -*- coding: utf-8 -*-

from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from shakal.wiki.models import Page
import reversion


class PageAdmin(reversion.VersionAdmin, MPTTModelAdmin):
	list_display = ('title', 'slug', )
	search_fields = ('title', 'filtered_text', )
	exclude = ('filtered_text', )
	ordering = ('-id', )
	prepopulated_fields = {'slug': ('title', )}
	raw_id_fields = ('parent', 'last_author',)

admin.site.register(Page, PageAdmin)
