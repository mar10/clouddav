# -*- coding: iso-8859-1 -*-
# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
#
# The original source for this module was taken from gaedav:
# (c) 2009 Haoyu Bai (http://gaedav.google.com/).
"""
File system operations.
"""
from __future__ import absolute_import

import time
import StringIO
import logging
from .model import Dir, File, Path
#from btfs import memcash

def initfs():
    """
    Make sure fs already inited.
    (e.g. there's a '/' and '/dav' collection in db).
    """
    logging.debug("fs.initfs")
    if not isdir('/'):
        logging.info("fs.initfs: mkdir '/'")
        mkdir('/')
    if not isdir('/dav'):
        logging.info("fs.initfs: mkdir '/dav'")
        mkdir('/dav')
    return

#@memcash.cache(ttl=10)  # cache function result for 10 seconds
def _getresource(path):
    """Return a model.Dir or model.File object for `path`.
    
    `path` may be an existing Dir/File entity. 
    Since _getresource is called by most other functions in the `fs` module, 
    this allows the DAV provider to pass a cached resource, thus implementing 
    a simple per-request caching, like in::
    
        statresults = fs.stat(self.pathEntity)
    
    Return None, if path does not exist.
    """
    if type(path) in (Dir, File):
        logging.debug("_getresource(%r): request cache HIT" % path.path)
        return path
#    logging.info("_getresource(%r)" % path)
    p = Path.retrieve(path)
    assert p is None or type(p) in (Dir, File)
    return p

def getdir(s):
    p = _getresource(s)
    if type(p) is Dir:
        return p
    return None

def getfile(s):
    p = _getresource(s)
    if type(p) is File:
        return p
    return None

def isdir(s):
    p = getdir(s)
    return p is not None

def isfile(s):
    p = getfile(s)
    return p is not None

def exists(s):
    return _getresource(s) is not None

def stat(s):
 
    def epoch(tm):
        return time.mktime(tm.utctimetuple())
    p = _getresource(s)
    size = p.size
    atime = epoch(p.modify_time)
    mtime = atime
    ctime = epoch(p.create_time)

    def itemgetter(n):
        return lambda self: self[n]
    # run
    #   collections.namedtuple('stat_result', 'st_size st_atime st_mtime st_ctime', verbose=True)
    # to get the following class
    class stat_result(tuple):                                                                         
        'stat_result(st_size, st_atime, st_mtime, st_ctime)'                                      

        __slots__ = () 

        _fields = ('st_size', 'st_atime', 'st_mtime', 'st_ctime') 

        def __new__(cls, st_size, st_atime, st_mtime, st_ctime):
            return tuple.__new__(cls, (st_size, st_atime, st_mtime, st_ctime))

        @classmethod
        def _make(cls, iterable, new=tuple.__new__, len=len):
            'Make a new stat_result object from a sequence or iterable'
            result = new(cls, iterable)
            if len(result) != 4:
                raise TypeError('Expected 4 arguments, got %d' % len(result))
            return result

        def __repr__(self):
            return 'stat_result(st_size=%r, st_atime=%r, st_mtime=%r, st_ctime=%r)' % self

#        def _asdict(t):
#            'Return a new dict which maps field names to their values'
#            return {'st_size': t[0], 'st_atime': t[1], 'st_mtime': t[2], 'st_ctime': t[3]}

        def _replace(self, **kwds):
            'Return a new stat_result object replacing specified fields with new values'
            result = self._make(map(kwds.pop, ('st_size', 'st_atime', 'st_mtime', 'st_ctime'), self))
            if kwds:
                raise ValueError('Got unexpected field names: %r' % kwds.keys())
            return result

        def __getnewargs__(self):
            return tuple(self)        
        
        st_size = property(itemgetter(0))
        st_atime = property(itemgetter(1))
        st_mtime = property(itemgetter(2))
        st_ctime = property(itemgetter(3))

    return stat_result(size, atime, mtime, ctime)

def mkdir(s):
    p = Dir.new(s)
    return p

def rmdir(s):
    p = getdir(s)
    p.delete(recursive=False)
    return

def rmtree(s):
    p = getdir(s)
    p.delete(recursive=True)
    return

def copyfile(s, d):
    # raise, if not exists:
    sio = btopen(s, 'rb')
    # overwrite destination, if exists:
    dio = btopen(d, 'wb')
    while True:
        buf = sio.read(8*1024)
        if not buf:
            break
        dio.write(buf)
    dio.close()
    sio.close()
    return

def unlink(s):
    f = getfile(s)
    f.delete()
    return

def btopen(s, mode='r'):
    """Open the file (eg. return a BtIO object)"""
    f = getfile(s)
    if f is None:
        # Create targtet file, but only in write mode
        if not 'w' in mode:
            raise ValueError("source not found %r" % s)
        f = File.new(path=s)
    io = BtIO(f, mode)
    return io

def listdir(s):
    p = getdir(s)
    path_str = [c.basename(c.path).encode('utf-8') for c in p.get_content()]
    return path_str


#===============================================================================
# BtIO
#===============================================================================
class BtIO(StringIO.StringIO):
    """
    Bigtable file IO object
    """
    def __init__(self, btfile, mode):
        self.btfile = btfile
        self.mode = mode
        StringIO.StringIO.__init__(self, btfile.get_content())
        return

    def is_readonly(self):
        return 'w' not in self.mode

    def flush(self):
        StringIO.StringIO.flush(self)
        if not self.is_readonly():
            self.btfile.put_content(self.getvalue())
        return

    def close(self):
        self.flush()
        StringIO.StringIO.close(self)
        return

    def __del__(self):
        try:
            if not self.closed:
                self.close()
        except AttributeError:
            pass
