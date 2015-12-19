#coding: utf-8

from __future__ import absolute_import, division, unicode_literals, print_function

import logging
log = logging.getLogger(__name__)

import os
import errno
from urllib.parse import quote

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
import transaction

from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPBadRequest
from pyramid.view import view_config

from .exceptions import HandlerException


class StoreViews(object):
    """
    """
    # override in subclass. project-wide settings
    file_request_param = 'file'
    type_request_param = 'type'

    delegates = dict()  # {'group_name': {'delegate_name': delegate}}

    @classmethod
    def _get_delegate(cls, name, group='default'):
        try:
            return cls.delegates[group][name]
        except KeyError:
            log.error('StoreViews: group %r / entity %r not registered', group, delegate_name)
            raise HTTPNotFound()  # TODO ???

    @classmethod
    def register(cls, group='default'):
        """
        @StoreViews.register('site') class User(RestDelegate): pass
        """
        def decorate(delegate):
            if delegate.name is None:
                raise ValueError('RestViews.register(): %r must have attribute "name"' % delegate)

            if delegate.entity is None:
                raise ValueError('RestViews.register(): %r must have attribute "entity"' % delegate)

            if delegate.name in cls.delegates:
                raise ValueError('RestViews.register(): %r: name %r already registered for class %r' % (
                    delegate, delegate.name, cls.delegates[delegate.name]))

            if group not in cls.delegates:
                cls.delegates[group] = dict()

            cls.delegates[group][delegate.name] = delegate

            return delegate

        return decorate

    @classmethod
    def configure(cls, config, group='default', url_prefix='/rest', **kwargs):
        """
        RestViews.configure(config, group='site', url_prefix='/rest', factory=ebff('admin-panel'))
        """
        if group not in cls.delegates:
            if group == 'default':
                return
            else:
                raise RuntimeError('group %r does not exist' % group)

        for delegate_name, delegate in cls.delegates[group].items():
            # example: eor.store.default.user.get
            route_name = lambda suffix: 'eor.store.%s.%s.%s' % (group, delegate_name, suffix)

            def permission(method):
                if isinstance(delegate.permission, dict):
                    try:
                        return delegate.permission[method]
                    except KeyError:
                        return delegate.permission.get('*', None)
                else:
                    return delegate.permission

            # collection resource

            url_pattern = R'%s/%s' % (url_prefix, delegate_name)  # example: /rest/user

            config.add_route(route_name('get-novariant'), url_pattern + R'/{id}',
                             request_method='GET', **kwargs)
            config.add_route(route_name('get'), url_pattern + R'/{id}/{variant}',
                             request_method='GET', **kwargs)
            config.add_route(route_name('upload'), url_pattern,
                             request_method='POST', **kwargs)
            config.add_route(route_name('delete'), url_pattern,
                             request_method='DELETE', **kwargs)
            config.add_route(route_name('badmethod'), url_pattern, **kwargs)

            config.add_view(cls, attr='get_view', route_name=route_name('get-novariant'), permission=permission('get'))
            config.add_view(cls, attr='get_view', route_name=route_name('get'), permission=permission('get'))
            config.add_view(cls, attr='upload_view',  route_name=route_name('upload'), renderer='json',
                            decorator=cls.handler_decorator, permission=permission('upload'))
            config.add_view(cls, attr='delete_view',  route_name=route_name('delete'), renderer='json',
                            decorator=cls.handler_decorator, permission=permission('delete'))
            config.add_view(cls, attr='bad_method',  route_name=route_name('badmethod'), renderer='json')

    def __init__(self, request):
        self.request = request

        if not request.matched_route.name.startswith('eor.store'):
            log.error('StoreViews: bad route name: %r', request.matched_route.name)
            raise HTTPNotFound()

        route_name = request.matched_route.name.split('.')  # eor.rest.default.user.get
        group = route_name[2]
        delegate_name = route_name[3]

        self.delegate = self._get_delegate(delegate_name, group)(self)

        # handlers

        self.handlers = self.delegate.get_save_handlers()

        for handler in self.handlers:
            handler.register(self, self.delegate)

        # variants

        self.variants = self.delegate.get_variants()  # returns dict

        for name, variant in self.variants.items():
            variant.register(self, self.delegate, name)

    def get_view(self):
        file_id = self.request.matchdict['id']
        variant_name = self.request.matchdict.get('variant', None)

        try:
            model_obj = self.delegate.get_obj_by_id(file_id)
        except NoResultFound:
            raise HTTPNotFound()

        if variant_name is not None:

            try:
                variant = self.variants[variant_name]
            except KeyError as e:
                log.warn('StoreViews.get_view(): unknown variant: %s, name %s', variant_name, self.delegate.name)
                raise HTTPBadRequest()

            if not variant.file_exists(model_obj):
                try:
                    variant.create_from_file(model_obj)
                except HandlerException as e:
                    log.error(u'when generating variant: %s', e)
                    raise HTTPBadRequest()  # TODO response?

        return HTTPFound(location=quote(model_obj.url(variant_name)))

    def upload_view(self):

        # request parameterts

        try:
            fieldstorage = self.request.params[self.file_request_param]
        except (KeyError, ValueError) as e:
            log.warn('FileViews.upload_view(): request parameter not present: %s', e)
            raise HTTPBadRequest()

        if fieldstorage.file is None:
            log.warn('FileViews.upload_view(): bad file request parameter')
            raise HTTPBadRequest()

        source_file = fieldstorage.file
        orig_filename = fieldstorage.filename

        # create model object for the file

        obj = self.delegate.create_obj(orig_filename)

        try:
            obj.add()
        except SQLAlchemyError as e:
            log.error('FileViews.upload_view(): error persisting file object: %s', e)
            return {'status': 'error', 'code': 'database-error'}

        # run handlers

        for handler in self.handlers:
            try:
                handler(obj, source_file, orig_filename)
            except HandlerException as e:
                transaction.doom()
                log.exception(u'exception when saving file: %s', e)
                return e.response()
            except Exception as e:
                transaction.doom()
                log.exception(u'exception when saving file: %s', e)
                return {'status': 'error'}  # unknown error

        return {'status': 'ok', 'data': {'id': obj.id}}

    def delete_view(self):
        pass  # TODO


    # TODO error view! this catches all exceptions
    @classmethod
    def handler_decorator(cls, view_handler):

        def replacement(context, request):
            try:
                return view_handler(context, request)
            except Exception as e:
                #log.error('rest: unhandled exception: ', e)
                raise
                # TODO status?
                # return render_to_response('json', cls._error_response(exception=e), request=request)

        return replacement
