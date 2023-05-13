from hashlib import md5 as _md5
from hashlib import sha1 as _sha1

try:
    from django.utils.encoding import force_bytes
except ImportError:
    raise ImportError("This module depends on django.")


def md5_text(*args):
    m = _md5()
    for x in args:
        m.update(force_bytes(x, errors="replace"))
    return m


def sha1_text(*args):
    m = _sha1()
    for x in args:
        m.update(force_bytes(x, errors="replace"))
    return m
