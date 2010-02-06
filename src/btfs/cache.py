# -*- coding: iso-8859-1 -*-
import threading

# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#
# The original source for this module was written by Haoyu Bai (http://gaedav.google.com/).  

"""
Implement cache mechanism.
"""
import logging
from google.appengine.api import memcache

CACHED_NONE = "{cached-none}"

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

# TODO Maybe more faster if we apply sessioncache to memcache.

#===============================================================================
# ExtendedCache
#===============================================================================
#class ExtendedCache(object):
#    """
#    Wrapper for google.appengine.api.memcache that provides additional
#    features:
#    
#    - Applies a name space to all keys 
#    - Adds a per-request caching by using a WSGI `environ` dictionary
#    - Invokes callbacks on cache miss to access the datastore
#    - Also caches 'None' results
#    """
#    def __init__(self, namespace, get_func=None, set_func=None):
#        self.namespace = namespace
#        self.get_func = get_func
#        self.set_func = set_func
#        return
#
#
#    def _namespaced(self, s):
#        return "wsgidav.%s.%s" % (self.namespace, s)
#    
#    
#    def get(self, key, environ):
#        try:
#            # The environ dictionary can cache None values
#            nskey = self._namespaced(key)
#            result = environ[nskey] 
#            logging.debug("Request-Cache HIT: %s" % nskey)
#            return result 
#        except KeyError:
#            pass
#
#        result = memcache.get(key, namespace=self.namespace)
#        if result == CACHED_NONE:
#            environ[nskey] = None
#            logging.debug("Memcache HIT: %r.%r (cached-None)" % (self.namespace, key))
#            return None 
#        elif result is not None:
#            environ[nskey] = result
#            logging.debug("Memcache HIT: %r.%r" % (self.namespace, key))
#            return result
#        logging.debug("Memcache MISS: %r.%r" % (self.namespace, key))
#
#        if self.get_func:
#            result = self.get_func(key)
#            self.set(key, result, environ)
#
#        return result
#
#
#    def set(self, key, value, environ, time=0):
#        # The environ dictionary can cache None values
#        environ[self._namespaced(key)] = value
#        # memcache.get cannot return None, so we escape it
#        if value is None:
#            value = CACHED_NONE
#        return memcache.set(key, value, namespace=self.namespace, time=time)
#
#
#    def set_multi(self, mapping, environ, time=0, key_prefix=''):
#        m2 = mapping.copy()
#        for key, value in mapping.items():
#            # add to request-cache
#            environ[self._namespaced(key)] = value
#            # escape 'None' for memcache
#            if value is None:
#                m2[key] = CACHED_NONE
#            else:
#                m2[key] = value
#        
#        return memcache.set_multi(mapping, namespace=self.namespace, time=time, 
#                                  key_prefix=key_prefix)
#
#
#    def delete(self, key, environ):
#        try:
#            del environ[self._namespaced(key)] 
#        except KeyError:
#            pass
#        return memcache.delete(key, namespace=self.namespace)


#===============================================================================
# NamespacedCache
#===============================================================================
class NamespacedCache(object):
    def __init__(self, namespace):
        logging.debug("NamespacedCache.__init__, thread=%s", threading._get_ident())
        self.namespace = namespace
        return

    
    def __del__(self):
        logging.debug("NamespacedCache.__del__, thread=%s", threading._get_ident())

    
    def get(self, key):
        result = memcache.get(key, namespace=self.namespace)
        if result is not None:
            logging.debug("Cache HIT: %r.%r" % (self.namespace, key))
        else:
            logging.debug("Cache MISS: %r.%r" % (self.namespace, key))
        return result


    def set(self, key, value, time=0):
        logging.debug("Cache add: %r.%r = %r" % (self.namespace, key, value))
        return memcache.set(key, value, namespace=self.namespace, time=time)


    def set_multi(self, mapping, time=0, key_prefix=''):
        for key, value in mapping.items():
            logging.debug("Cache add multi: %r.%r = %r" % (self.namespace, key, value))
        return memcache.set_multi(mapping, namespace=self.namespace, time=time, 
                                  key_prefix=key_prefix)

    def delete(self, key):
        logging.debug("Cache delete: %r.%r" % (self.namespace, key))
        return memcache.delete(key, namespace=self.namespace)


#===============================================================================
# 
#===============================================================================
logging.debug("import cache.py")
#cached_dir = NamespacedCache('dir')
#cached_file = NamespacedCache('file')
#cached_content = NamespacedCache('content')
cached_resource = NamespacedCache('resource')
cached_lock = NamespacedCache('lock')
#cached_lockpath = NamespacedCache('lockpath')
