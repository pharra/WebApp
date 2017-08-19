#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module packages the class add_route of module aiohttp."""

import functools
import logging
import asyncio
import inspect
import os
from aiohttp import web

class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional).
    '''
    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message


def request(path, method):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = method
        wrapper.__route__ = path
        return wrapper
    return decorator


get = functools.partial(request, method='GET')
post = functools.partial(request, method='POST')
put = functools.partial(request, method='PUT')
delete = functools.partial(request, method='DELETE')

class RequestHandler(object):
    def __init__(self, func):
        self._func = asyncio.coroutine(func)

    async def __call__(self, request):
        required_args = inspect.signature(self._func).parameters
        logging.info('required args: %s' %required_args)

        kw = {arg : value for arg, value in request.items() if arg in required_args}

        kw.update(request.match_info)

        if 'request' in required_args:
            kw['request'] = request

        for key, arg in required_args.items():

            if key == 'request' and arg.kind in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                return web.HTTPBadRequest(text='request parameter cannot be the var argument.')

            if arg.kind not in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):

                if arg.default == arg.empty and arg.name not in kw:
                    return web.HTTPBadRequest(text='Missing argument: %s' % arg.name)

        logging.info('call with args: %s' % kw)
        try:
            return await self._func(**kw)
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)

def add_routes(app, module_name):
    try:
        mod = __import__(module_name, fromlist=['get_submodule'])
    except ImportError as e:
        raise e
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        func = getattr(mod, attr)
        if callable(func) and hasattr(func, '__method__') and hasattr(func, '__route__'):
            args = ', '.join(inspect.signature(func).parameters.keys())
            logging.info('add route %s %s => %s(%s)' % (func.__method__, func.__route__, func.__name__, args))
            app.router.add_route(func.__method__, func.__route__, RequestHandler(func))


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
    app.router.add_static('/media/', path)
    logging.info('add static %s => %s' % ('/static/', path))