# -*- coding: utf-8 -*-
# pylint: disable=no-member,model-missing-unicode
from __future__ import unicode_literals

import os
import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import signals
from django.db.models.fields.files import FileField
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from .utils import replace_file_urls
from autoimagefield.fields import AutoImageFieldMixin
from common_utils import clean_dir, get_meta


def upload_to(instance, filename):
	content_class = instance.content_type.model_class()
	return 'attachment/{0}_{1}/{2:02x}/{3}/{4}'.format(
		get_meta(content_class).app_label,
		get_meta(content_class).object_name.lower(),
		instance.object_id % 256,
		instance.object_id,
		filename
	)


class ThumbnailImageField(AutoImageFieldMixin, FileField):
	def __init__(self, *args, **kwargs):
		self.thumbnail = {'standard': (256, 256)}
		super(ThumbnailImageField, self).__init__(*args, **kwargs)

	def _rename_image(self, instance, **kwargs):
		if hasattr(instance, 'attachmentimage'):
			return super(ThumbnailImageField, self)._rename_image(instance.attachmentimage, **kwargs)

	def _add_old_instance(self, instance, **kwargs):
		if hasattr(instance, 'attachmentimage'):
			return super(ThumbnailImageField, self)._add_old_instance(instance.attachmentimage, **kwargs)

	def _delete_image(self, instance, **kwargs):
		if hasattr(instance, 'attachmentimage'):
			return super(ThumbnailImageField, self)._delete_image(instance.attachmentimage, **kwargs)

	def contribute_to_class(self, cls, name):
		signals.post_save.connect(self._rename_image, sender=cls)
		signals.post_init.connect(self._add_old_instance, sender=cls)
		signals.post_delete.connect(self._delete_image, sender=cls)
		self._add_thumbnails(cls, name)
		super(ThumbnailImageField, self).contribute_to_class(cls, name)


class Attachment(models.Model):
	attachment = ThumbnailImageField(_('attachment'), upload_to=upload_to)
	created = models.DateTimeField(_('created'), auto_now_add=True)
	size = models.IntegerField(_('size'))
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = GenericForeignKey('content_type', 'object_id')

	class Meta:
		verbose_name = _('attachment')
		verbose_name_plural = _('attachments')

	@property
	def basename(self):
		return os.path.basename(self.attachment.name)

	@property
	def name(self):
		return os.path.split(self.attachment.name)[1]

	@property
	def url(self):
		return settings.MEDIA_URL + self.attachment.name

	@property
	def filename(self):
		return os.path.join(settings.MEDIA_ROOT, self.attachment.name)

	def __unicode__(self):
		return self.attachment.name

	def delete_file(self):
		if self.attachment:
			name = self.attachment.name
			storage = self.attachment.storage
			storage.delete(name)
			clean_dir(os.path.dirname(storage.path(name)), settings.MEDIA_ROOT)
			self.attachment = ''

	def save(self, *args, **kwargs):
		if self.pk:
			original = self.__class__.objects.get(pk=self.pk)
			if self.attachment and original.attachment:
				original.attachment.storage.delete(original.attachment.path)

		self.size = self.attachment.size
		self.copy_to_new_location()
		super(Attachment, self).save(*args, **kwargs)

	def copy_to_new_location(self):
		name = self.attachment.name
		storage = self.attachment.storage
		target_name = upload_to(self, os.path.basename(name))
		if target_name != name:
			if storage.exists(name):
				file_name = storage.save(target_name, self.attachment.file)
				self.attachment = file_name


class AttachmentImage(Attachment):
	width = models.IntegerField()
	height = models.IntegerField()

	def __unicode__(self):
		super(AttachmentImage, self).__unicode__()


class AttachmentImageRaw(models.Model):
	attachment_ptr = models.PositiveIntegerField(db_column='attachment_ptr_id', primary_key=True)
	width = models.IntegerField()
	height = models.IntegerField()

	class Meta:
		app_label = get_meta(AttachmentImage).app_label
		db_table = get_meta(AttachmentImage).db_table
		managed = False


def generate_uuid():
	return uuid.uuid1().hex


class UploadSession(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	uuid = models.CharField(max_length=32, unique=True, default=generate_uuid)
	attachments = GenericRelation(Attachment)

	def move_attachments(self, content_object, replace_urls=True):
		"""
		Presun príloh do adresára podľa typu objektu a jeho ID napr: attachments/article/1
		"""
		moves = []
		temp_attachments = self.attachments.all()
		for temp_attachment in temp_attachments:
			attachment = Attachment(
				attachment=temp_attachment.attachment.name,
				content_type=ContentType.objects.get_for_model(content_object.__class__),
				object_id=content_object.pk
			)
			attachment.save()
			moves.append((temp_attachment.attachment.name, attachment.attachment.name))
			temp_attachment.delete()
		if replace_urls and moves:
			self.__replace_content_attachment_urls(content_object, moves)
		return moves

	def __unicode__(self):
		return self.uuid

	def __replace_content_attachment_urls(self, content_object, moves):
		"""
		Nahradenie dočasných URL adres v objekte po presune príloh.
		"""
		changed = False
		if not hasattr(content_object, 'content_fields'):
			return
		for field in content_object.content_fields:
			old_val = getattr(content_object, field, None)
			if isinstance(old_val, six.string_types):
				new_val = replace_file_urls(old_val, moves)
				if new_val != old_val:
					changed = True
					setattr(content_object, field, new_val)
		if changed:
			content_object.save()
