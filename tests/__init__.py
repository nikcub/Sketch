
import os
import sys
import logging
import unittest

from sketch.util import add_to_path, setup_gae_paths

class BaseTest(unittest.TestCase):
  pass

class TestLoader(unittest.TestLoader):
  def __init__(self):
    pass

def main():
  print 'running tests'
  try:
    unittest.main(testLoader=TestLoader(), defaultTest='suite')
  except Exception, e:
    print 'Error: %s' % e