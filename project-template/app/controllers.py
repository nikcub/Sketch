import logging
import time

import sketch
import app.models as models

from google.appengine.ext import db
from google.appengine.api import urlfetch
from sketch.vendor import stash

class Backbone(sketch.BaseController):
  def get(self):
    return self.render('backbone', {})

class Todo(sketch.BaseController):
  def post(self, key = None):
    if key:
      return self.render('json', {'error': 'not implemented'})
    donev = self.request.get('done', False)
    descv = self.request.get('desc', "")
    todo = imgahz.models.Todos(
      done = donev,
      desc = descv,
    )
    r = todo.put()
    
    if not r:
      return self.render('json', {'error': 'could not save'})
    return self.render('json', {'stored': True, 'todo': todo})
    
  def get(self, key = None):
    if not key:
      todos = imgahz.models.Todos.get_last(20)
    else:
      todos = imgahz.models.Todos.get_by_key(key)
    todo_ret = []
    for todo in todos:
      todo_ret.append({
        'when': time.mktime(todo.created.timetuple()),
        'desc': todo.desc,
        'done': todo.done
      })
    return self.render('json', todo_ret)


class Index(sketch.BaseController):
  def get(self):
    posts = models.Posts.get_last(20)
    return self.render('index', {
      'posts': posts,
    })

