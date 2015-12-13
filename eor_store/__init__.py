# coding: utf-8

from .config import config
from .views import StoreViews
from .delegate import StoreDelegate
from .model import File

from .handlers import (
    SaveFile,
    MakeThumbnail,
    SetOwner
)


def includeme(config):
    settings = config.get_settings()

    from eor.utils.settings import ParseSettings

    (ParseSettings(settings, prefix='eor-store.')
        .path('path', default='../store'))
