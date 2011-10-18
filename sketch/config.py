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

  cache_key = "sketch.config"
  cache_timeout = 60 * 60

  # TODO implement config defaults
  def __init__(self, config_file_path, cache_options = {}, refresh = False):
    self.cache_handler = cache_handler()

    if os.path.isfile(config_file_path):
      self.load_config(config_file_path, refresh)

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

    dict.__init__(self, conf)
    
  def save_config(self):
    stash.set(self.cache_key, self)
