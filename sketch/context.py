"""
lots to do here. point is to write a simple DSL in Python that will allow us to
define apps like so:

with get('/') as r:
  r.render('index')
  
with post('/') as r:
  post = Posts.get(r.param['key'])
  post.update(r.params())
  r.render(post)

"""
import sketch

APP = None

from __future__ import with_statement
from contextlib import contextmanager

class App(object):
  def __init__(self, route):
    self.table_name = table_name
    self.fields = {}

  def __setattr__(self, attr, value):
    if attr in ("fields", "table_name"):
      object.__setattr__(self, attr, value)
    else:
      self.fields[attr] = value

  def execute(self):
    print "Creating table %s with fields: %s" % (self.table_name, self.fields)


@contextmanager
def create_table(table_name):
  table=Table(table_name)
  yield table
  table.execute()

@contextmanager
def get(route):
  setup_app()
  pass
  
def post(route):
  pass

def setup_app():
  if not APP:
    app = sketch.Application()


with get('/') as r:
  t.render('index')

#try it!
with create_table("Employee") as t:
    t.first_name = {"type" : "char", "length" : 30 }
    t.last_name = {"type" : "char", "length" : 30 }
    t.age = {"type" : "int"}
