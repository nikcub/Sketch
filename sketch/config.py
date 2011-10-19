#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sketch Config class

Support reading configuration files from the following file formats:
  * YAML (with file extension .yaml or .yml)
  * JSON (with file extension .json or .js)
  * INI (extension .ini)
  * Text (with extension .txt or .cnf)
  * XML (not yet implemented but will be)

Supports caching to
  * Local memcache
  * Google App Engine memcache
  * Google App Engine db objects

Supports deployment environments by default: dev, staging, production

Requires: sketch/cache.py

# TODO implement different types of config as well as caching classes
"""

import os
import sys
import yaml
import logging

from sketch.vendor import stash
from sketch.vendor.stash import cache as old_cache

try:
  from sketch.vendor.stash import handler as cache_handler
except ImportError:
  logging.info('Config: no cache configured')


__all__ = ['Config']

class ConfigFileError(Exception): pass

class ConfigCacheError(Exception): pass

class ConfigParseError(Exception): pass

class Config(dict):

  cache_key = "sketch.config.two"
  cache_timeout = 60 * 60
  dirty = True

  # TODO implement config defaults
  # TODO implement cascading cache using Stash
  # TODO abstract this object and Session into Stash.util.dict
  # TODO fix save config
  def __init__(self, config_file_path=False, config_data={}, cache_options = {}, refresh = False):
    self.data = config_data
    self.cache_handler = cache_handler()

    if config_file_path and os.path.isfile(config_file_path):
      self.load_config(config_file_path, refresh)

  def __repr__(self): return repr(self.data)
  def __len__(self): return len(self.data)
  def clear(self): self.data.clear()
  def copy(self): return self.data.copy()
  def keys(self): return self.data.keys()
  def items(self): return self.data.items()
  def iteritems(self): return self.data.iteritems()
  def iterkeys(self): return self.data.iterkeys()
  def itervalues(self): return self.data.itervalues()
  def values(self): return self.data.values()
  def has_key(self, key): return key in self.data

  def get(self, key, default = None):
    if key not in self:
      return default
    return self[key]

  def __str__(self):
    return str(self.data)

  def __delitem__(self, key):
    del self.data[key]
    self.dirty = True

  def __getitem__(self, key):
    if key in self.data:
      return self.data[key]
    raise KeyError(key)

  def __setitem__(self, key, val):
    if type(val) is dict:
      val = Config(config_data=val)
    self.data[key] = val
    self.dirty = True
    

  def __getattr__(self, key):
    return self.get(key)

  def __contains__(self, key):
    return key in self.data

  def __iter__(self):
    return iter(self.data)

  def save(self):
    if self.active and self.dirty:
      stash.set(self.cache_key, self.data)
      self.dirty = False

  def load_config(self, file_name, refresh=False):
    conf = stash.get(self.cache_key)
    if not conf or refresh:
      conf = self.load_file(file_name, refresh)
    self.parse_config(conf)

  # @stash.Cache
  def load_file(self, file_name, refresh=False):
    file_contents = open(file_name, 'r')
    conf_parsed = yaml.load(file_contents)
    return conf_parsed

  def parse_config(self, conf):
    if type(conf) != dict:
      raise ConfigParseError, "Could not parse cached config"
    self.data = conf
    
  def save_config(self):
    stash.set(self.cache_key, self.data)
