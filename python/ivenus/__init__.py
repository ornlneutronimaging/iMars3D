# iVenus python package

from __future__ import absolute_import, division, print_function

import yaml, os
conf_path = "ivenus.conf"
config = dict()
if os.path.exists(conf_path):
    config = yaml.load(open(conf_path))

import logging.config
logging_conf = config.get("logging")
if logging_conf:
    logging.config.dictConfig(logging_conf)


from . import io, components
