#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=2:sw=2:expandtab
#
# Copyright (c) 2010-2011, Nik Cubrilovic. All rights reserved.
#
# <nikcub@gmail.com> <http://nikcub.appspot.com>  
#
# Licensed under a BSD license. You may obtain a copy of the License at
#
#     http://nikcub.appspot.com/bsd-license
#
"""
  Sketch - messages.py

  implement user messages

  This source file is subject to the new BSD license that is bundled with this 
  package in the file LICENSE.txt. The license is also available online at the 
  URL: <http://nikcub.appspot.com/bsd-license.txt>

  :copyright: Copyright (C) 2011 Nik Cubrilovic and others, see AUTHORS
  :license: new BSD, see LICENSE for more details.
"""

__version__ = '0.0.1'
__author__ = 'Nik Cubrilovic <nikcub@gmail.com>'


# Do stackexchange style messages across top of page


# TODO make flash messages a module
class Messages(object):
  info = "info"
  warning = "warning"
  error = "error"

