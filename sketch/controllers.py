import sys
import os
import cgi
import datetime
import urllib
import logging
from os.path import isdir
from os.path import join as dj

import sketch
from sketch.util import hasmethod, hasvar, getmethattr
from google.appengine.ext import webapp
from django.utils.timesince import timesince
from django.utils.dateformat import format as django_format


class BaseController(sketch.RequestHandler):
  """BaseController default application controller that is inherited for other
  controllers. Implements requests, response, rendering, plugins etc.
  
  """
  
  _Plugins = {}
  message = False
  message_type = None

  def pre_hook(self):
    self.reg_messages()

  def post_hook(self):
    self.session.save()

  # Plugin reg
  def plugin_register(self, plugin_name, plugin_inst):
    self._Plugins[plugin_name] = plugin_inst

  def attach_session(self, session):
    self.session = session

  def reg_messages(self):
    self.messages = sketch.Messages()

    # logging.info("Plugin Reg: Registering messages plugin")
    # logging.info(self.messages)
    # logging.info(self.messages.info)
    if 'message' in self.session:
      self.message = self.session['message']
      self.message_type = self.session['message_type']
      self.message_class = self.session['message_class']
      del self.session['message']
      del self.session['message_type']
      del self.session['message_class']
      self.session.save()



  #---------------------------------------------------------------------------
  #   messages
  #---------------------------------------------------------------------------


  def set_msg(self, message, message_type = None):
    return self.set_message(message, message_type)

  def set_message(self, message, message_type = None, fade = 'fade'):
    if not message_type:
        message_type = self.messages.info
    # use a custom session component to set the message
    self.session['message'] = message
    self.session['message_type'] = message_type
    self.session['message_class'] = fade
    self.session.save()
    # self.message_type = message_type


  #---------------------------------------------------------------------------
  #   Rendering
  #---------------------------------------------------------------------------


  def render(self, template_name, passed_vars, response_code = 200, 
          response_type = False, prettyPrint = False, template_folder=None):
    """Main render helper function. Wraps other rendering functions
    
    """
    if not response_type:
      response_type = self.request.response_type()

    prettyPrint = bool(self.request.get('prettyPrint', False))
    
    if hasmethod(self, 'template_wrapper'):
      passed_vars = self.template_wrapper(variables = passed_vars)
          
    if response_type in ['xml', 'json']:
      serial_f = getattr(sketch.serialize, response_type)
      content = serial_f(passed_vars, pretty = prettyPrint)
      self.response.headers['Content-Type'] = "application/%s; charset=utf-8" % (response_type)
    else:
      passed_vars = self.get_template_vars(passed_vars)
      passed_vars = self.get_plugin_vars(passed_vars)
      # fixing..
      template_path = self.get_template_dir(template_folder)
      content = self.render_jinja(template_path, template_name, passed_vars)
    
    logging.info("%s - %s" % (template_path, template_name))
    logging.info(content)
    
    self.render_content(content, response_code)


  def render_content(self, content, response_code = 200, headers = []):
    """The actual function that will render content back into the response
    
    :param content: Content to be rendered
    :param response_code: HTTP response code
    :param headers: Response headers
    """
    self.response.clear()
    if len(headers) > 0:
      for hn, hv in headers:
        self.response.headers[hn] = hv
    self.response.set_status(response_code)
    self.response.write(content)


  def render_error(self, message = False, code = 404):
    self.render('error', {
        'code': '%d - %s' % (code, self.response.http_status_message(code)),
        'message': message
    }, code)


  def render_admin(self, template_name, vars):
    return self.render(template_name, vars, template_folder='admin')


  def render_sketch(self, template_name, vars):
    vars['admin'] = True
    return self.render(template_name, vars, template_folder='sketch')


  def render_blob(self, blob_key_or_info, filename=None):
    """Render a file from the GAE blobstore
    
    :param blog_key_or_info: A key for the blog
    :param filename: (optional) Name of file in user download
    """
    if isinstance(blob_key_or_info, blobstore.BlobInfo):
      blob_key = blob_key_or_info.key()
      blob_info = blob_key_or_info
    else:
      blob_key = blob_key_or_info
      blob_info = None

    self.response.headers[blobstore.BLOB_KEY_HEADER] = str(blob_key)
    del self.response.headers['Content-Type']

    def saveas(filename):
      if isinstance(filename, unicode):
        filename = filename.encode('utf-8')
      self.response.headers['Content-Disposition'] = 'attachment; filename="%s"' % filename

    if filename:
      if isinstance(filename, basestring):
        saveas(filename)
      elif blob_info and filename:
        saveas(blob_info.filename)
      else:
        raise ValueError("problem with filename to save as")

    self.response.clear()


  def render_jinja(self, template_path, template_name, vars):
    from sketch.vendor import jinja2
    
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    env.filters['timesince'] = timesince
    env.filters['tformat'] = django_format
    template = env.get_template(template_name + '.html')
    return template.render(vars)


  def render_django(self, template_name, vars, response_type = False):
    from google.appengine.ext.webapp import template
    
    if not response_type:
        response_type = self.request.response_type()
    vars = self.get_template_vars(vars)
    vars = self.get_plugin_vars(vars)
    if response_type in ['xml', 'json']:
        serial_f = getattr(sketch.serialize, response_type)
        content = serial_f(vars)
        self.response.headers['Content-Type'] = "application/%s; charset=utf-8" % (response_type)
    else:
        content = template.render(self.get_template_path(template_name, response_type), vars)
    return content


  #---------------------------------------------------------------------------
  #   helpers
  #---------------------------------------------------------------------------


  def get_template_dir(self, template_folder=None):
    """Given a template name return a full path to the template directory.
    Template folders are alises defined in config or within the applications.
    
    :param template_name: name of template
    :param template_folder: template folder
    """
    if not template_folder and hasattr(self, 'template_folder'):
      template_folder = getmethattr(self, 'template_folder')
      
    if template_folder in self.app.config.paths.templates:
      template_dir = self.app.config.paths.templates[template_folder]
    elif 'app_template_basedir' in self.app.config.paths:
      if isdir(dj(self.app.config.paths['app_template_basedir'], template_folder)):
        template_dir = dj(self.app.config.paths['app_template_basedir'], template_folder)
    elif 'app_template_default' in self.app.config['paths']:
      template_dir = self.app.config['paths']['app_template_default']
    else:
      raise Exception("Could not find template to use: given %s" % template_folder)

    if not os.path.isdir(template_dir):
      raise Exception("Not a template path: %s. Please specify the template path in config", templates_path)

    return template_dir


  def get_template_vars(self, vars):
    if type(vars) != dict:
      vars = {'_vars': vars}
      
    additional = {
      'session': self.session,
      'user': False,
        # 'admin': users.is_current_user_admin(),
        # 'user': users.get_current_user(),
        # 'logout': users.create_logout_url('/'),
        # 'login': users.create_login_url('/'),
        # 'title': 'test'
        # 'title': self.conf_get('title')
    }

    if 'auth' in self.session:
      additional['loggedin'] = True
      additional['username'] = self.session.get('username', '')
      additional['user'] = self.user

    if self.message:
      additional['message'] = self.message
      additional['message_type'] = self.message_type
      additional['message_class'] = self.message_class

    return dict(vars, **additional)


  def get_plugin_vars(self, vars):
    for plugin in self._Plugins:
      if hasattr(self._Plugins[plugin], "render"):
        val_dict = self._Plugins[plugin].render()
        if type(val_dict) == type({}):
          for temp_var in val_dict:
            if not vars.has_key(temp_var):
              vars[temp_var] = val_dict[temp_var]
            else:
              logging.error("Did not get a valid dict type from plugin %s" % plugin)
    return vars


  def get_param_dict(self):
    params = {}
    for argument in self.request.arguments():
      params[argument] = self.request.get(argument)
    return params


  def handle_exception(self, exception = None, errno = None, strerror = None):
    """Called if this handler throws an exception during execution.

    The default behavior is to call self.error(500) and print a stack trace
    if debug_mode is True.

    Args:
    exception: the exception that was thrown
    debug_mode: True if the web application is running in debug mode
    """
    logging.info("*********** HANDLER EXCEPTION ******************")
    raise
    return False
    self.error(500)
    logging.exception(exception)
    lines = ""
    if self.config['debug']:
      import traceback
      lines = ''.join(traceback.format_exception(*sys.exc_info()))
    self.render_error(message = lines, code = 500)


  
  #---------------------------------------------------------------------------
  #   Conveniance Methods
  #---------------------------------------------------------------------------

  @property
  def debug(self):
    return self.config.is_debug

  @property
  def is_dev(self):
    return self.config.is_dev
    
  @property
  def is_staging(self):
    return self.config.is_staging
    
  @property
  def is_live(self):
    return self.config.is_live
    
  @property
  def env(self):
    return self.config.enviro['name'] or None

  @property
  def enviro(self):
    return self.config.enviro


class AdminController(BaseController):

  template_path = os.path.join('')

  def __call__(self, _method, *args, **kwargs):
    if not self.user:
      abort(403)

    if not self.user.admin:
      abort(405)

    super(AdminController, self).__call__(_method, *args, **kwargs)

