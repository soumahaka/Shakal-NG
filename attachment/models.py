# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
import uuid
import os

class Attachment(models.Model):
	def upload_dir(instance, filename):
		return 'attachment/{0}_{1}/{2}/{3:02x}/{4}'.format(
			instance.content_object._meta.app_label,
			instance.content_object._meta.object_name.lower(),
			instance.content_object.pk,
			instance.content_object.pk,
			filename
		)

	attachment = models.FileField(verbose_name = _('attachment'), upload_to = upload_dir)
	created = models.DateTimeField(auto_now_add = True, verbose_name = _('created'))
	size = models.IntegerField(verbose_name = _('size'))
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = generic.GenericForeignKey('content_type', 'object_id')

	def delete(self, *args, **kwargs):
		super(Attachment, self).delete(*args, **kwargs)
		self.attachment.storage.delete(self.attachment.path)

	def save(self, *args, **kwargs):
		if self.pk:
			try:
				original = Attachment.objects.get(pk = self.pk)
				if self.attachment != original.attachment:
					original.attachment.storage.delete(original.attachment.path)
			except:
				pass
		self.size = self.attachment.size
		super(Attachment, self).save(*args, **kwargs)

	def clean(self):
		available_size = self.get_available_size(self.content_type, self.object_id, class_instance = self._meta.model)
		if self.attachment.size > available_size:
			raise ValidationError(_('File size exceeded, maximum size is ') + filesizeformat(available_size))

	@staticmethod
	def get_available_size(content_type, object_id, class_instance):
		if isinstance(content_type, (int, long, str, unicode)):
			content_type = ContentType.objects.get(pk = int(content_type))
		max_size = getattr(settings, 'ATTACHMENT_MAX_SIZE', -1)
		db_table = content_type.model_class()._meta.db_table
		size_for_content = getattr(settings, 'ATTACHMENT_SIZE_FOR_CONTENT', {}).get(db_table, -1)
		# Bez limitu
		if max_size == -1 and size_for_content == -1:
			return -1
		# Obsah bez limitu
		if size_for_content == -1:
			return max_size
		size = class_instance.objects.filter(object_id = object_id, content_type = content_type).aggregate(models.Sum('size'))["size__sum"]
		if size is None:
			size = 0
		if max_size == -1:
			return size_for_content - size
		else:
			return min(max_size, size_for_content - size)

	@property
	def name(self):
		return os.path.split(self.attachment.name)[1]

	def __unicode__(self):
		return self.attachment.name

	class Meta:
		verbose_name = _('attachment')
		verbose_name_plural = _('attachments')


def generate_uuid():
	return uuid.uuid1().hex

class UploadSession(models.Model):
	created = models.DateTimeField(auto_now_add = True)
	uuid = models.CharField(max_length = 32, unique = True, default = generate_uuid)


class TemporaryAttachment(Attachment):
	session = models.ForeignKey(UploadSession)
