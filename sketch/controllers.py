import os, logging, traceback, sys, cgi, datetime, urllib

import sketch

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class BaseController(sketch.RequestHandler):

  _Plugins = {}
  message = False
  message_type = None

  # Hooks
  def pre_hook(self):
    self.reg_messages()
    # self.session = sketch.Session()

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

  # TODO use 307 on redirect?
  # TODO use session info here and do not trust referrer
  def redirect_back(self):
    re = self.request.environ.get('HTTP_REFERER', '/')
    self.redirect(re, code = 303)


  @property
  def is_ajax(self):
    return self.request.is_ajax()

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
  #   rendering
  #---------------------------------------------------------------------------

  # TODO - build template path, then render

  # TODO - fuck all this up and throw it away

  def render(self, template_name, passed_vars, response_code = 200, response_type = False, prettyPrint = False):

    if not response_type:
      response_type = self.request.response_type()

    prettyPrint = bool(self.request.get('prettyPrint', False))
    
    if response_type in ['xml', 'json']:
      serial_f = getattr(serialize, response_type)
      content = serial_f(passed_vars, pretty = prettyPrint)
      self.response.headers['Content-Type'] = "application/%s; charset=utf-8" % (response_type)
    else:
      passed_vars = self.get_template_vars(passed_vars)
      passed_vars = self.get_plugin_vars(passed_vars)
      template_path = self.get_template_path(template_name)
      content = self.render_jinja(template_path, template_name, passed_vars)

    self.response.clear()
    self.response.set_status(response_code)
    self.response.write(content)

  def render_error(self, message = False, code = 404):
    self.render('error', {
        'code': '%d - %s' % (code, self.response.http_status_message(code)),
        'message': message
    }, code)


  def render_blob(self, blob_key_or_info, filename=None):
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

  def render_admin(self, template_name, vars):
    # TODO change this and make it *better*
    vars['admin'] = True
    template_path = self.get_template_path(template_name, 'admin')
    content = self.render_jinja(template_path, template_name, vars)
    self.response.clear()
    self.response.set_status(200)
    self.response.write(content)


  def get_template_path(self, template_name, template_type = 'app'):
    base = os.path.dirname(__file__)
    if template_type in self.app.config['templates']:
      template_dir = self.app.config['templates'][template_type]
    else:
      template_dir = os.path.join('app', 'templates')
    templates_path = os.path.join(base, '..', template_dir)
    templates_path = os.path.realpath(templates_path)
    templates_path = os.path.normpath(templates_path)
    if not os.path.isdir(templates_path):
      raise Exception("Not a template path: %s. Please specify the template path in config", templates_path)
    template_path = os.path.join(templates_path, "%s.html" % template_name)
    if not os.path.isfile(template_path):
      raise Exception("Not a template: %s", template_path)
    return templates_path


  def render_jinja(self, template_path, template_name, vars):
    # env = jinja2.Environment(loader=jinja2.PackageLoader('evergreen', 'templates'))

    # logging.info("Jinja: template path is %s" % template_path)
    
    # TODO better support of vendor things..
    
    from sketch.vendor import jinja2
    
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    # from sketch.utils import timesince
    # env.filters['timesince'] = timesince
    template = env.get_template(template_name + '.html')
    return template.render(vars)


  def render_django(self, template_name, vars, response_type = False):
    if not response_type:
        response_type = self.request.response_type()
    vars = self.get_template_vars(vars)
    vars = self.get_plugin_vars(vars)
    if response_type in ['xml', 'json']:
        serial_f = getattr(serialize, response_type)
        content = serial_f(vars)
        self.response.headers['Content-Type'] = "application/%s; charset=utf-8" % (response_type)
    else:
        content = template.render(self.get_template_path(template_name, response_type), vars)
    return content


  #---------------------------------------------------------------------------
  #   helpers
  #---------------------------------------------------------------------------




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




class AdminController(BaseController):

  template_path = os.path.join('')

  def __call__(self, _method, *args, **kwargs):
    if not self.user:
      abort(403)

    if not self.user.admin:
      abort(405)

    super(AdminController, self).__call__(_method, *args, **kwargs)

