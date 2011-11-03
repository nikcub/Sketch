from distutils.core import setup
import sys

setup(name='sketch',
      version='0.2-alpha',
      author='Nik Cubrilovic',
      author_email='nikcub@gmail.com',
      url='http://nikcub.appspot.com/projects/sketch',
      download_url='http://github.com/nikcub/sketch',
      description='Python web application framework for Google App Engine',
      long_description=sketch.__doc__
      package_dir={'': 'sketch'},
      py_modules=['sketch'],
      provides=['sketch'],
      keywords='web application framework google appengine gae',
      license='2-clause BSD',
      py_modules=['urllib'],
)