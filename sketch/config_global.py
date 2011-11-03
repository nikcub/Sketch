# default sketch config

debug = False
default_charset = 'utf-8'
default_language = 'en-us'
append_slash = False
prepend_www = False
user_agent = "Mozilla/5.0 (compatible; SketchBot/0.1; +http://nikcub.appspot.com/projects/sketch)"
session_name = 'sess'
server_email = {
  'address': 'root@localhost',
  'host': 'localhost',
  'port': 25,
  'secure': False,
  'username': None,
  'password': None
}
templates = {
  'test': '$site_dir/test',
  'app': '$app_dir/templates',
  'sketch': '$sketch_dir/templates',
}
enviroments = {
  'live': {
    'debug': False,
    'hosts': ['*.appspot.com']
  },
  'staging': {
    'debug': True,
    'hosts': ['*.*.appspot.com']
  },
  'dev': {
    'debug': True,
    'hosts': ['localhost', '*.dyndns.org']
  }
}
auth_providers = {}