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

import sys
import os

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
from .debug import Handler as debug_handler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vendor'))
