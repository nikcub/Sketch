#!/usr/bin/env python
import os
import sys
import logging

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

def main():
  setup_gae_paths()
  sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
  from sketch.testsuite import main as run_tests
  run_tests()

if __name__ == '__main__':
  main()