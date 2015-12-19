# coding: utf-8

from __future__ import absolute_import, division, unicode_literals, print_function

import logging
log = logging.getLogger(__name__)

import os

from .model import File


class StoreDelegate(object):
    name = None
    entity = File
    permission = None

    def __init__(self, views):
        self.views = views

    def create_obj(self, filename):
        filename_base, ext = os.path.splitext(filename)
        ext = ext.lstrip('.').lower()  # TODO sanitize
        # TODO check extension!
        return self.entity(type=self.name, orig_name=filename_base, ext=ext)

    def get_obj_by_id(self, file_id):
        return self.entity.get_by_id(file_id)

    def get_save_handlers(self):
        return []

    def get_variants(self):
        return {}
