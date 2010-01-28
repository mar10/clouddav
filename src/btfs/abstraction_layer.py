#!/usr/bin/env python
import os.path
import logging
import md5
import mimetypes
from pyfileserver import processrequesterrorhandler, httpdatehelper
import fs

class AbstractionLayer(object):
   def __init__(self): 
       fs.initfs()
       return

   def getResourceDescriptor(self, respath):
      resdesc = self.getResourceDescription(respath)
      ressize = str(self.getContentLength(respath)) + " B"
      resmod = httpdatehelper.getstrftime(self.getLastModified(respath))
      if fs.isdir(respath):
         ressize = ""
      return [resdesc, ressize, resmod]
   
   def getResourceDescription(self, respath):
      if fs.isdir(respath):
         return "Directory"
      elif fs.isfile(respath):
         return "File"
      else:
         return "Unknown"

   def getContentType(self, respath):
      if fs.isfile(respath):
         (mimetype, mimeencoding) = mimetypes.guess_type(respath, strict=False)
         logging.debug("Guess type of %s is %s", repr(respath), mimetype)
         if mimetype == '' or mimetype is None:
            mimetype = 'application/octet-stream' 
         mimetype = 'application/octet-stream'
         return mimetype
      else:
         return "httpd/unix-directory" 

   def getLastModified(self, respath):
         statresults = fs.stat(respath)
         return statresults.st_mtime
   
   def getContentLength(self, respath):
      if not fs.isfile(respath):
         return 0
      else:
         statresults = fs.stat(respath)
         return statresults.st_size
   
   def getEntityTag(self, respath):
      if not fs.isfile(respath):
         return '"' + md5.new(respath).hexdigest() +'"'
      statresults = fs.stat(respath)
      return md5.new(respath).hexdigest() + '-' + str(statresults.st_mtime) + '-' + str(statresults.st_size)

   def matchEntityTag(self, respath, entitytag):
      return entitytag == self.getEntityTag(respath)

   def isCollection(self, respath):
      return fs.isdir(respath)
   
   def isResource(self, respath):
      return fs.isfile(respath)
   
   def exists(self, respath):
      return fs.exists(respath)
   
   def createCollection(self, respath):
      fs.mkdir(respath)
   
   def deleteCollection(self, respath):
      fs.rmdir(respath)

   def supportEntityTag(self, respath):
      return True

   def supportLastModified(self, respath):
      return True
   
   def supportContentLength(self, respath):
      return True
   
   def supportRanges(self, respath):
      return True
   
   def openResourceForRead(self, respath):
      mime = self.getContentType(respath)
      if mime.startswith("text"):
         return fs.btopen(respath, 'r')
      else:
         return fs.btopen(respath, 'rb')
   
   def openResourceForWrite(self, respath, contenttype=None):
      if contenttype is None:
         istext = False
      else:
         istext = contenttype.startswith("text")
      if istext:
         return fs.btopen(respath, 'w')
      else:
         return fs.btopen(respath, 'wb')
   
   def deleteResource(self, respath):
      fs.unlink(respath)
   
   def copyResource(self, respath, destrespath):
      raise NotImplementedError
      #shutil.copy2(respath, destrespath)
   
   def getContainingCollection(self, respath):
      #TODO
      return os.path.dirname(respath)
   
   def getCollectionContents(self, respath):
      return fs.listdir(respath)
      
   def joinPath(self, rescollectionpath, resname):
      #TODO
      return os.path.join(rescollectionpath, resname)

   def splitPath(self, respath):
      #TODO
      return os.path.split(respath)

   def writeProperty(self, respath, propertyname, propertyns, propertyvalue):
      raise HTTPRequestException(processrequesterrorhandler.HTTP_CONFLICT)

   def removeProperty(self, respath, propertyname, propertyns):
      raise HTTPRequestException(processrequesterrorhandler.HTTP_CONFLICT)

   def getProperty(self, respath, propertyname, propertyns):
      if propertyns == 'DAV:':
         isfile = fs.isfile(respath)
         if propertyname == 'creationdate':
             statresults = fs.stat(respath)
             return httpdatehelper.rfc3339(statresults.st_ctime)
         elif propertyname == 'getcontenttype':
             return self.getContentType(respath)
         elif propertyname == 'resourcetype':
            if fs.isdir(respath):
               return '<D:collection />'
            else:
               return ''
         elif propertyname == 'getlastmodified':
            statresults = fs.stat(respath)
            return httpdatehelper.getstrftime(statresults.st_mtime)
         elif propertyname == 'getcontentlength':
            if isfile:
               statresults = fs.stat(respath)
               return str(statresults.st_size)
            else:
                return '0'
            raise HTTPRequestException(processrequesterrorhandler.HTTP_NOT_FOUND)        
         elif propertyname == 'getetag':
            return self.getEntityTag(respath)
      raise HTTPRequestException(processrequesterrorhandler.HTTP_NOT_FOUND)
   
   def isPropertySupported(self, respath, propertyname, propertyns):
      supportedliveprops = ['creationdate', 'getcontenttype','resourcetype','getlastmodified', 'getcontentlength', 'getetag']
      if propertyns != "DAV:" or propertyname not in supportedliveprops:
         return False
      return True
   
   def getSupportedPropertyNames(self, respath):
      appProps = []
      #DAV properties for all resources
      appProps.append( ('DAV:','creationdate') )
      appProps.append( ('DAV:','getcontenttype') )
      appProps.append( ('DAV:','resourcetype') )
      appProps.append( ('DAV:','getlastmodified') )
      appProps.append( ('DAV:','getetag') )
      appProps.append( ('DAV:','getcontentlength') )
      return appProps
   
   def resolvePath(self, resheadpath, urlelementlist):
      relativepath = os.sep.join(urlelementlist)
      relativepath = os.path.normpath(relativepath)
     
      normrelativepath = ''
      if relativepath != '':          # avoid adding of .s
         normrelativepath = os.path.normpath(relativepath)   

      return resheadpath + os.sep + normrelativepath

   def breakPath(self, resheadpath, respath):      
      relativepath = respath[len(resheadpath):].strip(os.sep)
      return relativepath.split(os.sep)


