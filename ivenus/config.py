#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for configurations. Copied from yxqd/nimg.
"""

from __future__ import absolute_import, division, print_function

import logging
logger = logging.getLogger(__name__)


__author__ = "Doga Gursoy"
__copyright__ = "Copyright (c) 2015, ORNL."
__docformat__ = 'restructuredtext en'
__all__ = ['load_yaml_config',
           'Struct']


def load_yaml_config(path):
    """
    Load yaml config file from the given path and
    return a python object.
    """
    import yaml
    f = open(path)
    d = yaml.safe_load(f)
    f.close()
    return Struct(d)


class Struct:

    """
    The recursive class for building and representing objects with.
    """

    def __init__(self, obj):
        for k, v in obj.items():
            if isinstance(v, dict):
                setattr(self, k, Struct(v))
            else:
                setattr(self, k, v)

    def __getitem__(self, val):
        return self.__dict__[val]

    def __repr__(self):
        return '{%s}' % str(', '.join('%s : %s' % (k, repr(v)) for
                                      (k, v) in self.__dict__.items()))
