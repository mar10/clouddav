# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
Implementation of a domain controller that uses the Users Service of 
Google App Engine.

Credentials are verified by applying this rules:

1. If '*' is in the list of configured users allow anonymous access. 
2. If the current request was made by an authenticated user with 
   admin permissions for this GAE application: grant write access.
3. If the user name that is passed with the request is not configured in the 
   'User Administration' page of this CloudDAV application: deny access.
4. Use Google's ClientLogin API to verify the the password.
5. TODO: Grant read or read/write access, depending on user configuration. 

Example:  
    >net use M: https://myapp.appspot.com/ /user:user@gmail.com 
    >dir m:
  or pass a password  
    >net use M: https://myapp.appspot.com/ /user:user@gmail.com mypassword

  When using XP:
  - we cannot use https:// in the URL (but will be redirected)
  - we must connect to a sub-folder
    >net use M: http://myapp.appspot.com/dav /user:user@gmail.com
    

See http://code.google.com/appengine/docs/python/users/
    http://code.google.com/apis/accounts/docs/AuthForInstalledApps.html

See `Developers info`_ for more information about the WsgiDAV architecture.

.. _`Developers info`: http://docs.wsgidav.googlecode.com/hg/html/develop.html  
"""
import logging 
import sys
import urllib
import urllib2
import cookielib

from google.appengine.api import users 
from auth import AuthorizedUser, findAuthUser
__docformat__ = "reStructuredText"


#===============================================================================
# xAppAuth
#===============================================================================
class xAppAuth:
    """
    Author: Dale Lane; Modified by 'youngfe' on this page:
    http://dalelane.co.uk/blog/?p=303
    """
    def __init__(self, user, password, appName):
        self.user = user
        self.password = password
        self.appName = appName
        self.authtoken = None
        self.lastError = (None, None, None)
        # TODO: should be a lastAccess tag, so we can force a refresh after 1 hour or so

    def getAuthtoken(self, refresh=False):
        if self.authtoken is None or refresh:
            self.lastError = (None, None, None)
            cookiejar = cookielib.LWPCookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
            urllib2.install_opener(opener)
            auth_uri = "https://www.google.com/accounts/ClientLogin"
            authreq_data = urllib.urlencode({"Email": self.user,
                "Passwd": self.password,
                "service": "ah",
                "source": self.appName,
                "accountType": "HOSTED_OR_GOOGLE" })
            auth_req = urllib2.Request(auth_uri, data=authreq_data)
            try:
                auth_resp = urllib2.urlopen(auth_req)
            except urllib2.HTTPError, e:
                self.lastError = (e.code, e.msg, None)
                if e.code == 403:  
                    # '403 Forbidden': unknown user or wrong password
                    # We still can get error details from the response body
                    logging.error("HTTPError %s: %r, %r" % (e, e.message, e.strerror))
                    self.lastError = (e.code, e.msg, "%s/%s" % (e.message, e.strerror))
                raise e
            auth_resp_body = auth_resp.read()
            # auth response includes several fields - we're interested in
            # the bit after Auth=
            auth_resp_dict = dict(x.split("=")
                                  for x in auth_resp_body.split("\n") if x)
            self.authtoken = auth_resp_dict["Auth"]
        return self.authtoken
    
    def getAuthUrl(self, Uri, AppName):
        serv_uri = Uri
        serv_args = {}
        serv_args["continue"] = serv_uri
        serv_args["auth"] = self.getAuthtoken()
        return "http://" + AppName + ".appspot.com/_ah/login?%s" % (urllib.urlencode(serv_args))
    
    def getAuthRequest(self, Uri, AppName):
        return urllib2.Request(self.getAuthUrl(Uri, AppName))
    
    def getAuthResponse(self, Uri, AppName):
        return urllib2.urlopen(self.getAuthRequest(Uri, AppName))
    
    def getAuthRead(self, Uri, AppName):
        return self.getAuthResponse(Uri, AppName).read()


#===============================================================================
# GoogleDomainController
#===============================================================================
class GoogleDomainController(object):

    def __init__(self, userMap=None):
#        self.appName = appName
        self.userMap = userMap

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
        return realm
    
    def requireAuthentication(self, realmname, environ):
        """Return True if this realm requires authentication or False if it is 
        available for general access."""
        logging.debug("requireAuthentication(%r)" 
                      % (realmname, ))
        # If '*' is in the list of allowed accounts, allow anonymous access
        if findAuthUser("*"):
            logging.debug("Granting access to everyone (*)")
            return False
        return True
    
    def isRealmUser(self, realmname, username, environ):
        """Returns True if this username is valid for the realm, False otherwise.
        
        Used for digest authentication.
        """
        raise NotImplementedError("We cannot query users without knowing the password for a Google account. Digest authentication must be disabled.")
            
    def getRealmUserPassword(self, realmname, username, environ):
        """Return the password for the given username for the realm.
        
        Used for digest authentication.
        """
        raise NotImplementedError("We cannot query the password for a Google account. Digest authentication must be disabled.")
    
    def authDomainUser(self, realmname, username, password, environ):
        """Returns True if this username/password pair is valid for the realm, 
        False otherwise. 

        Used for basic authentication.
        """
        logging.debug("authDomainUser(%r, %r, %r)" 
                      % (realmname, username, "***"))
#        headers = [ "%s: %r" % e for e in environ.items() ]
#        logging.debug("headers:\n\t" + "\n\t".join(headers))

        # If current user is logged in to Google Apps and has 'admin'
        # permission, allow access  
        google_user = users.get_current_user()
        logging.debug("User %s is googleapp user %s" % (username, google_user))
        if users.is_current_user_admin():
            logging.debug("User %s is authorized as GAE admin %s for %s" 
                          % (username, google_user.nickname(), environ.get("APPLICATION_ID")))
            return True

        # Check if user name that was passed with the request is in the list 
        # of allowed accounts
        auth_user = findAuthUser(username)
        if not auth_user:
            logging.info("User %s is not configured to have access" 
                          % (username, ))
            return False
        logging.debug("User %s is configured (canWrite: %s)" 
                      % (username, auth_user.canWrite))

        # Check if user name / password that was passed with the request is a 
        # (globally) registered, valid account.
         
        # TODO: pass self.appName and check, if user has 'admin' permissions on <appName>
        # TODO: cache this info for at least 10 minutes
        user = xAppAuth(username, password, appName=environ.get("APPLICATION_ID"))
        try:
            authToken = user.getAuthtoken()
            logging.debug("User %s is authorized: %s" % (username, authToken))
        except urllib2.HTTPError, _:
            logging.info("User %s is not authorized: %s" % (username, user.lastError))
            authToken = None
        return bool(authToken) 
