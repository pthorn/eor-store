# coding: utf-8

from __future__ import absolute_import, division, unicode_literals, print_function

import logging
log = logging.getLogger(__name__)

import os
import errno
import math

from PIL import Image

from .exceptions import FileException, NotAnImageException


def get_image_format(file_obj):
    ext = os.path.splitext(file_obj.filename)[1]
    if ext.lower() in('.gif', '.png'):
        return 'png'
    else:
        return 'jpg'


def open_image(source_file):
    try:
        image = Image.open(source_file)
    except IOError as e:
        if str(e).find('annot identify image file') != -1:
            raise NotAnImageException(exc=e)
        else:
            raise FileException(exc=e)

    if image.mode != 'RGB':
        image.convert('RGB')

    return image


def make_thumbnail_crop_to_size(image, size):
    image = image.copy()

    # calculate crop window centered on image
    # TODO!!! won't work if original is smaller than thumbnail

    factor = min(float(image.size[0]) / size[0],  float(image.size[1]) / size[1])
    crop_size = (size[0] * factor, size[1] * factor)

    crop = (
        math.trunc((image.size[0] - crop_size[0]) / 2),
        math.trunc((image.size[1] - crop_size[1]) / 2),
        math.trunc((image.size[0] + crop_size[0]) / 2),
        math.trunc((image.size[1] + crop_size[1]) / 2)
    )

    #print '\n----------', 'image.size', image.size, 'thumb_def.size', thumb_def.size, 'factor', factor, 'crop_size', crop_size, 'crop', crop

    image = image.crop(crop)
    image.thumbnail(size, Image.ANTIALIAS)

    return image


def make_thumbnail_keep_proportions(image, size):
    image = image.copy()

    if image.size[0] > size[0] or image.size[1] > size[1]:
            image.thumbnail(size, Image.ANTIALIAS)

    return image


def save_image(image, save_path, quality):
    """
    """

    if os.path.exists(save_path):
        log.warn('overwriting existing image: %s', save_path)

    save_dir = os.path.dirname(save_path)
    if not os.path.exists(save_dir):
        #log.warn('save_uploaded_image(): creating directory %s', save_dir)
        try:
            os.makedirs(save_dir)
        except OSError as e:
            # this can happen if multiple images are uploaded concurrently
            if e.errno == errno.EEXIST:
                pass
            else:
                raise

    image.save(save_path, quality=quality)

    #webob_obj.file.close()
