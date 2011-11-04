#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=2:sw=2:expandtab
#
# Copyright (c) 2011, Nik Cubrilovic. All rights reserved.
#
# <nikcub@gmail.com> <http://nikcub.appspot.com>  
#
# Licensed under a BSD license. You may obtain a copy of the License at
#
#     http://nikcub.appspot.com/bsd-license
#

"""
  Sketch - jinja helpers
  
  * compile templates to python (use in deploy scripts)
  * load compiled templates
  * custom template loader supporting template themes in subdirectories
  * template caching using GAE memcache
  * single enviroment cached across entire app

  @TODO write the custom loader to handle subdirs and subprojects and themes
  @TODO complete compiler
  @TODO option to compile into memcache
  @TODO implement admin interface on compiling
  @TODO monkey patch jinja to load compiled templates: http://paste.pocoo.org/show/124381/
"""

"""
  compile
  ~~~~~~~

  Compiles Jinja2 templates to python code. To compile a whole dir:

    from jinja2 import Environment
    from jinja2_compile import compile_dir

    env = Environment(extensions=['jinja2.ext.i18n'])
    src_path = '/path/to/templates'
    dst_path = '/path/to/templates_compiled'

    compile_dir(env, src_path, dst_path)

  :copyright: (c) 2009 Rodrigo Moraes <rodrigo.moraes@gmail.com>.
  :license: BSD, see LICENSE for more details.
"""

import os
import sys
import re
import sketch
import logging

from sketch.helpers.dateformat import *

try:
  from google.appengine.api import memcache as gae_memcache
  GAE_CACHE = True
except ImportError:
  GAE_CACHE = False

try:
  import jinja2
except ImportError:
  try:
    from sketch.vendor import jinja2
  except ImportError:
    logging.info('Could not import Jinja')
    logging.info(sys.path)
    raise sketch.exception.NotFound()
    
_jinja_env = None
_jinja_loaders = {}


class JinjaEnviroment(jinja2.Environment):
  def join_path(self, template, parent=None):
    if ':' in template:
      sep, template = template.split(':', 1)
      return "%s:%s/%s" % (sep, parent, template)
    elif '/' in parent:
      return os.path.normpath(os.path.join(parent, '..', template))
    else:
      return "%s/%s" % (parent, template)
    
    # return template
    # return template
    # return os.path.normpath(os.path.join(parent, '..', template))
    


class GAEMemcacheBytecodeCache(jinja2.BytecodeCache):
  def __init__(self, client=None, prefix='stash.jinja2.cache.', timeout=None):
    self.client = gae_memcache
    self.prefix = prefix
    self.timeout = timeout

  def load_bytecode(self, bucket):
    code = self.client.get(self.prefix + bucket.key)
    if code is not None:
      bucket.bytecode_from_string(code)

  def dump_bytecode(self, bucket):
    args = (self.prefix + bucket.key, bucket.bytecode_to_string())
    if self.timeout is not None:
      args += (self.timeout,)
    self.client.set(*args)


class CompiledLoader(jinja2.BaseLoader):
  """Load compiled jinja templates
  
  """
  def load(self, env, name, glob={}):
    source, filename, uptodate = self.get_source(environment, name)
    code = compile(source, filename, 'exec')
    return env.template_class.from_code(env, code, glob, uptodate)


class SubdirLoader(jinja2.BaseLoader):
  """A loader that is passed a dict of loaders where each loader is bound
  to a prefix.  The prefix is delimited from the template by a slash per
  default, which can be changed by setting the `delimiter` argument to
  something else::

    loader = PrefixLoader({
        'app1':     PackageLoader('mypackage.app1'),
        'app2':     PackageLoader('mypackage.app2')
    })

  By loading ``'app1/index.html'`` the file from the app1 package is loaded,
  by loading ``'app2/index.html'`` the file from the second.
  """

  def __init__(self, mapping, delimiter=':'):
    self.mapping = mapping
    self.delimiter = delimiter

  def get_source(self, environment, template):
    try:
      prefix, name = template.split(self.delimiter, 1)
      logging.info("Trying => %s %s" % (prefix, name))
      loader = self.mapping[prefix]
    except (ValueError, KeyError):
      raise jinja2.TemplateNotFound(template)
    try:
      return loader.get_source(environment, name)
    except jinja2.TemplateNotFound:
      # re-raise the exception with the correct fileame here.
      # (the one that includes the prefix)
      raise jinja2.TemplateNotFound(template)

  def list_templates(self):
    result = []
    for prefix, loader in self.mapping.iteritems():
      for template in loader.list_templates():
        result.append(prefix + self.delimiter + template)
    return result


def setup_cache():
  pass

def setup(template_paths={}, autoescape=False, cache_size=100, auto_reload=True, bytecode_cache=True):
  """Setup Jinja enviroment
  
  eg. sketch.jinja.setup({
      'app': self.config.paths['app_template_basedir'],
      'sketch': self.config.paths['sketch_template_dir'],
    })
  
  :param template_paths: Dictionary of paths to templates (template_name => template_path)
  :param autoescape: Autoescape
  :param cache_size:
  :param auto_reload:
  :param bytecode_cache: 
  """
  global _jinja_env, _jinja_loaders
  
  if not _jinja_env:
    _jinja_env = JinjaEnviroment(
      autoescape=autoescape,
      cache_size=cache_size,
      auto_reload=auto_reload,
      bytecode_cache=None)

  if bytecode_cache and GAE_CACHE:
    _jinja_env.bytecode_cache = GAEMemcacheBytecodeCache()

  if len(template_paths) > 1:
    loaders = {}
    for dirn, path in template_paths.items():
      loaders[dirn] = jinja2.FileSystemLoader(path)
      logging.info('jinja: add loader: %s %s' % (dirn, path))
    _jinja_env.loader = SubdirLoader(loaders)
  else:
    tp = template_paths['app']
    if tp in _jinja_loaders:
      _jinja_env.loader = _jinja_loaders[tp]
    else:
      _jinja_env.loader = _jinja_loaders[tp] = jinja2.FileSystemLoader(tp)


def render(template_name, vars={}, template_set='app', template_theme=None):
  """Given a template path, a template name and template variables
  will return rendered content using jinja2 library
  
  :param template_path: Path to template directory
  :param template_name: Name of template
  :param vars: (Optional) Template variables
  """
  global _jinja_env
  
  if not _jinja_env:
    raise 'Jinja env not setup'

  _jinja_env.filters['timesince'] = timesince
  _jinja_env.filters['timeuntil'] = timeuntil
  _jinja_env.filters['date'] = date_format
  _jinja_env.filters['time'] = time_format
  _jinja_env.filters['shortdate'] = short_date
  _jinja_env.filters['isodate'] = iso_date
  _jinja_env.filters['rfcdate'] = rfc2822_date
  _jinja_env.filters['dtformat'] = datetimeformat
  _jinja_env.filters['timestamp'] = timestamp
  
  _template_name = "app:%s.html" % (template_name)
  template = _jinja_env.get_template(_template_name, parent=template_theme)
  
  return template.render(vars)


def compile_file(env, src_path, dst_path, encoding='utf-8', base_dir=''):
  """Compiles a Jinja2 template to python code.

  :param env: a Jinja2 Environment instance.
  :param src_path: path to the source file.
  :param dst_path: path to the destination file.
  :param encoding: template encoding.
  :param base_dir: the base path to be removed from the compiled template filename.
  """
  src_file = file(src_path, 'r')
  source = src_file.read().decode(encoding)
  name = src_path.replace(base_dir, '')
  raw = env.compile(source, name=name, filename=name, raw=True)
  src_file.close()

  dst_file = open(dst_path, 'w')
  dst_file.write(raw)
  dst_file.close()


def compile_dir(env, src_path, dst_path, pattern=r'^.*\.html$', encoding='utf-8', base_dir=None):
  """Compiles a directory of Jinja2 templates to python code.
  
  :param env: a Jinja2 Environment instance.
  :param src_path: path to the source directory.
  :param dst_path: path to the destination directory.
  :param encoding: template encoding.
  :param base_dir: the base path to be removed from the compiled template filename.
  """
  from os import path, listdir, mkdir
  file_re = re.compile(pattern)

  if base_dir is None:
    base_dir = src_path

  for filename in listdir(src_path):
    src_name = path.join(src_path, filename)
    dst_name = path.join(dst_path, filename)

    if path.isdir(src_name):
      mkdir(dst_name)
      compile_dir(env, src_name, dst_name, encoding=encoding, base_dir=base_dir)
    elif path.isfile(src_name) and file_re.match(filename):
      compile_file(env, src_name, dst_name, encoding=encoding, base_dir=base_dir)
