import os.path
import logging
from google.appengine.ext import db
from google.appengine.ext.db import GqlQuery
from cache import cached_dir, cached_file, cached_content

#TODO: may apply the technique described here:
# http://code.google.com/appengine/docs/python/datastore/keysandentitygroups.html

class Path(db.Model):
    path = db.StringProperty(required=True)
    size = db.IntegerProperty(required=True, default=0) # cache the size of content, 0 for dir
    create_time = db.DateTimeProperty(required=True, auto_now_add = True)
    modify_time = db.DateTimeProperty(required=True, auto_now = True)

    def put(self):
        db.Model.put(self)
        self.cache.set(self.path, self)
        return 

    def delete(self):
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
        if not isinstance(p, unicode):
            logging.debug("Path.normalize: encoding str %s to unicode.", repr(p))
            p = str.decode(p, 'utf-8')
        result = os.path.normpath(p)
        result = result.replace('//','/')
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

    @classmethod
    def retrieve(cls, path):
        path = cls.normalize(path)
        result = cls.cache.get(path)
        if result:
            return result
        logging.debug("Retrieving with path = %s", repr(path))
        result = list(cls.gql("WHERE path = :1", path))
        if len(result) == 1:
            result = result[0]
            cls.cache.set(path, result)
            return result
        elif len(result) == 0:
            return None
        else:
            raise ValueError("The given path has more than one entities", path)

    @classmethod
    def new(cls, path):
        path = cls.normalize(path)
        # TODO raise error when this path does exist

        # here we use Dir.retrieve because the parent must be a Dir.
        parent_path = Dir.retrieve(cls.get_parent_path(path))
        result = cls(path=path, parent_path=parent_path)
        result.put()
        return result

class Dir(Path):
    parent_path = db.ReferenceProperty(Path)
    cache = cached_dir
   
    def get_contents(self):
        result = list(self.dir_set) + list(self.file_set)
        return result    

class File(Path):
    ChunkSize = 800*1024 # split file to chunks at most 800K

    parent_path = db.ReferenceProperty(Path)
    #content = db.BlobProperty(default='')
    #content = db.ListProperty(db.Blob)

    cache = cached_file

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
            logging.debug("File.put_content putting the chunk with offset = %d", i)
            data = s[i:i+self.ChunkSize]
            ck = Chunk(file=self, offset=i, data=data)
            ck.put()
        self.put()
        return

    def delete(self):
        """
        Also delete chunks.
        """
        for chunk in self.chunk_set:
            chunk.delete()
        Path.delete(self)
        return

class Chunk(db.Model):
    file = db.ReferenceProperty(File)
    offset = db.IntegerProperty(required=True)
    data = db.BlobProperty(default='')

    def __len__(self):
        return len(self.data)

