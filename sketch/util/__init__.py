#!/usr/bin/env python
#
# Copyright (c) 2010-2011, Nik Cubrilovic. All rights reserved.
# <nikcub@gmail.com> <http://nikcub.appspot.com>  
#

"""Sketch Utility methods


  TODO  break up into packages  
"""

import random
import logging
import urllib
import urlparse
import posixpath
import re
import hashlib

from .object import hasmethod, hasvar, getmethattr
from .security import bcrypt, file_hash, generate_password

from sketch.vendor.BeautifulSoup import BeautifulSoup
import sketch.vendor.feedparser

feed_content_types = ['text/xml', 'application/rss+xml', 'application/atom+xml']
_format_re = re.compile(r'\$(?:(%s)|\{(%s)\})' % (('[a-zA-Z_][a-zA-Z0-9_]*',) * 2))

try:
  from email.utils import formatdate
  def HTTPDate(timeval=None):
    return formatdate(timeval, usegmt=True)
except ImportError:
  from rfc822 import formatdate as HTTPDate

def extract_dataurl(dataurl):
  if not dataurl[:5] == 'data:':
    return (None, None)
  img_index = dataurl.index(',')
  if not img_index:
    return (None, None)

  img_type = dataurl[5:img_index].split(';')[0]
  img_dat_enc = dataurl[img_index + 1:]

  import base64
  img_dat = base64.decodestring(img_dat_enc)
  return (img_dat, img_type)




def urlunsplit(scheme=None, netloc=None, path=None, query=None, fragment=None):
  """Similar to ``urlparse.urlunsplit``, but will escape values and
  urlencode and sort query arguments.

  :param scheme:
    URL scheme, e.g., `http` or `https`.
  :param netloc:
    Network location, e.g., `localhost:8080` or `www.google.com`.
  :param path:
    URL path.
  :param query:
    URL query as an escaped string, or a dictionary or list of key-values
    tuples to build a query.
  :param fragment:
    Fragment identifier, also known as "anchor".
  :returns:
    An assembled absolute or relative URL.
  """
  if not scheme or not netloc:
    scheme = None
    netloc = None

  if path:
    path = urllib.quote(to_utf8(path))

  if query and not isinstance(query, basestring):
    if isinstance(query, dict):
      query = query.items()

    query_args = []
    for key, values in query:
      if isinstance(values, basestring):
        values = (values,)

      for value in values:
        query_args.append((to_utf8(key), to_utf8(value)))

    # Sorting should be optional? Sorted args are commonly needed to build
    # URL signatures for services.
    query_args.sort()
    query = urllib.urlencode(query_args)

  if fragment:
    fragment = urllib.quote(to_utf8(fragment))

  return urlparse.urlunsplit((scheme, netloc, path, query, fragment))




def escape(s, quote=False):
  """Replace special characters "&", "<" and ">" to HTML-safe sequences.  If
  the optional flag `quote` is `True`, the quotation mark character (") is
  also translated.

  There is a special handling for `None` which escapes to an empty string.

  :param s: the string to escape.
  :param quote: set to true to also escape double quotes.
  """
  if s is None:
    return ''
  elif hasattr(s, '__html__'):
    return s.__html__()
  elif not isinstance(s, basestring):
    s = unicode(s)
  s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
  if quote:
    s = s.replace('"', "&quot;")
  return s

def test_normalize_url():
  urls = [
  # 'example.com',
  # 'example.com/',
  # 'http://example.com/',
  # 'http://example.com',
  # 'http://example.com?',
  # 'http://example.com/?',
  # 'http://example.com//',
  # 'http://example.com/a',
  # 'http://example.com/a/',
  # 'http://example.com/a/?',
  # 'http://example.com/a/../',
  # 'http://example.com/a/../?',
  # 'http://example.com/a/b/../?',
  # 'http://example.com/a/../',
  # 'http://example.com/a/b/?z=1',
  'http://example.com/a/?',
  'http://@example.com/a/?',
  'http://example.com:/a/?',
  'http://@example.com:/a/?',
  'http://example.com:80/a/?',
  ]

  for url in urls:
    print "%s \t\t\t\t\t\tclean: %s" % (url, normalize_url(url))


def normalize_url(s, charset='utf-8'):
  """
  function that attempts to mimic browser URL normalization.

  Partly taken from werkzeug.utils

  <http://www.bitbucket.org/mitsuhiko/werkzeug-main/src/tip/werkzeug/utils.py>

  There is a lot to URL normalization, see:

  <http://en.wikipedia.org/wiki/URL_normalization>

  :param charset: The target charset for the URL if the url was
               given as unicode string.
  """
  if isinstance(s, unicode):
   s = s.encode(charset, 'ignore')
  scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
  # print "scheme: %s\n netloc:%s\n path:%s\n qs:%s\n anchor:%s\n" % (scheme, netloc, path, qs, anchor)
  path = urllib.unquote(path)
  if not netloc:
    netloc = path.strip("/\\:?&")
    path = '/'
  if not scheme:
    scheme = "http"
  if not path:
    path = '/'
  netloc = netloc.strip("/\\:@?&")
  path = posixpath.normpath(path)
  path = urlparse.urljoin('/', path)
  # path = urllib.quote(path, '/%')
  qs = urllib.quote_plus(qs, ':&=')
  # print "scheme: %s\n netloc:%s\n path:%s\n qs:%s\n anchor:%s\n" % (scheme, netloc, path, qs, anchor)
  return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))


def get_content_type(req_headers):
    """
        Reads a dictionary of request headers and extracts content type and charset
    """
    header_ct = req_headers['content-type'].split('; ')
    content_type = header_ct[0]
    if len(header_ct) > 1:
        content_charset = header_ct[1].split('=')[1]
    else:
        content_charset = 'UTF-8'

    return content_type, content_charset

def discover_feed_hub(content):
    d = sketch.feedparser.parse(content)
    hub_list = []
    if not d['feed'].has_key('links'):
        return False
    for link in d['feed']['links']:
        if link['rel'] == 'hub':
            hub_list.append(link['href'])
    if len(hub_list) > 0:
        return hub_list
    return False


def discover_feed_self(content):
    d = sketch.feedparser.parse(content)
    if d['feed'].has_key('links'):
        for link in d['feed']['links']:
            if link['rel'] == 'self':
                return link['href']
    return None


def get_feed_title(content):
    d = sketch.feedparser.parse(content)
    if d['feed'].has_key('title'):
        return d['feed'].title
    return None

def get_page_title(content):
    s = BeautifulSoup(content)
    return s.find('title').text

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def remove_extra_spaces(data):
    p = re.compile(r'\s+')
    return p.sub(' ', data)

def discover_feeds(content, base_href = ""):
    """
        Given HTML content will attempt to auto-discover all feed links, both RSS and Atom
    """
    s = BeautifulSoup(content)
    t = s.findAll('link', rel='alternate')

    if not t:
        return False

    feeds_list = []
    title = ""

    for e in t:
        if not e.has_key('href') or not e.has_key('type'):
            logging.info("discover_feeds: Found an alternate that doesn't have a href or type: %s" % e)
            continue

        if not e['type'] in feed_content_types:
            logging.info("discover_feeds: Found an alternate that doesn't have right content type: %s" % e['type'])
            continue

        # TODO: Work out base_href here, when we put it in etc.
        # have to detect if we have a path or a
        # atm we just check for '/' - err
        feed_url = str(e['href'])
        if feed_url.startswith('/'):
            feed_url = base_href + e['href']

        feed = {
            "url": feed_url,
            "type": e['type']
        }

        if e.has_key('title'):
            feed['title'] = e['title']

        feeds_list.append(feed)

    if len(feeds_list) == 0:
        return False

    return feeds_list

def redirect(location, code = 302):
  assert code in (301, 302, 303, 305, 307), 'invalid code'
  from sketch import Response
  display_location = location
  response = Response(
    '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
    '<title>Redirecting...</title>\n'
    '<h1>Redirecting...</h1>\n'
    '<p>You should be redirected automatically to target URL: '
    '<a href="%s">%s</a>.    If not click the link.' %
    (location, display_location), code, mimetype='text/html')
  response.headers['Location'] = location
  return response

def format_string(string, context):
  """String-template format a string:

  >>> format_string('$foo and ${foo}s', dict(foo=42))
  '42 and 42s'

  This does not do any attribute lookup etc.  For more advanced string
  formattings have a look at the `werkzeug.template` module.

  :from: werkzeug.util
  :param string: the format string.
  :param context: a dict with the variables to insert.
  """
  def lookup_arg(match):
    x = context[match.group(1) or match.group(2)]
    if not isinstance(x, basestring):
      x = type(string)(x)
    return x
  return _format_re.sub(lookup_arg, string)



#---------------------------------------------------------------------------
#   Modules, Packages, etc.
#---------------------------------------------------------------------------


def import_string(import_name, silent=False):
  """Imports an object based on a string.  This is useful if you want to
  use import paths as endpoints or something similar.  An import path can
  be specified either in dotted notation (``xml.sax.saxutils.escape``)
  or with a colon as object delimiter (``xml.sax.saxutils:escape``).

  If `silent` is True the return value will be `None` if the import fails.

  from werkzeug.util

  :param import_name: the dotted name for the object to import.
  :param silent: if set to `True` import errors are ignored and
                               `None` is returned instead.
  :return: imported object
  """
  # force the import name to automatically convert to strings
  if isinstance(import_name, unicode):
    import_name = str(import_name)
  try:
    if ':' in import_name:
      module, obj = import_name.split(':', 1)
    elif '.' in import_name:
      module, obj = import_name.rsplit('.', 1)
    else:
      return __import__(import_name)
    # __import__ is not able to handle unicode strings in the fromlist
    # if the module is a package
    if isinstance(obj, unicode):
      obj = obj.encode('utf-8')
    return getattr(__import__(module, None, None, [obj]), obj)
  except (ImportError, AttributeError):
    logging.info('Import Error: Could not load module %s' % import_name)
    if not silent:
      raise

def set_package(self, package_dir):
  """Find all packages in a directory and add them to import paths so that 
  they can be imported by the application
  
  :param package_dir: the package directory
  """
  for filename in os.listdir(package_dir):
    if filename.endswith((".zip", ".egg")):
      sys.path.insert(0, "%s/%s" % (package_dir, filename))


def clear_path(self):
  sys.path = [path for path in sys.path if 'site-packages' not in path]


def iter_modules(path):
  """Iterate over all modules in a package.
  :from: werkzeug._internal
  """
  import os
  import pkgutil
  if hasattr(pkgutil, 'iter_modules'):
    for importer, modname, ispkg in pkgutil.iter_modules(path):
      yield modname, ispkg
    return
  from inspect import getmodulename
  from pydoc import ispackage
  found = set()
  for path in path:
    for filename in os.listdir(path):
      p = os.path.join(path, filename)
      modname = getmodulename(filename)
      if modname and modname != '__init__':
        if modname not in found:
          found.add(modname)
          yield modname, ispackage(modname)


def find_modules(import_path, include_packages=False, recursive=False):
  """Find all the modules below a package.    This can be useful to
  automatically import all views / controllers so that their metaclasses /
  function decorators have a chance to register themselves on the
  application.

  Packages are not returned unless `include_packages` is `True`.  This can
  also recursively list modules but in that case it will import all the
  packages to get the correct load path of that module.

  :param import_name: the dotted name for the package to find child modules.
  :param include_packages: set to `True` if packages should be returned, too.
  :param recursive: set to `True` if recursion should happen.
  :return: generator
  """
  module = import_string(import_path)
  path = getattr(module, '__path__', None)
  if path is None:
    raise ValueError('%r is not a package' % import_path)
  basename = module.__name__ + '.'
  for modname, ispkg in _iter_modules(path):
    modname = basename + modname
    if ispkg:
      if include_packages:
        yield modname
      if recursive:
        for item in find_modules(modname, include_packages, True):
          yield item
    else:
      yield modname


def import_object(name):
  """Imports an object by name.

  import_object('x.y.z') is equivalent to 'from x.y import z'.

  >>> import tornado.escape
  >>> import_object('tornado.escape') is tornado.escape
  True
  >>> import_object('tornado.escape.utf8') is tornado.escape.utf8
  True
  """
  parts = name.split('.')
  obj = __import__('.'.join(parts[:-1]), None, None, [parts[-1]], 0)
  return getattr(obj, parts[-1])

def import_string_two(import_name, silent=False):
  """Imports an object based on a string. If *silent* is True the return
  value will be None if the import fails.

  Simplified version of the function with same name from `Werkzeug`_.

  :param import_name:
    The dotted name for the object to import.
  :param silent:
    If True, import errors are ignored and None is returned instead.
  :returns:
    The imported object.
  """
  import_name = to_utf8(import_name)
  try:
    if '.' in import_name:
      module, obj = import_name.rsplit('.', 1)
      return getattr(__import__(module, None, None, [obj]), obj)
    else:
      return __import__(import_name)
  except (ImportError, AttributeError):
    if not silent:
      raise



#---------------------------------------------------------------------------
#   HTTP, etc.
#---------------------------------------------------------------------------


def abort_old(code, *args, **kwargs):
  """Raises an ``HTTPException``. The exception is instantiated passing
  *args* and *kwargs*.

  :param code:
      A valid HTTP error code from ``webob.exc.status_map``, a dictionary
      mapping status codes to subclasses of ``HTTPException``.
  :param args:
      Arguments to be used to instantiate the exception.
  :param kwargs:
      Keyword arguments to be used to instantiate the exception.
  """
  cls = webob.exc.status_map.get(code)
  if not cls:
    raise KeyError('No exception is defined for code %r.' % code)

  raise cls(*args, **kwargs)


def get_valid_methods(handler):
  """Returns a list of HTTP methods supported by a handler.

  :param handler:
    A :class:`RequestHandler` instance.
  :returns:
    A list of HTTP methods supported by the handler.
  """
  return [method for method in Application.ALLOWED_METHODS if getattr(handler,
    method.lower().replace('-', '_'), None)]



#---------------------------------------------------------------------------
#   Unicode, Character Encoding
#---------------------------------------------------------------------------


def to_utf8(value):
  """Returns a string encoded using UTF-8.

  This function comes from `Tornado`_.

  :param value:
    A unicode or string to be encoded.
  :returns:
    The encoded string.
  """
  if isinstance(value, unicode):
    return value.encode('utf-8')

  assert isinstance(value, str)
  return value


def to_unicode(value):
  """Returns a unicode string from a string, using UTF-8 to decode if needed.

  This function comes from `Tornado`_.

  :param value:
    A unicode or string to be decoded.
  :returns:
    The decoded string.
  """
  if isinstance(value, str):
    return value.decode('utf-8')

  assert isinstance(value, unicode)
  return value

