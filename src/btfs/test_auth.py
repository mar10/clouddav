# -*- coding: iso-8859-1 -*-

# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

"""
"""
from __future__ import print_function
from __future__ import absolute_import
import logging


def test_auth():
#    from google.appengine.tools.appengine_rpc import AbstractRpcServer
    
    
    
    from google.appengine.api import users
    from .google_domain_controller import xAppAuth
    
#    auth = xAppAuth("moogle@wwwendt.de", "test", "clouddav")
#    print auth.getAuthtoken()

    user = users.get_current_user()
    print(user) 

    auth = xAppAuth("moogle@wwwendt.de", "mc.martin", "clouddav-mar10")
    print(auth.getAuthtoken())
    user = users.get_current_user()
    print(user) 

    return

#    import os
#    import urllib
#    import urllib2
#    import cookielib
#    
#    users_email_address = "XXXXXmoogle@wwwendt.de"
#    users_password      = "xxx"
#    
##    target_authenticated_google_app_engine_uri = "http://mylovelyapp.appspot.com/mylovelypage"
##    my_app_name = "yay-1.0"
#    target_authenticated_google_app_engine_uri = "http://clouddav-mar10.appspot.com/"
#    my_app_name = "clouddav-mar10"
#    
#    # we use a cookie to authenticate with Google App Engine
#    #  by registering a cookie handler here, this will automatically store the
#    #  cookie returned when we use urllib2 to open http://mylovelyapp.appspot.com/_ah/login
#    cookiejar = cookielib.LWPCookieJar()
#    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
#    urllib2.install_opener(opener)
#    
#    #
#    # get an AuthToken from Google accounts
#    #
#    auth_uri = "https://www.google.com/accounts/ClientLogin"
#    authreq_data = urllib.urlencode({ "Email":   users_email_address,
#                                      "Passwd":  users_password,
#                                      "service": "ah",
#                                      "source":  my_app_name,
#                                      "accountType": "HOSTED_OR_GOOGLE" })
#    auth_req = urllib2.Request(auth_uri, data=authreq_data)
#    try:
#        auth_resp = urllib2.urlopen(auth_req)
#    except urllib2.HTTPError, e:
#        if e.code == 403:  
#            # '403 Forbidden': unknown user or wrong password
#            print e
#            pass
#        raise e
#    auth_resp_body = auth_resp.read()
#    # auth response includes several fields - we're interested in
#    #  the bit after Auth=
#    auth_resp_dict = dict(x.split("=")
#                          for x in auth_resp_body.split("\n") if x)
#    authtoken = auth_resp_dict["Auth"]
#    
#    #
#    # get a cookie
#    #
#    #  the call to request a cookie will also automatically redirect us to the page
#    #   that we want to go to
#    #  the cookie jar will automatically provide the cookie when we reach the
#    #   redirected location
#    
#    # this is where I actually want to go to
#    serv_uri = target_authenticated_google_app_engine_uri
#    
#    serv_args = {}
#    serv_args['continue'] = serv_uri
#    serv_args['auth']     = authtoken
#    
#    full_serv_uri = "http://mylovelyapp.appspot.com/_ah/login?%s" % (urllib.urlencode(serv_args))
#    
#    serv_req = urllib2.Request(full_serv_uri)
#    serv_resp = urllib2.urlopen(serv_req)
#    serv_resp_body = serv_resp.read()
#    
#    # serv_resp_body should contain the contents of the
#    #  target_authenticated_google_app_engine_uri page - as we will have been
#    #  redirected to that page automatically
#    #
#    # to prove this, I'm just gonna print it out
#    print serv_resp_body
    
    
def profile_test():
    # This is the main function for profiling 
    import cProfile, pstats, StringIO
    prof = cProfile.Profile()
    prof = prof.runctx("test_auth()", globals(), locals())
    stream = StringIO.StringIO()
    stats = pstats.Stats(prof, stream=stream)
#    stats.sort_stats("time")  # Or cumulative
    stats.sort_stats("cumulative")  # Or time
    stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    logging.info("Profile data:\n%s", stream.getvalue())
    print("*** See log for profiling info ***")


if __name__ == "__main__":
    profile_test()
