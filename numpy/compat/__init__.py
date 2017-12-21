"""
Compatibility module.

This module contains duplicated code from Python itself or 3rd party
extensions, which may be included for the following reasons:

  * compatibility
  * we may only need a small subset of the copied library/module

"""
from __future__ import division, absolute_import, print_function

from . import _inspect
from . import py3k
from ._inspect import getargspec, formatargspec
from .py3k import (Path, absolute_import, asbytes, asbytes_nested, asstr,
                   asunicode, asunicode_nested, basestring, bytes, division,
                   getexception, integer_types, is_pathlib_path, isfileobj,
                   long, npy_load_module, open_latin1, print_function, sixu,
                   strchar, sys, unicode)

__all__ = []
__all__.extend(_inspect.__all__)
__all__.extend(py3k.__all__)
