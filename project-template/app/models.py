import uuid
import sketch

from google.appengine.ext import db
from sketch.users import User

"""
* updated
* created

get_all
get_last
get_by_key
update
"""
class Todos(sketch.Model):
  user = db.ReferenceProperty(User)
  done = bool
  desc = db.TextProperty()
  
  @property
  def id(self):
    return self.key().id_or_name()

  @classmethod
  def get_by_user(self, userkey):
    q = db.GqlQuery("SELECT * FROM Posts WHERE user = :1", userkey)
    r = q.fetch(20)
    return r


class Assets(sketch.Model):
  url = db.StringProperty()
  user = db.ReferenceProperty(User)
  img_dat = db.BlobProperty(default = None)
  img_type = db.StringProperty()
  img_size = db.IntegerProperty()

  @property
  def id(self):
    return self.key().id_or_name()

  @property
  def k(self):
    return self.key()

  @property
  def url(self):
    return "/p/%s.jpg" % (self.id)


class Posts(sketch.Model):
  msg = db.StringProperty()
  user = db.ReferenceProperty(User, required=True)
  # image = blobstore.BlobReferenceProperty()
  img = db.ReferenceProperty(Assets)

  def create():
    pass

  @property
  def id(self):
    return self.key().id_or_name()

  @property
  def k(self):
    return self.key()

  @property
  def url(self):
    return "/p/%s" % (self.id)

  @classmethod
  def get_by_user(self, userkey):
    q = db.GqlQuery("SELECT * FROM Posts WHERE user = :1", userkey)
    r = q.fetch(20)
    return r
