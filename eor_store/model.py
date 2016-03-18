# coding: utf-8

from __future__ import absolute_import, division, unicode_literals, print_function

import logging
log = logging.getLogger(__name__)

import os
import re
import unicodedata
from uuid import UUID, uuid1

from sqlalchemy import Column
from sqlalchemy.schema import Table, FetchedValue
from sqlalchemy.types import Unicode, DateTime
from sqlalchemy.ext.hybrid import hybrid_property

from . import config
from eor_settings import get_setting


# TODO delete files


def _slugify(val, max_len=32):
    """
    from https://github.com/django/django/blob/master/django/utils/text.py#L413
    unicodedata.normalize(): http://stackoverflow.com/a/14682498/1092084
    """
    val = unicodedata.normalize('NFKD', val)
    val = re.sub(r'[^\w\s-]', '', val, flags=re.U)
    val = val.strip().lower()
    val = re.sub(r'[-\s]+', '-', val, flags=re.U)
    return val[:max_len].replace('/', '-')


class File(config.sqlalchemy_base):
#class File(Base):
    """
    """

    __tablename__ = 'files'

    id                  = Column('id', Unicode, primary_key=True)
    type                = Column(Unicode)
    _orig_name          = Column('orig_name', Unicode)
    orig_name_sanitized = Column(Unicode)
    ext                 = Column(Unicode)
    #user_id             = Column(Unicode)
    added               = Column(DateTime, FetchedValue())

    def __init__(self, **kwargs):
        self.id = uuid1().hex
        super(File, self).__init__(**kwargs)

    @classmethod
    def get_by_id(cls, id):
        return (config.sqlalchemy_session()
                .query(cls)
                .filter(cls.id == id)
                .one())

    def add(self):
        config.sqlalchemy_session().add(self)

    # @hybrid_property
    # def id(self):
    #     return UUID(self._id)
    #
    # @id.setter
    # def id(self, val):
    #     self._id = val.hex

    @hybrid_property
    def orig_name(self):
        return self._orig_name

    @orig_name.setter
    def orig_name(self, val):
        self._orig_name = val
        self.orig_name_sanitized = _slugify(val)

    def fs_path(self, variant=None):
        """
        :return: absolute filesystem path to the file
        """
        filename = self._filename(variant)
        return os.path.join(self._filesystem_path_prefix(), self.type, self._subdirs(filename), filename)

    def url(self, variant=None):
        """
        :return: URL of the file
        """
        filename = self._filename(variant)
        return os.path.join(self._url_prefix(), self.type, self._subdirs(filename), filename)

    def get_src(self, variant=None):
        return self.url(variant)

    def get_view_url(self, variant=None, group='default'):
        from .views import StoreViews
        return StoreViews.get_view_url(self.type, self.id, group, variant)

    @classmethod
    def _filesystem_path_prefix(cls):
        return get_setting('eor-store.path')

    @classmethod
    def _url_prefix(cls):
        return '//' + get_setting('eor.static-domain') + '/store/'

    def _filename(self, variant=None):
        """
        :return: filename
        """
        variant = '.' + variant if variant else ''
        return u'%s-%s%s.%s' % (self.id, self.orig_name_sanitized, variant, self.ext)

    @classmethod
    def _subdirs(cls, filename):
        subdirs = [filename[n*config.subdir_chars:(n+1)*config.subdir_chars]
                   for n in range(config.subdirs)]
        return os.path.join(*subdirs)
