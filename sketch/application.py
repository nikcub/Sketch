import os
import types
import sys
import logging
import traceback

from os.path import join as j_dir
from os.path import dirname

import sketch

from .util import import_string

from google.appengine.ext.webapp.util import run_bare_wsgi_app
from google.appengine.ext.webapp import WSGIApplication
from google.appengine.runtime import DeadlineExceededError
from google.appengine.api import app_identity

class AppAuthError(Exception):
  pass

class SketchException(Exception):
  pass

class Application(object):
  """
  Sketch base Application class. Implements WSGI interface and will dispatch requests
  
  example.
  
  """

  ALLOWED_METHODS = frozenset(['GET', 'POST', 'HEAD', 'OPTIONS', 'PUT', 'DELETE', 'TRACE'])

  static_uri = '/static'

  vendor_path = 'vendor'

  app_template_folder = 'templates'

  sketch_template_folder = 'templates'

  app_template_path = None

  sketch_template_path = None

  # pointer to app instance
  app = None

  # pointer to current active app instance
  active_app = None

  # pointer to current response
  response = None

  _Plugins = {}

  plugins_registered = False

  #: Default class used for the request object.
  request_class = sketch.Request
  
  #: Default class used for the response object.
  response_class = sketch.Response
  
  #: Default class used for the router object.
  router_class = sketch.Router
  
  #: Default class used for the config object.
  config_class = sketch.Config
  
  #: Request variables.
  active_instance = app = request = None

  def __init__(self, config_file = "sketch.yaml", app_name = None, debug = False, routes = None):
    """Application object constructor
    
    :param config_file: (optional) full path to configuration file
    :param app_name: (optional) name of application
    :param debug: (optional) debug mode for the aplication
    :param routes: (optional) default routes
    """
    # Config
    # @TODO try loading default config if none specified
    # @TODO intelligent caching so that we don't always reparse config
    if not os.path.isfile(config_file):
      raise Exception("Not a valid project_path %s" % config_file)
    self.config = sketch.Config(config_file, refresh = debug)

    # Appname
    # @TODO do away with appname
    self.app_name = self.config.get('appname', False) or app_name
    if not self.app_name:
      raise Exception, "Could not get application name"

    # Plugins
    if 'plugins' in self.config:
      plugins = self.import_app_module('plugins', 'plugins', silent = True)
      self._init_plugins(plugins)

    # Routing
    self.routes = self.get_routes()
    self.router = self.router_class(self, self.routes)

    # Config
    self.config = self.set_config_paths(self.config)
    self.config = self.set_config_template_paths(self.config)
    # @TODO fix save config
    # self.config.save_config()

    self.set_vendor()

    self._handlers = {}
    Application.app = self


  def get_routes(self, routes = None):
    """Imports routes for the application
    
    Returns a dictionary of routes imported from a module or file
    
    :param routes: (optional) path to module or object with routing info
    """
    return self.import_app_module_new('routes', 'routes')


  def set_environ(self, enviroments):
    """Returns the running environment and sets debug options, hostname etc.
    
    :param env: Defined environments in config
    """
    enviro_set = False
    self.config.hostname = hostname = self.get_current_hostname()
    self.config.appid = app_identity.get_application_id()
    self.config.gae_hostname = app_identity.get_default_version_hostname()
    
    for env in enviroments:
      self.config['enviroments'][env]['name'] = env
      if 'hosts' in enviroments[env] and hostname in enviroments[env]['hosts']:
        self.config.set_enviro = env
        enviro_set = True
    
    # logging.info(self.config.enviro)
    # logging.info("%s - %s - %s" % (hostname, id_gae, host_gae))
    # self.debug = self.config.get('debug', debug)
    # self.debug = debug or os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')


  def setup_logging(self, debug=False):
    """Setup application logging level based on being in debug mode or not
    
    :param debug: (optional) If debug is one then log more info
    """
    if debug:
      logging.getLogger().setLevel(logging.INFO)


  def set_config_paths(self, config):
    """Sets path information in the :class:`Config` object.
    
    Returns the new :class:`Config` object
    
    :param config: Config object to add path information to
    """
    config = self.assure_obj_child_dict(config, 'paths')
    
    paths = {}
    paths['sketch_base_dir'] = sketch_dir = dirname(__file__)
    paths['site_base_dir'] = site_dir = j_dir(dirname(__file__), '..')
    paths['app_base_dir'] = app_dir = j_dir(site_dir, self.app_name)
    paths['sketch_template_dir'] = j_dir(sketch_dir, self.sketch_template_folder)
    paths['app_template_basedir'] = j_dir(app_dir, self.sketch_template_folder)
    paths['app_template_default'] = j_dir(app_dir, self.sketch_template_folder, 'default')
    
    for path in paths:
      p = os.path.normpath(paths[path])
      if os.path.isdir(p) and not path in config['paths']:
        config['paths'][path] = p

    return config


  def set_config_template_paths(self, config):
    """Sets the paths to templates in the config
    
    Returns a new :class:`Config` object
    
    :param config: Config object
    """
    config['paths'] = self.assure_obj_child_dict(config['paths'], 'templates')
    templates = {}

    for template in config.templates:
      p = os.path.normpath(j_dir(config.paths.site_base_dir, config.templates[template]))
      if os.path.isdir(p):
        config['paths']['templates'][template] = p
    
    return config


  def assure_obj_child_dict(self, obj, var):
    """Assure the object has the specified child dict
    """
    if not var in obj or type(obj[var]) != type({}):
      obj[var] = {}
    return obj


  def set_vendor(self, vendor_dir = None):
    """Sets a vendor directory containing third-party modules and files into the 
    system path so that they can be imported directly
    
    :param vendor_dir: full path to directory to import
    """
    if not vendor_dir:
      vendor_dir = os.path.join(os.path.dirname(__file__), self.vendor_path)
    if os.path.isdir(vendor_dir):
      sys.path.insert(0, vendor_dir)


  def get_current_hostname(self, port=False):
    """Returns the current hostname 
    
    :param port: (optional) include port information
    """
    if self.request and 'HTTP_HOST' in self.request.environ:
      host_full = self.request.environ['HTTP_HOST'] or 'localhost'
      hostname = host_full.split(':')[0]
    else:
      hostname = 'localhost'
    
    return hostname


  @property
  def debug(self):
    """Conveniance method to return current debug level
    
    """
    if 'debug' in self.config:
      return self.config.debug
    return False

  def import_app_module_new(self, module, obj = None):
    # TODO work out what went wrong here
    mod = __import__('%s.%s' % (self.app_name, module), globals(), None, self.app_name)
    return getattr(mod, obj)

  def import_app_module(self, module, obj = None, silent = False):
    # TODO do some sanitation on import and move the import_string module over
    imp = "%s.%s" % (self.app_name, module)
    if obj:
      imp = "%s:%s" % (imp, obj)
    try:
      ret = import_string(imp, silent)
    except AttributeError, e:
      logging.info("Import Error: %s" % str(e))
      return None
    return ret

  def _init_plugin_class(self, plugin_name):
    fromlist = [plugin_name]
    try:
      module = __import__("plugins.%s.%s" % (plugin_name, plugin_name), globals(), {}, fromlist)
    except ImportError:
      module = __import__("plugins.%s" % (plugin_name), globals(), {}, fromlist)

    return getattr(module, plugin_name)()

  def _init_plugins(self, plugins):
    if plugins:
      for plugin in plugins:
        # try:
        plug_inst = self._init_plugin_class(plugin)
        if plug_inst.set_config(plugins[plugin]):
            self._Plugins[plugin] = plug_inst
        # except ImportError, e:
            # logging.error('could not import pluging %s: %s' % (plugin, e))
        # except Exception, e:
            # logging.error('Exception: %s' % e)
    else:
      self.plugins_registered = False

  # TODO : implement
  def _safe_import(self, module_name):
    try:
      module = __import__("plugins.%s.%s" % (plugin_name, plugin_name), globals(), {}, fromlist)
    except ImportError:
      module = __import__("plugins.%s" % (plugin_name), globals(), {}, fromlist)
    return getattr(module, plugin_name)()

  def _init_project(self, url_mapping, plugins, debug=False):
    pass


  # TODO implement GAE warmup
  def warmup(self):
    """
        Very cool feature which will warm up and prime the caches etc. via a GET req
    """
    # add route /_ah/warmup
    # warmup cache etc.


  def handle_exception(self, request, response, e, environ):
    """
    Will convert an exception into a rendered error message
    """
    logging.exception(e)

    if self.debug:
      tb = ''.join(traceback.format_exception(*sys.exc_info()))
    else:
      tb = ""

    try:
      content = self.render_exception({
          'status_code': e.code,
          'status_message': e.name,
          'message': e.get_description(environ),
          'traceback': tb,
      })
      response.set_status(e.code)
      response.out.write(content)
      return response
    except:
      return sketch.exception.InternalServerError(traceback = tb)

  # TODO implement url_for()
  def url_for(self):
    pass

  def dispatch(self, match, request, response, method = None):
    """
    docstring for dispatch
    """
    handler_class, args, kwargs = match
    method = method or request.method.lower().replace('-', '_')

    if isinstance(handler_class, basestring):
        if handler_class not in self._handlers:
            self._handlers[handler_class] = sketch.util.import_string(handler_class)
        handler_class = self._handlers[handler_class]

    # def handler class
    handler = handler_class(self, request, response)

    # def handler middleware
    handler.config = self.config

    session = sketch.Session(handler, 'sess')
    handler.attach_session(session)

    if 'key' in handler.session:
      logging.info(handler.session)
      try:
        handler.user = sketch.users.User.get_by_key(handler.session['key'])
      except Exception, e:
        logging.error('Error: could not get user. destroying session (%s)' % handler.session.key)
        handler.session.destroy()
        handler.user = False
    else:
      handler.user = False

    #  def handler plugins
    if self.plugins_registered:
      if hasattr(handler, 'plugin_register'):
        for pl in self._Plugins:
          handler.plugin_register(pl, self._Plugins[pl])
      else:
        logging.error("Handler %s does not support plugin resitration" % handler.__name__)

    # run prehook
    if hasattr(handler, 'pre_hook'):
      handler.pre_hook()

    try:
      logging.info("Calling: %s %s %s %s" % (handler, method, args, kwargs))
      view_func = getattr(handler, method, None)
      if view_func is None:
        valid = ', '.join(get_valid_methods(self))
        raise Exception('not implemented')
        # TODO implment 'not implented 405 error'
        # self.abort(405, headers=[('Allow', valid)])

      view_func(*args, **kwargs)

    except Exception, e:
      if method == 'handle_exception':
        raise

      handler.handle_exception(e, self.debug)

    if hasattr(handler, 'post_hook'):
      handler.post_hook()


  def wsgi_app(self, environ, start_response):
    """Called by WSGI when a request comes in."""
    Application.active_app = Application.app = self
    Application.request = request = self.request_class(environ)
    response = self.response_class()

    if 'enviroments' in self.config:
      self.set_environ(self.config.enviroments)
      
    try:
      if request.method not in self.ALLOWED_METHODS:
        raise sketch.exception.NotImplemented()

      match = self.router.match(request)

      if not match:
        raise sketch.exception.NotFound()

      self.dispatch(match, request, response)
    except sketch.exception.HTTPException, response:
      pass
    except Exception, e:
      try:
        response = self.handle_exception(request, response, e, environ)
      except sketch.exception.HTTPException, e:
        response = e
      except Exception, e:
        # Error wasn't handled so we have nothing else to do.
        logging.exception(e)
        if self.debug:
          raise
        response = sketch.exception.InternalServerError()
    finally:
      Application.active_app = Application.app = Application.request = None

    return response(environ, start_response)

  def run_appengine(self, bare=False):
    run_bare_wsgi_app(self)

  def __call__(self, environ, start_response):
    return self.wsgi_app(environ, start_response)
