import sys
import os
import logging
import sketch

from google.appengine.ext import db

class RestController(sketch.BaseController):
  """A generic REST controller to expose a model as a web service
  
  """
  def get(self, key=None):
    logging.info('Called GET')
    logging.info(self.model)
    try:
      if key:
        posts = self.model.get_by_key(key)
      else:
        posts = self.model.get_all()
        logging.info(posts)
    except db.BadKeyError, e:
      return self.render('json', e, 404)
    except Exception, e:
      logging.exception(e)
      return self.render('json', e, 500)
    
    return self.render('json', posts, 200)
  
  def post(self, key=None):
    pass
  
  def put(self, key=None):
    if not key:
      raise sketch.exception.NotFound()
    
    entry = db.get(db.key(key))
    if not entry:
      raise sketch.exception.NotFound()
    
    for field, value in self.request.get_all():
      logging.info("%s => %s" % (field, value))
    
  
  def delete(self, key=None):
    pass