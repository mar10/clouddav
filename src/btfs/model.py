# -*- coding: iso-8859-1 -*-

# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
#
# The original source for this module was written by Haoyu Bai (http://gaedav.google.com/).  

import os.path
import logging
from google.appengine.ext import db
from google.appengine.ext.db import polymodel
#from google.appengine.ext.db import GqlQuery
#from cache import cached_dir, cached_file, cached_content
from cache import cached_resource
#from google.appengine.api import memcache

DO_EXPENSIVE_CHECKS = False
#DO_EXPENSIVE_CHECKS = True

class UnmappedPath(object):
    """Dummy object to cache lookups for non-existent URLs."""
    pass

#TODO: may apply the technique described here:
# http://code.google.com/appengine/docs/python/datastore/keysandentitygroups.html

#===============================================================================
# Path
#===============================================================================
#class Path(db.Model):
class Path(polymodel.PolyModel):
    """Derived from PolyModel, so we can perform queries on objects of the parent class"""
    path = db.StringProperty(required=True)
    size = db.IntegerProperty(required=True, default=0) # cache the size of content, 0 for dir
    create_time = db.DateTimeProperty(required=True, auto_now_add = True)
    modify_time = db.DateTimeProperty(required=True, auto_now = True)

    cache = cached_resource
     
    def put(self):
        logging.debug("Path.put(%r)" % (self.path))
        db.Model.put(self)
        self.cache.set(self.path, self)
        return 

    def delete(self):
        logging.debug("Path.delete(%r)" % (self.path))
        if self.path == "/":
            raise RuntimeError("Though shalt not delete root")
        self.cache.delete(self.path)
        return db.Model.delete(self)

    @classmethod
    def normalize(cls, p):
        """
         /foo/bar/ -> /foo/bar
         / -> /
         // -> /
        """
        # XXX: this is not portable on win32
#        if not isinstance(p, unicode):
#            logging.debug("Path.normalize: encoding str %s to unicode.", repr(p))
#            p = str.decode(p, 'utf-8')
        result = os.path.normpath(p)
        # mw: added for Windows:
        result = result.replace("\\", "/")
        result = result.replace('//','/')
        if not isinstance(result, unicode):
#            logging.debug("Path.normalize: encoding str %s to unicode.", repr(p))
            result = result.decode('utf-8')
        if p != result:
            logging.debug("Path.normalize(%r): %r." % (p, result))
        return result

    @classmethod
    def basename(cls, p):
        return os.path.basename(p)

    @classmethod
    def get_parent_path(cls, p):
        """
         /foo/bar -> /foo
        """
        return os.path.dirname(cls.normalize(p))

#    @classmethod
#    def check_existence(cls, path):
#        """Checking for a path existence.
#        
#        Querying for the key should be faster than SELECET *.
#        This also 
#        """
#        path = cls.normalize(path)
#        result = cls.cache.get(path)
#        if result:
#            return result
#        logging.debug("check_existence(%r)" % path)
#        result = db.GqlQuery("SELECT __key__ WHERE path = :1", path)
#        return result is not None

    @classmethod
    def retrieve(cls, path):
        logging.debug("Path.retrieve(%s, %r)" % (cls.__name__, path))
        assert cls is Path
        path = cls.normalize(path)
        assert path.startswith("/")
        result = cls.cache.get(path)
        if result:
            return result
        result = list(cls.gql("WHERE path = :1", path))
        if len(result) == 1:
            result = result[0]
#            assert type(result) in (Path, cls)
            cls.cache.set(path, result)
            return result
        elif len(result) == 0:
            # TODO: cache 'Not found' also
            return None
        else:
            raise ValueError("The given path has more than one entities", path)

    @classmethod
    def new(cls, path):
        # Make sure, we don't instantiate <Path> objects
        assert cls in (Dir, File)
        logging.debug("%s.new(%r)" % (cls.__name__, path))
        path = cls.normalize(path)
        # here we use Dir.retrieve because the parent must be a Dir.
#        parent_path = Dir.retrieve(cls.get_parent_path(path))
        parent_path = Path.retrieve(cls.get_parent_path(path))
        if path != "/":
            if not parent_path:
                raise RuntimeError("Parent path does not exists for: %r" % path)
            if type(parent_path) is not Dir:
                raise RuntimeError("Parent must be a Dir for: %r" % path)
        if DO_EXPENSIVE_CHECKS:
            if Path.retrieve(path):
                raise RuntimeError("Path exists: %r" % path)
        result = cls(path=path, parent_path=parent_path)
        result.put()
        return result


#===============================================================================
# Dir
#===============================================================================
class Dir(Path):
    parent_path = db.ReferenceProperty(Path)
#    cache = cached_dir
   
    def get_content(self):
#        result = list(self.dir_set) + list(self.file_set)
#        logging.debug("Dir.get_content: %r" % result)
        # TODO: ORDER BY
        result = list(Path.gql("WHERE parent_path=:1", self))
        logging.debug("Dir.get_content: %r" % result)
        
        return result    

    def delete(self, recursive=False):
        logging.debug("Dir.delete(%s): %r" % (recursive, self.path))
        if not recursive:
            # TODO: faster lookup (for __key__)
            if len(self.get_content()) > 0:
                raise RuntimeError("Dir must be empty")
        else:
            for p in self.get_content():
                logging.debug("Dir.delete(%s): %r, p=%r" % (recursive, self.path, p))
                if type(p) is Dir:
                    p.delete(recursive)
                elif type(p) is File:
                    p.delete()
                else:
                    RuntimeError("invalid child type")
#            for d in self.dir_set:
#                logging.debug("Dir.delete(%s): %r, d=%r" % (recursive, self.path, d))
#                d.delete(recursive)
#            for f in self.file_set:
#                logging.debug("Dir.delete(%s): %r, f=%r" % (recursive, self.path, f))
#                f.delete() 
        Path.delete(self)
        return

#===============================================================================
# File
#===============================================================================
class File(Path):
    ChunkSize = 800*1024 # split file to chunks at most 800K

    parent_path = db.ReferenceProperty(Path)
    #content = db.BlobProperty(default='')
    #content = db.ListProperty(db.Blob)

#    cache = cached_file

    def put(self):
        if self.is_saved():
            self.size = sum(len(chunk) for chunk in self.chunk_set)
        else:
            self.size = 0
        Path.put(self)
        return

    def get_content(self):
        """
        Join chunks together.
        """
        if self.is_saved():
            chunks = Chunk.gql("WHERE file=:1 ORDER BY offset ASC", self)
        else:
            chunks = []
        result = ''.join(chunk.data for chunk in chunks)
        return result
    
    def put_content(self, s):
        """
        Split the DB transaction to serveral small chunks,
        to keep we don't exceed appengine's limit.
        """
        size = len(s)
        #self.content = []
        # clear old chunks
        for chunk in self.chunk_set:
            chunk.delete()

        # put new datas
        for i in range(0, size, self.ChunkSize):
            logging.debug("File.put_content putting the chunk with offset = %d" % i)
            data = s[i:i+self.ChunkSize]
            ck = Chunk(file=self, offset=i, data=data)
            ck.put()
        self.put()
        return

    def delete(self):
        """
        Also delete chunks.
        """
        logging.debug("File.delete %s" % repr(self.path))
        for chunk in self.chunk_set:
            chunk.delete()
        Path.delete(self)
        return

#===============================================================================
# Chunk
#===============================================================================
class Chunk(db.Model):
    file = db.ReferenceProperty(File)
    offset = db.IntegerProperty(required=True)
    data = db.BlobProperty(default='')

    def __len__(self):
        return len(self.data)

