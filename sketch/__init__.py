#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sketch
    =======

    __init__.py

    A simple and portable python web application framework

    :homepage: <http://bitbucket.org/nik/sketch>
    :author: Nik Cubrilovic <nikcub@gmail.com>
    :copyright: (c) 2011 by Nik Cubrilovic and others, see AUTHORS for more details.
    :license: 3-clause BSD, see LICENSE for more details.
"""

__version__ = '0.0.1'
__author__ = "Nik Cubrilovic <nikcub@gmail.com>"
__license__ = "BSD 3-clause"

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'sketch.django_settings'

import os
import sys

# import cgi
# import datetime
# import time
# import urllib
# import urlparse
# import webob
# import webob.exc
# from Cookie import BaseCookie

import exception
import serialize
import util

from .webapp import Request, Response, RequestHandler, RedirectHandler
from .router import BaseRoute, SimpleRoute, Route, Router
from .config import Config
from .controllers import BaseController, AdminController
from .messages import Messages
from .session import Session
from .model import Model
from .application import Application
from .users import User

from google.appengine.dist import use_library
use_library('django', '0.96')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vendor'))
from vendor.diffbot import DiffBot
from vendor import jinja2

from django.utils import simplejson as json

# GAE
# from google.appengine.ext import webapp
# from google.appengine.ext import blobstore
# from google.appengine.ext.webapp import template
# from google.appengine.api import memcache
# from google.appengine.runtime import DeadlineExceededError
