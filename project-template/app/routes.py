import sketch
import app.controllers as controllers
import app.admin as admin

routes = [
    # sketch.Route(r'/<username>', controllers.UserPage),
    sketch.Route(r'/', controllers.Index),
]

