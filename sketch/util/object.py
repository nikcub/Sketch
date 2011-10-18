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
  Sketch.Util - object.py

  Object oriented utils

  This source file is subject to the new BSD license that is bundled with this 
  package in the file LICENSE.txt. The license is also available online at the 
  URL: <http://nikcub.appspot.com/bsd-license.txt>

  :copyright: Copyright (C) 2011 Nik Cubrilovic and others, see AUTHORS
  :license: new BSD, see LICENSE for more details.
"""

__version__ = '0.0.1'
__author__ = 'Nik Cubrilovic <nikcub@gmail.com>'

#---------------------------------------------------------------------------
#   Python Object Oriented Helper Functions
#---------------------------------------------------------------------------


def hasmethod(obj, meth):
  """
    Checks if an object, obj, has a callable method, meth
    
    return True or False
  """
  if hasattr(obj, meth):
    return callable(getattr(obj,meth))
  return False

def hasvar(obj, var):
  """
    Checks if object, obj has a variable var
    
    return True or False
  """
  if hasattr(obj, var):
    return not callable(getattr(obj, var))
  return False

def getmethattr(obj, meth):
  """
    Returns either the variable value or method invocation
  """
  if hasmethod(obj, meth):
    return getattr(obj, meth)()
  elif hasvar(obj, meth):
    return getattr(obj, meth)
  return None