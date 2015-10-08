# config: utf-8

from __future__ import absolute_import, division, unicode_literals, print_function

import logging
log = logging.getLogger(__name__)

import os
import errno

from sqlalchemy.orm.exc import NoResultFound
from pyramid.httpexceptions import HTTPBadRequest

#from .image import get_image_format, save_uploaded_image, NotAnImageException
from .image_ops import (
    open_image, save_image,
    make_thumbnail_crop_to_size, make_thumbnail_keep_proportions
)

from .exceptions import HandlerException


class Handler(object):

    def register(self, views, delegate):
        self.views = views
        self.delegate = delegate


class SetOwner(Handler):

    def __init__(self, owner_entity, owner_field=None, file_field=None,
                 owner_id_req_param='owner_id'):
        self.owner_entity = owner_entity
        self.owner_field = owner_field
        self.file_field = file_field
        self.owner_id_req_param = owner_id_req_param

    def get_owner_id(self):
        return self.views.request.params.get(self.owner_id_req_param)

    def get_owner_entity(self):
        owner_id = self.get_owner_id()
        if not owner_id:
            return None

        try:
            return self.owner_entity.get_by_id(owner_id)
        except NoResultFound:
            raise HandlerException(code='owner-not-found')

    def __call__(self, model_obj, source_file, orig_name):
        owner = self.get_owner_entity()
        if not owner:
            return

        if self.owner_field:
            setattr(model_obj, self.owner_field, owner)

        if self.file_field:
            getattr(owner, self.file_field).delete()
            setattr(owner, self.file_field, model_obj)


class SaveFile(Handler):

    def __init__(self, variant=None):
        self.variant = variant

    def __call__(self, model_obj, source_file, orig_name):
        save_path = model_obj.fs_path(self.variant)
        save_dir = os.path.dirname(save_path)

        if os.path.exists(save_path):
            log.warn('overwriting existing file: %s', save_path)

        if not os.path.exists(save_dir):
            log.debug('save_file(): creating directory %s', save_dir)

            try:
                os.makedirs(save_dir)
            except OSError as e:
                # this can happen if multiple files are uploaded concurrently
                if e.errno == errno.EEXIST:
                    pass
                else:
                    log.error('SaveFile: error [%s] creating directory: %s', e, save_dir)
                    raise # TODO

        try:
            with open(save_path, 'wb') as f:
                source_file.seek(0)
                while True:
                    data = source_file.read(8192)
                    if not data:
                        break
                    f.write(data)
        except Exception as e:
            log.error('SaveFile: error [%s] saving file: %s', e, save_path)
            raise # TODO


class MakeThumbnail(Handler):

    algos = {
        'keep-proportions': make_thumbnail_keep_proportions,
        'crop-to-size':     make_thumbnail_crop_to_size
    }

    def __init__(self, size, variant=None, quality=70, algo='keep-proportions'):
        self.algo = self.algos[algo]
        self.size = size
        self.variant = variant
        self.quality = quality

    def __call__(self, model_obj, source_file, orig_name):
        image = open_image(source_file)
        image = self.algo(image, self.size)
        save_image(image, model_obj, self.variant, self.quality)
