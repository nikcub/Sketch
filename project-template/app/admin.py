
import sketch
import app.models

#---------------------------------------------------------------------------
#   admin controllers
#---------------------------------------------------------------------------


class UsersIndex(sketch.AdminController):
  def get(self):
    return self.render('admin.users', {
      "users": sketch.users.User.get_all()
    })

  def post(self):
    username = self.request.get("username")
    email = self.request.get("email")
    password = self.request.get("password")
    msg = User.create(
      username = username,
      email = email,
      password = password
    );
    self.redirect('/admin/users?created')

class Users(sketch.AdminController):
  def get(self, key):
    usr = sketch.users.User.get_by_key(key)
    usrlog = usr.activity.order('-created').fetch(20)
    return self.render('admin.users.edit', {
      "user": usr,
      "userlog": usrlog,
    })

  def post(self, key):
    user = sketch.users.User.get_by_key(key)
    action = self.request.get('action', False)

    if not user or not action:
      self.set_message('User Error')
      return self.redirect_back()

    if action == "_update":
      username = self.request.get('username', "")
      name = self.request.get('name', "")
      email = self.request.get('username', "")
      picture = self.request.get('picture', "")
      password = self.request.get('password', "")
      disabled = self.request.get_checkbox('disabled')
      admin = self.request.get_checkbox('admin')

      r = user.update({
        "username": username,
        "name": name,
        "email": email,
        "picture": picture,
        "password": password,
        "disabled": disabled,
        "admin": admin,
      })

      if r:
        self.set_message('saved')
      else:
        self.set_message('save error')
      return self.redirect_back()


    self.set_message('other error')
    return self.redirect_back()
