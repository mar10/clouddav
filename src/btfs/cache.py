# -*- coding: iso-8859-1 -*-

# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#
# The original source for this module was written by Haoyu Bai (http://gaedav.google.com/).  

"""
Implement cache mechanism.
"""
import logging
from google.appengine.api import memcache

class UnmappedPath(object):
    """Dummy object to cache lookups for non-existent URLs."""
    pass

#def sessioncached(f):
#    """
#    The cache only live in one session.
#    """
#    cache_dict = dict()  # used by the inner function
#    def cached_func(*args, **kwargs):
#        t = (args, kwargs.items())
#        try:
#            hash(t)
#            key = t
#        except TypeError:
#            try:
#                import pickle
#                key = pickle.dumps(t)
#            except pickle.PicklingError:
#                logging.warn("Cache FAIL: can't hash %s(args=%s, kwargs=%s)", repr(f), repr(args), repr(kwargs))
#                return f(*args, **kwargs)
#        if cache_dict.get(key) is not None:
#            logging.info("Cache HIT: %s(args=%s, kwargs=%s)", repr(f), repr(args), repr(kwargs))
#            return cache_dict[key]
#        logging.info("Cache MISS: %s(args=%s, kwargs=%s)", repr(f), repr(args), repr(kwargs))
#        value = f(*args, **kwargs)
#        cache_dict[key]=value
#        return value
#    try:
#        cached_func.func_name = f.func_name
#    except AttributeError:
#        # for class method which has no func_name
#        pass
#    return cached_func
#
## TODO Maybe more faster if we apply sessioncache to memcache.

class NamespacedCache(object):
    def __init__(self, namespace):
        self.namespace = namespace
        return

    def namespaced(self, key):
        return self.namespace + ':' + key
    
    def get(self, key):
        nk = self.namespaced(key)
        result = memcache.get(nk)
        if result is not None:
            logging.info("Cache HIT: %s", repr(nk))
        else:
            logging.info("Cache MISS: %s", repr(nk))
        return result

    def set(self, key, value):
        return memcache.set(self.namespaced(key), value)

    def delete(self, key):
        return memcache.delete(self.namespaced(key))

cached_dir = NamespacedCache('dir')
cached_file = NamespacedCache('file')
#cached_content = NamespacedCache('content')
cached_resource = NamespacedCache('resource')
