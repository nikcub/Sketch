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
          response_type=False, prettyPrint=False, template_set='app', template_theme=None):
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
      sketch.jinja.setup(self.config.paths.templates)
      passed_vars = self.get_template_vars(passed_vars)
      passed_vars = self.get_plugin_vars(passed_vars)
      # fixing..
      
      if hasattr(self, 'template_folder'):
        template_theme = getmethattr(self, 'template_folder')
      
      content = sketch.jinja.render(template_name, passed_vars, template_theme=template_theme, template_set=template_set)
    
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
    }, code, template_folder='sketch')


  def render_admin(self, template_name, vars):
    return self.render(template_name, vars, template_folder='admin')


  def render_sketch(self, template_name, vars):
    vars['admin'] = True
    return self.render(template_name, vars, template_folder='sketch')


  def get_javascripts(self, template_vars):
    """Will read the javascripts to be included, create the tags and include
    them as part of the template variables
    
    :param template_vars: Template variable dict
    """
    if not hasattr(self, 'javascripts'):
      return template_vars
    
    scripts_dict = getmethattr(self, 'javascripts')
    js_tmp = ""

    for script_d in scripts_dict:
      for script_src in scripts_dict[script_d]['src']:
        js_tmp = js_tmp + "<script type=\"text/javascript\" src=\"%s\"></script>\n" % script_src

    template_vars['javascripts'] = js_tmp
    return template_vars


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

    additional = self.get_javascripts(additional)

    return dict(vars, **additional)


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


  #---------------------------------------------------------------------------
  #   helpers
  #---------------------------------------------------------------------------


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


  #---------------------------------------------------------------------------
  #   Rendering Engines
  #---------------------------------------------------------------------------


  def render_django(self, template_name, vars, response_type = False):
    """Given a template name and variables will render the template using
    the default Django template rendering engine 
    
    :param template_name: Name of template
    :param vars: Template variables
    
    @TODO clean out the 'get_template_path' stuff and put that in render
    @TODO this should only be rendering, none of the fancy content stuff
    """
    pass
    # from google.appengine.dist import use_library
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
    return self.config.enviro or None

  @property
  def enviro(self):
    return self.config.enviro


class AdminController(BaseController):
  """A custom controller that restricts permissions to only those users who are
  an administrator
  
  """

  template_path = os.path.join('')

  def __call__(self, _method, *args, **kwargs):
    if not self.user:
      abort(403)

    if not self.user.admin:
      abort(405)

    super(AdminController, self).__call__(_method, *args, **kwargs)

