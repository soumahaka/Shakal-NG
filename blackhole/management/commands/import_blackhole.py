# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple

from django.core.management.base import BaseCommand
from django.db import connections
from datetime import datetime
from django.utils.functional import cached_property
#from common_utils.asciitable import NamedtupleTablePrinter


COMMENT_NODE_HIDDEN = 0
COMMENT_NODE_CLOSED = 1
COMMENT_NODE_OPEN = 2

NODE_NOT_PROMOTED = 0
NODE_PROMOTED = 1

NODE_NOT_STICKY = 0
NODE_STICKY = 1

USER_STATUS_BLOCKED = 0
USER_STATUS_ACTIVE = 1


FilterFormat = namedtuple('FilterFormat', ['format', 'name'])
NodeData = namedtuple('NodeData', ['nid', 'type', 'title', 'uid', 'status', 'created', 'changed', 'comment', 'promote', 'sticky', 'vid'])
TermData = namedtuple('TermData', ['tid', 'parent', 'vid', 'name', 'description'])
UserData = namedtuple('UserData', ['uid', 'name', 'signature', 'created', 'login', 'status', 'picture'])


FORMATS_TRANSLATION = {
	'Filtered HTML': 'html',
	'PHP code': 'html',
	'Full HTML': 'raw',
	'No HTML': 'text',
}


class Command(BaseCommand):
	@cached_property
	def db_connection(self):
		return connections['blackhole']

	def db_cursor(self):
		return self.db_connection.cursor()

	@cached_property
	def filter_formats(self):
		cursor = self.db_cursor()
		cursor.execute('SELECT format, name FROM filter_formats')
		formats = tuple(FilterFormat(*row) for row in cursor.fetchall())
		return {f.format: FORMATS_TRANSLATION[f.name] for f in formats}

	def nodes(self):
		def to_python(row):
			row = list(row)
			row[5] = datetime.fromtimestamp(row[5])
			row[6] = datetime.fromtimestamp(row[6])
			return tuple(row)
		cursor = self.db_cursor()
		cursor.execute('SELECT nid, type, title, uid, status, created, changed, comment, promote, sticky, vid FROM node')
		nodes = tuple(NodeData(*to_python(row)) for row in cursor.fetchall())
		for node in nodes:
			yield node

	def terms(self):
		cursor = self.db_cursor()
		cursor.execute('SELECT term_data.tid, term_hierarchy.parent, term_data.vid, term_data.name, description FROM term_data LEFT JOIN term_hierarchy ON term_data.tid = term_hierarchy.tid')
		return tuple(TermData(*row) for row in cursor.fetchall())

	def users(self):
		cursor = self.db_cursor()
		cursor.execute('SELECT uid, name, signature, created, login, status, picture FROM users')
		return tuple(UserData(*row) for row in cursor.fetchall())

	def handle(self, *args, **options):
		print(self.users())