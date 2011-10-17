#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sketch

# TODO support environments eg. testing, dev, staging, live and change config loading based on
# TODO load different config sections based on environment specified
def run():
    config_file = os.path.join(os.path.dirname(__file__), "sketch.yaml")
    app = sketch.Application(config_file, 'app')
    app.run_appengine()