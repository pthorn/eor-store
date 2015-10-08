# config: utf-8

from __future__ import absolute_import, division, unicode_literals, print_function

import logging
log = logging.getLogger(__name__)


class HandlerException(Exception):

    def __init__(self, code=None, msg=None):
        self.code = code
        self.msg = msg

    def response(self):
        resp = {'status': 'error'}

        if self.code:
            resp['code'] = self.code
        if self.msg:
            resp['message'] = self.msg

        return resp


class NotAnImageException(HandlerException):
    pass

