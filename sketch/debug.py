
import sketch

class CookieTest(sketch.AdminController):
  def get(self, arg):
    if arg == "/set":
      self.redirect('/cookie?set')
    if arg == "/clear":
      session.invalidate()
      self.redirect('/cookie')
    else:
      if self.session.is_new():
        self.session["test"] = 1
      else:
        self.session["test"] += 1
      self.render('cookie', {
        'cookie': self.request.str_cookies,
        'session': self.session,
        'test': self.session["test"],
        'sid': self.session.get_sid(),
        })

class SketchSession(sketch.AdminController):
  def get(self, action):
    if action == "template":
      return self.render('template', {})
    if action == "sessionDestroy":
      self.session.invalidate()
      return self.redirect('/_session')
    if action == "sessionCreate":
      self.session['test'] = "test"
      self.session.save()
      return self.redirect('/_session')
    if action == "sessionAddTest":
      self.session['var1'] = "this is var one"
      self.session['var2'] = {"this": "var two"}
      self.session['var3'] = ['this', 'is', 'var3']
      self.session['auth'] = True
      self.session.save()
      return self.redirect('/_session')
    if action == "session":
      pass

class Handler(sketch.AdminController):
  template_folder = 'sketch.admin'

  def get(self, action):
    if action == "stash":
      # from vendor import stash
      pass
    if action == "session":
      action = self.request.get('action')
      if action == "create":
        self.session['init'] = "initialized"
        return self.redirect_back()
      if action == "destroy":
        self.session.destroy()
        return self.redirect_back()
      if action == "del":
        del self.session['test']
        del self.session['beta']
        return self.redirect_back()
      if action == "add":
        self.session['test'] = "test string"
        self.session['beta'] = "beta string"
        return self.redirect_back()
      if action == "regen":
        self.session.regen()
        return self.redirect_back()
      sts = stash.increment()
      content = self.render_admin('session', {
          'stash': sts,
          'session': self.session,
          'cookie': os.environ.get('HTTP_COOKIE', ''),
        })
      return content
    if action == "modified":
      self.response.headers['Last-Modified'] = "zAmsdwsdsd"
      return self.render_admin('modified', {
        'req': self.request.headers,
        'res': self.response.headers,
      })
    if action == "etag":
      etag_set = self.request.get('etag', False)
      if etag_set:
        self.response.headers['ETag'] = etag_set
        # return self.redirect('/_etag')
      return self.render_admin('etag', {
        'req': self.request.headers,
        'res': self.response.headers,
      })
    if action == "globals":
      glob = sketch._sketch_globals
      return self.render_admin('globals', {
        'globals': glob,
      })
    if action == "env":
      return self.render_sketch('env', {
        'debug': self.debug,
        'is_dev': self.is_dev,
        'env': self.env,
        'enviro': self.enviro,
      })