from builtins import str
from builtins import map
import time, os, random
from google.appengine.api import memcache
CURRENT_VERSION_ID = os.environ.get('CURRENT_VERSION_ID','0')
local_cache = {}
DOG_PILE_WINDOW = 10 # seconds
 
import logging

 
def cash(ttl=60, key=None, ver=CURRENT_VERSION_ID, pre='', off=False):
    """
    Copyright (C)  2009  twitter.com/rcb
    
    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
    
    ======================================================================
    
    Builds a decorator that caches any function for ttl (time to live) secs
    using both a local dict and memcache.  Keys are strings but can be static, 
    formatting, or callable, and caching can be disabled entirely.  Keys 
    are auto invalidated on each deployment because keys include the 
    application's current_version_id by default.
    
    It is called 'cash' because it can save lots of money in API CPU.
    
    >>> count = 0
    >>> def inc():
    ...     global count
    ...     count+=1
    ...     return count
    
    >>> @cash()              # uses 'foo' in key
    ... def foo(*a):
    ...     return inc()
    >>> foo(1,2) == foo(1,2)
    True
    >>> foo(1,1) != foo(2,2) # varies by args
    True
    >>> @cash(key='foo:%s:%s', ver=1)
    ... def foo(*a):
    ...     return inc()
    >>> foo(1,2) == foo(1,2)
    True
    >>> foo(1,1) != foo(2,2) # vary by args
    True
    
    >>> @cash(key=lambda *a,**k: 'foo:%s'%(a[0]+a[1],), ver=2)
    ... def foo(*a):
    ...     return inc()
    >>> foo(1,2) == foo(1,2)
    True
    >>> foo(1,3) == foo(3,1) # dynamic key
    True
    
    >>> @cash(off=True, ver=3)
    ... def foo(*a):
    ...     return inc()
    >>> foo.__name__         # not wrapped
    'foo'
    >>> foo() != foo()       # caching disabled
    True
    
    ## can uncomment slow tests
    # >>> @cash(ttl=1, ver=4)
    # ... def foo(*a):
    # ...     return inc()
    # >>> val = foo() 
    # >>> foo() == val         # cached
    # True
    # >>> time.sleep(2)
    # >>> foo() != val         # new value
    # True
    # 
    # >>> @cash(ttl=0, ver=5)
    # ... def foo(*a):
    # ...     return inc()
    # >>> val = foo() 
    # >>> foo() == val         # cached
    # True
    # >>> time.sleep(1)
    # >>> foo() == val         # does not expire
    # True
    
    :param key: A formatting string or callable accepting args.
    :param ttl: Time to live in seconds: 0 means do not expire.
    :param ver: Version id: defaults to app current version id.
    :param pre: A Key prefix that will be applied to every key.
    :param off: Caching will be disabled if off is set to True.
    """
    
    ttl = int(ttl)
    keytmpl = 'cash(v=%s,k=%s:%%s)' % (ver,pre)
    def decorator(wrapped):
        if off:
            return wrapped
        if callable(key):
            make_key = key
        else:
            if key:
                kee = str(key)
            else:
                name = getattr(wrapped, '__name__', 'wrapper')
                if name == 'wrapper':
                    raise ValueError('cash(key=?) needs a key')
                kee = '__name__:%s' % name
            count = kee.count('%')
            if count:
                make_key = lambda *a, **k: kee % a[:count]
            else:
                make_key = lambda *a, **k: '%s(%s)'%(kee,','.join(map(str,a)))
        def wrapper(*args, **kwargs):
            now = int(time.time())
            keystr = keytmpl % make_key(*args, **kwargs)
            if keystr in local_cache:
                expire, val = local_cache[keystr]
                if expire - now > DOG_PILE_WINDOW:
                    logging.info("@cash: HIT %r" % keystr)
                    return val
            logging.info("@cash: get %r" % keystr)
            cached = memcache.get(keystr)
            if cached:
                (expire, val) = cached
                """ probabilistically avoid a dog pile """
                if ttl > DOG_PILE_WINDOW or ttl == 0:
                    remaining = expire - now
                    if DOG_PILE_WINDOW > remaining:
                        if random.uniform(0, DOG_PILE_WINDOW) > remaining:
                            cached = None
            if cached is None:
                if ttl == 0:
                    expire = now + 60*60*24*28 # 28 days
                else:
                    expire = now + ttl
                val = wrapped(*args, **kwargs)
                logging.info("@cash: set %r" % keystr)
                memcache.set(keystr, (expire, val), ttl)    
            local_cache[keystr] = (expire, val)
            return val       
        return wrapper
    return decorator
cache=cash
