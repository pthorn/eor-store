# config: utf-8

from __future__ import absolute_import, division, unicode_literals, print_function

import logging
log = logging.getLogger(__name__)


class HandlerException(Exception):

    def __init__(self, code=None, msg=None, exc=None):
        self.code = code
        self.msg = msg
        self.exc = exc

    def __str__(self):
        if self.exc:
            return self.__class__.__name__ + ': ' + str(self.exc)
        else:
            return self.__class__.__name__

    def response(self):
        resp = {'status': 'error'}

        if self.code:
            resp['code'] = self.code

        if self.msg:
            resp['message'] = self.msg
        else:
            resp['message'] = self.__class__.__name__

        return resp


class NotAnImageException(HandlerException):

    def __init__(self, exc=None):
        super().__init__(code='not-an-image', exc=exc)


class FileException(HandlerException):

    def __init__(self, exc=None):
        super().__init__(code='file-error', exc=exc)
