from __future__ import absolute_import, unicode_literals

import sys
import types

try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

try:
    from django.utils.module_loading import import_string
except ImportError:
    def import_string(dotted_path):
        try:
            module_path, obj_name = dotted_path.rsplit('.', 1)
        except ValueError:
            msg = '%s does not look like a module path' % dotted_path
            raise ImportError(msg)

        module = import_module(module_path)

        try:
            return getattr(module, obj_name)
        except AttributeError:
            msg = 'Module %s does not define name %s' % (module_path, obj_name)
            raise ImportError(msg)


PY3 = sys.version_info[0] == 3

if PY3:
    binary_type = bytes
    class_types = (type,)
    string_types = (str,)
    text_type = str
else:
    binary_type = str
    class_types = (type, types.ClassType)
    string_types = (basestring,)  # noqa
    text_type = unicode  # noqa
