# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
Implementation of a lock manager using Memcache.

Note (http://code.google.com/appengine/docs/python/memcache/overview.html):
    "Values can expire from the memcache at any time, and may be expired prior 
    to the expiration deadline set for the value." 

We still use it here for locking, since it's much faster than datastore 
persistence. And also (http://www.webdav.org/specs/rfc4918.html#lock-timeout):
    "a client MUST NOT assume that just because the timeout has not expired, 
    the lock still exists."

Memcache does not allow enumeration of stored values, so we have to keep a 
list of all locked paths in order to find locked children for a given path. 

See http://code.google.com/appengine/docs/python/memcache/
See `Developers info`_ for more information about the WsgiDAV architecture.

.. _`Developers info`: http://docs.wsgidav.googlecode.com/hg/html/develop.html  
"""
from __future__ import absolute_import
from builtins import object
import logging
from wsgidav import util
from wsgidav.lock_manager import normalizeLockRoot, lockString,\
    validateLock, generateLockToken
import time
from .cache import cached_lock
_logger = util.getModuleLogger(__name__)

__docformat__ = "reStructuredText"


#===============================================================================
# LockStorageMemcache
#===============================================================================

class LockStorageMemcache(object):
    """
    An in-memory lock manager implementation using a Google's Memcache.
    
    The data is stored in the Memcache namespace 'lock' like this::
    
    memcache[{lock:}<token>] : <lock dictionary>
    memcache[{lock:}<token2>] : <lock dictionary 2>
    ...
    memcache[{lock:}'*'] : {path1: [<token-list>],
                            path2: [<token-list>]),
                            } 
    """
    LOCK_TIME_OUT_DEFAULT = 604800 # 1 week, in seconds
    LOCK_TIME_OUT_MAX = 4 * 604800 # 1 month, in seconds

    def __init__(self):
        pass


    def __repr__(self):
        return self.__class__.__name__


    def __del__(self):
        pass   


    def open(self):
        """Called before first use.
        
        May be implemented to initialize a storage.
        """
        pass

    
    def close(self):
        """Called on shutdown."""
        pass

    
    def cleanup(self):
        """Purge expired locks (optional)."""
        pass

    
    def get(self, token):
        """Return a lock dictionary for a token.
        
        See wsgidav.lock_storage.LockStorageDict.get()
        """
        lock = cached_lock.get(token)
        if lock is None: 
            # Lock not found: purge dangling root-path entries
            _logger.debug("Lock purged dangling: %s" % token)
            self._deleteLock(lock)      
            return None
        expire = float(lock["expire"])
        if expire >= 0 and expire < time.time():
            _logger.debug("Lock timed-out(%s): %s" % (expire, lockString(lock)))
            self._deleteLock(lock)      
            return None
        return lock
    
    
    def create(self, path, lock):
        """Create a direct lock for a resource path.
        
        See wsgidav.lock_storage.LockStorageDict.create()
        """
        # We expect only a lock definition, not an existing lock
        assert lock.get("token") is None
        assert lock.get("expire") is None, "Use timeout instead of expire"
        assert path and "/" in path

        # Normalize root: /foo/bar 
        org_path = path
        path = normalizeLockRoot(path)
        lock["root"] = path

        # Normalize timeout from ttl to expire-date
        timeout = float(lock.get("timeout"))
        if timeout is None:
            timeout = LockStorageMemcache.LOCK_TIME_OUT_DEFAULT
        elif timeout < 0 or timeout > LockStorageMemcache.LOCK_TIME_OUT_MAX:
            timeout = LockStorageMemcache.LOCK_TIME_OUT_MAX     

        lock["timeout"] = timeout
        lock["expire"] = time.time() + timeout
        
        validateLock(lock)
        
        token = generateLockToken()
        lock["token"] = token
        
        # Append this lock root to current path list
        lockRoots = cached_lock.get("*")
        if lockRoots is None:
            lockRoots = {}
        lockRoots.setdefault(path, []).append(token)

        # Store lock and path lock list
        mapping = {token: lock,
                   "*": lockRoots}
        res = cached_lock.set_multi(mapping)
        if len(res) > 0:
            raise RuntimeError("Could not store lock")
        logging.info("lock.create(%r): %s\n\t%s" % (org_path, lock, lockRoots))
        return lock
    
    
    def refresh(self, token, timeout):
        """Modify an existing lock's timeout.
        
        See wsgidav.lock_storage.LockStorageDict.refresh()
        """
        lock = self.get(token) 
        assert lock, "Lock must exist"
        assert timeout == -1 or timeout > 0
        if timeout < 0 or timeout > LockStorageMemcache.LOCK_TIME_OUT_MAX:
            timeout = LockStorageMemcache.LOCK_TIME_OUT_MAX

        lock["timeout"] = timeout
        lock["expire"] = time.time() + timeout

        cached_lock.set(token, lock)
        return lock

    
    def _deleteLock(self, lock):
        """Internal method to prevent recursion when called .get() calls .delete()"""
        if lock is None:
            return False
        token = lock["token"]
        lockRoots = cached_lock.get("*")
        try:
            tokenlist = lockRoots[lock["root"]] 
            tokenlist.remove(token)
            if len(tokenlist) == 0:
                del lockRoots[lock["root"]]
            cached_lock.set("*", lockRoots)
        except Exception as e:
            logging.warning("_deleteLock(%s): %s failed to fix root list: %s" % (token, lock, e))
        logging.info("_deleteLock(%r): %s\n\t%s" % (token, lock, lockRoots))
        # Remove the lock
        cached_lock.delete(token)       
        return True
        
        
    def delete(self, token):
        """Delete lock.
        
        See wsgidav.lock_storage.LockStorageDict.delete()
        """
        lock = self.get(token)
        logging.debug("delete %s" % lockString(lock))
        return self._deleteLock(lock)
    
    
    def getLockList(self, path, includeRoot, includeChildren, tokenOnly):
        """Return a list of direct locks for <path>.

        See wsgidav.lock_storage.LockStorageDict.getLockList()
        """
        path = normalizeLockRoot(path)
        lockRoots = cached_lock.get("*")
        if not lockRoots:
            return []

        def __appendLocks(toklist):
            if tokenOnly:
                lockList.extend(toklist)
            else:
                for token in toklist:
                    lock = self.get(token)
                    if lock:
                        lockList.append(lock)

        lockList = []

        if includeRoot and path in lockRoots:
            __appendLocks(lockRoots[path])
                
        if includeChildren:
            for root, toks in list(lockRoots.items()):
                if util.isChildUri(path, root): 
                    __appendLocks(toks)
        
        return lockList
