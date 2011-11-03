
import os
import sys
import unittest

class ConfigTest(unittest.TestCase):
  
  config_dir = 'configs'
  
  config_files = {
    "yaml": "config.yaml",
    "ini": "config.ini",
    "py": "config.py",
    "json": "config.json",
  }
  
  conf_output = {
    "Diffbot": {
      "debug": True,
      "apikey": "0000010000111",
    },
    "debug": False,
    "apikey": "apikey"
  }
  
  def setup_conf(self, filename):
    conf_file_path = os.path.join(self.config_dir, filename)
    if not os.path.isfile(conf_file_path):
      raise Exception, "Could not load config file: %s" % conf_file_path
    return sketch.Config(conf_file_path)
    
  def test_non_existant_config_file(self):
    """Passing a non-existant file should raise an error"""
    non_existant_file = "zzzzzz"
    self.assertRaises(config.ConfigFileError, config.Config, non_existant_file)
  
  def test_detect_file_type_yaml(self):
    conf = self.setup_conf('config.yaml')
    self.assertEqual(conf.file_type, 'yaml')

  def test_load_yaml_config(self):
    conf = self.setup_conf('config.yaml')
    self.assertEqual(conf, self.conf_output)


#---------------------------------------------------------------------------
#   Setup Helpers
#---------------------------------------------------------------------------


def setup_paths():
  sketch_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
  if os.path.isdir(sketch_path):
    sys.path.insert(0, sketch_path)
    return True
  raise Exception('could not load sketch')


def setup_gae_paths(gae_base_dir=None):
  if not gae_base_dir:
    gae_base_dir = '/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine'

  if not os.path.isdir(gae_base_dir):
    return False

  ae_path = os.path.abspath(os.path.realpath(gae_base_dir))

  AE_PATHS = [
    ae_path,
    os.path.join(ae_path, 'lib', 'antlr3'),
    os.path.join(ae_path, 'lib', 'django'),
    os.path.join(ae_path, 'lib', 'fancy_urllib'),
    os.path.join(ae_path, 'lib', 'ipaddr'),
    os.path.join(ae_path, 'lib', 'webob'),
    os.path.join(ae_path, 'lib', 'yaml', 'lib'),
  ]
  
  sys.path = sys.path + AE_PATHS

  return True


#---------------------------------------------------------------------------
#   Main
#---------------------------------------------------------------------------


if __name__ == '__main__':
  setup_gae_paths()
  setup_paths()
  
  try:
    import sketch
    unittest.main()
  except ImportError, e:
    print "Could not find module sketch. Please check import paths etc."
  except Exception, e:
    print "Error: %s" % e
  