# config: utf-8

from __future__ import absolute_import, division, unicode_literals, print_function

import logging
log = logging.getLogger(__name__)

import os
import errno

from sqlalchemy.orm.exc import NoResultFound
from pyramid.httpexceptions import HTTPBadRequest

from .image_ops import (
    open_image, save_image,
    make_thumbnail_crop_to_size, make_thumbnail_keep_proportions
)

from .exceptions import HandlerException


class Variant(object):

    def __init__(self, quality=70):
        self.quality = quality

    def register(self, views, delegate, variant):
        self.views = views
        self.delegate = delegate
        self.variant = variant

    def create_from_request(self, model_obj, source_file):
        image = open_image(source_file)
        image = self._process_image(image)
        self._save_image(image, model_obj)

    def file_exists(self, model_obj):
        path = model_obj.fs_path(self.variant)
        return os.path.isfile(path)

    def create_from_file(self, model_obj):
        source_path = model_obj.fs_path()
        image = open_image(source_path)
        image = self._process_image(image)
        self._save_image(image, model_obj)

    def _process_image(self, image):
        return image

    def _save_image(self, image, model_obj):
        save_path = model_obj.fs_path(self.variant)
        save_image(image, save_path, self.quality)


class Thumbnail(Variant):

    algos = {
        'keep-proportions': make_thumbnail_keep_proportions,
        'crop-to-size':     make_thumbnail_crop_to_size
    }

    def __init__(self, size, algo='keep-proportions', **kwargs):
        super().__init__(**kwargs)
        self.size = size
        self.algo = self.algos[algo]

    def _process_image(self, image):
        return self.algo(image, self.size)
