#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import re, time, json, logging, hashlib, base64, asyncio


from aiohttp import web

from coroweb import get, post



@get('/')
def index(request):
    return {
        '__template__': 'index.html',
        'index': index
    }

