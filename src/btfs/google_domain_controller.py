# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
Implementation of a domain controller that uses the Users Service of 
Google App Engine.

See http://code.google.com/appengine/docs/python/users/

See `Developers info`_ for more information about the WsgiDAV architecture.

.. _`Developers info`: http://docs.wsgidav.googlecode.com/hg/html/develop.html  
"""
import sys
__docformat__ = "reStructuredText"

class GoogleDomainController(object):

    def __init__(self, userMap):
        self.userMap = userMap
#        self.allowAnonymous = allowAnonymous
           

    def __repr__(self):
        return self.__class__.__name__


    def getDomainRealm(self, inputURL, environ):
        """Resolve a relative url to the  appropriate realm name."""
        # we don't get the realm here, its already been resolved in request_resolver
        davProvider = environ["wsgidav.provider"]
        if not davProvider:
            if environ["wsgidav.verbose"] >= 2:
                print >>sys.stderr, "getDomainRealm(%s): '%s'" %(inputURL, None)
            return None
        realm = davProvider.sharePath
        if realm == "":
            realm = "/"
#        if environ["wsgidav.verbose"] >= 2:
#            print >>sys.stderr, "getDomainRealm(%s): '%s'" %(inputURL, realm)
        return realm

    
    def requireAuthentication(self, realmname, environ):
        """Return True if this realm requires authentication or False if it is 
        available for general access."""
        # TODO: Should check for --allow_anonymous?
#        assert realmname in environ["wsgidav.config"]["user_mapping"], "Currently there must be at least on user mapping for this realm"
        return realmname in self.userMap
    
    
    def isRealmUser(self, realmname, username, environ):
        """Returns True if this username is valid for the realm, False otherwise."""
#        if environ["wsgidav.verbose"] >= 2:
#            print >>sys.stderr, "isRealmUser('%s', '%s'): %s" %(realmname, username, realmname in self.userMap and username in self.userMap[realmname])
        return realmname in self.userMap and username in self.userMap[realmname]
            
    
    def getRealmUserPassword(self, realmname, username, environ):
        """Return the password for the given username for the realm.
        
        Used for digest authentication.
        """
        return self.userMap.get(realmname, {}).get(username, {}).get("password")
      
    
    def authDomainUser(self, realmname, username, password, environ):
        """Returns True if this username/password pair is valid for the realm, 
        False otherwise. Used for basic authentication."""
        user = self.userMap.get(realmname, {}).get(username)
        return user is not None and password == user.get("password")
