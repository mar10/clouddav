import time
import StringIO
import logging
from model import Dir, File


"""
File system operations.
"""

def initfs():
    """
    Make sure fs already inited.
    (eg. there's a '/' in db).
    """
    if not isdir('/'):
        mkdir('/')
    return

def getdir(s):
    p = Dir.retrieve(s)
    return p

def getfile(s):
    f = File.retrieve(s)
    return f

def isdir(s):
    p = getdir(s)
    result = p is not None
    return result

def isfile(s):
    p = getfile(s)
    return p is not None

def exists(s):
    return isdir(s) or isfile(s)

def stat(s):
 
    def epoch(tm):
        return time.mktime(tm.utctimetuple())

    p = getdir(s) or getfile(s)
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

        def _asdict(t):
            'Return a new dict which maps field names to their values'
            return {'st_size': t[0], 'st_atime': t[1], 'st_mtime': t[2], 'st_ctime': t[3]}

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
    p.delete()
    return

def unlink(s):
    f = getfile(s)
    f.delete()
    return

def btopen(s, mode='r'):
    """
    Open the file (eg. return a BtIO object)
    """
    f = getfile(s)
    if f is None:
        f = File.new(path=s)
    io = BtIO(f, mode)
    return io

def listdir(s):
    p = getdir(s)
    path_str = [c.basename(c.path).encode('utf-8') for c in p.get_contents()]
    return path_str


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
