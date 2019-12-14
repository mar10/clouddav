# -*- coding: iso-8859-1 -*-
# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
Implementation of a WsgiDAV provider that implements a virtual file system based
on Google's Big Table.
"""
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from btfs.model import Path, Dir, File
import logging
import md5
import mimetypes
from . import fs

try:
    from io import StringIO
except ImportError:
    from io import StringIO #@UnusedImport
from wsgidav.dav_provider import DAVProvider, _DAVResource
from wsgidav import util

__docformat__ = "reStructuredText en"

#_logger = util.getModuleLogger(__name__)
BUFFER_SIZE = 8192

#===============================================================================
# BTFSResource classes
#===============================================================================
class BTFSResource(_DAVResource):
    """."""
    _supportedProps = ["{btfs:}key",
                       ]

    def __init__(self, path, environ):
        self.pathEntity = Path.retrieve(path)
        if not self.pathEntity:
            raise ValueError("Path not found: %r" % path)
        isCollection = ( type(self.pathEntity) is Dir )
        logging.debug("BTFSResource(%r): %r" % (path, isCollection))
        super(BTFSResource, self).__init__(path, isCollection, environ)
        self.statresults = fs.stat(self.pathEntity)

    def getContentLength(self):
        if self.isCollection:
            return None
        return self.statresults.st_size

    def getContentType(self):
        if self.isCollection:
            # TODO: should be None?
            return "httpd/unix-directory" 
        (mimetype, _mimeencoding) = mimetypes.guess_type(self.path, strict=False)
        logging.debug("Guess type of %s is %s", repr(self.path), mimetype)
        if mimetype == '' or mimetype is None:
            mimetype = 'application/octet-stream' 
#        mimetype = 'application/octet-stream'
        return mimetype

    def getCreationDate(self):
        return self.statresults.st_ctime
    
    def getDisplayName(self):
        return self.name
    
    def getEtag(self):
        if self.isCollection:
            return '"' + md5.new(self.path).hexdigest() +'"'
        return md5.new(self.path).hexdigest() + '-' + str(self.statresults.st_mtime) + '-' + str(self.statresults.st_size)
    
    def getLastModified(self):
        return self.statresults.st_mtime
    
    def supportRanges(self):
        return True

    def getMemberNames(self):
        """Return list of (direct) collection member names (_DAVResource or derived).
        
        See _DAVResource.getMemberList()
        """
        return fs.listdir(self.pathEntity)
    
    def getMember(self, name):
        """Return list of (direct) collection members (_DAVResource or derived).
        
        See _DAVResource.getMemberList()
        """
        res = BTFSResource(util.joinUri(self.path, name), self.environ)
        return res

#    def handleDelete(self):
#        raise DAVError(HTTP_FORBIDDEN)
#    def handleMove(self, destPath):
#        raise DAVError(HTTP_FORBIDDEN)
#    def handleCopy(self, destPath, depthInfinity):
#        raise DAVError(HTTP_FORBIDDEN)


    # --- Read / write ---------------------------------------------------------
    
    def createEmptyResource(self, name):
        """Create an empty (length-0) resource.
        
        See _DAVResource.createEmptyResource()
        """
        assert self.isCollection
        assert not "/" in name
        path = util.joinUri(self.path, name) 
        f = fs.btopen(path, "wb")
        # FIXME: should be length-0
#        f.write(".")
        f.close()
        return self.provider.getResourceInst(path, self.environ)
    

    def createCollection(self, name):
        """Create a new collection as member of self.
        
        See _DAVResource.createCollection()
        """
        assert self.isCollection
        path = util.joinUri(self.path, name) 
        fs.mkdir(path)


    def getContent(self):
        """Open content as a stream for reading.
         
        See _DAVResource.getContent()
        """
        assert not self.isCollection
#        return fs.btopen(self.path, "rb")
        return fs.btopen(self.pathEntity, "rb")
   

    def beginWrite(self, contentType=None):
        """Open content as a stream for writing.
         
        See _DAVResource.beginWrite()
        """
        assert not self.isCollection
#        return fs.btopen(self.path, "wb")
        return fs.btopen(self.pathEntity, "wb")

    
    def supportRecursiveDelete(self):
        """Return True, if delete() may be called on non-empty collections 
        (see comments there).
        
        This method MUST be implemented for collections (not called on 
        non-collections).
        """
        # TODO: should support recursive operations 
        return False

    def delete(self):
        """Remove this resource or collection (recursive).
        
        See _DAVResource.delete()
        """
        if self.isCollection:
#            fs.rmtree(self.path)
            fs.rmtree(self.pathEntity)
        else:
#            fs.unlink(self.path)
            fs.unlink(self.pathEntity)
        self.removeAllProperties(True)
        self.removeAllLocks(True)
            

    def copyMoveSingle(self, destPath, isMove):
        """See _DAVResource.copyMoveSingle() """
        assert not util.isEqualOrChildUri(self.path, destPath)
        if self.isCollection:
            # Create destination collection, if not exists
            if not fs.exists(destPath):
                fs.mkdir(destPath)
        else:
            # Copy file (overwrite, if exists)
#            fs.copyfile(self.path, destPath)
            fs.copyfile(self.pathEntity, destPath)
#            shutil.copy2(self._filePath, fpDest)
        # (Live properties are copied by copy2 or copystat)
        # Copy dead properties
        propMan = self.provider.propManager
        if propMan:
            destRes = self.provider.getResourceInst(destPath, self.environ)
            if isMove:
                propMan.moveProperties(self.getRefUrl(), destRes.getRefUrl(), 
                                       withChildren=False)
            else:
                propMan.copyProperties(self.getRefUrl(), destRes.getRefUrl())
               

    def supportRecursiveMove(self, destPath):
        """Return True, if moveRecursive() is available (see comments there)."""
        # TODO: should support recursive operations 
        return False

    
#    def moveRecursive(self, destPath):
#        """See _DAVResource.moveRecursive() """
#        # FIXME
#        raise NotImplementedError()
#        fpDest = self.provider._locToFilePath(destPath)
#        assert not util.isEqualOrChildUri(self.path, destPath)
#        assert not os.path.exists(fpDest)
#        _logger.debug("moveRecursive(%s, %s)" % (self._filePath, fpDest))
#        shutil.move(self._filePath, fpDest)
#        # (Live properties are copied by copy2 or copystat)
#        # Move dead properties
#        if self.provider.propManager:
#            destRes = self.provider.getResourceInst(destPath, self.environ)
#            self.provider.propManager.moveProperties(self.getRefUrl(), destRes.getRefUrl(), 
#                                                     withChildren=True)
               


    
    def getPropertyNames(self, isAllProp):
        """Return list of supported property names in Clark Notation.
        
        See _DAVResource.getPropertyNames() 
        """
        # Let base class implementation add supported live and dead properties
        propNameList = super(BTFSResource, self).getPropertyNames(isAllProp)
        # Add custom live properties (report on 'allprop' and 'propnames')
#        propNameList.extend(BTFSResource._supportedProps)
        return propNameList

    def getPropertyValue(self, propname):
        """Return the value of a property.
        
        See _DAVResource.getPropertyValue()
        """
        # Supported custom live properties
        if propname == "{btfs:}key":
            return self._data["key"]
        # Let base class implementation report live and dead properties
        return super(BTFSResource, self).getPropertyValue(propname)
    

#    def setPropertyValue(self, propname, value, dryRun=False):
#        """Set or remove property value.
#        
#        See _DAVResource.setPropertyValue()
#        """
#        if value is None:
#            # We can never remove properties
#            raise DAVError(HTTP_FORBIDDEN)
##        if propname == "{btfs:}key":
##            # value is of type etree.Element
##            self._data["tags"] = value.text.split(",")
#        elif propname == "{virtres:}description":
#            # value is of type etree.Element
#            self._data["description"] = value.text
#        elif propname in VirtualResource._supportedProps:
#            # Supported property, but read-only    
#            raise DAVError(HTTP_FORBIDDEN,  
#                           errcondition=PRECONDITION_CODE_ProtectedProperty)
#        else:
#            # Unsupported property    
#            raise DAVError(HTTP_FORBIDDEN)
#        # Write OK
#        return  
              

        
         
#===============================================================================
# BTFSResourceProvider
#===============================================================================

class BTFSResourceProvider(DAVProvider):
    """
    WsgiDAV provider that implements a virtual filesystem based on Googles Big Table.
    """
    def __init__(self):
        super(BTFSResourceProvider, self).__init__()
        fs.initfs()

    def getResourceInst(self, path, environ):
        self._count_getResourceInst += 1
        try:
            res = BTFSResource(path, environ)
        except:
            logging.exception("getResourceInst(%r) failed" % path)
            res = None
        logging.debug("getResourceInst(%r): %s" % (path, res))
        return res
