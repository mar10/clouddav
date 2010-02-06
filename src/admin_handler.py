# -*- coding: iso-8859-1 -*-

# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import users, memcache
from google.appengine.ext.webapp import template
from pprint import pformat
import os
import logging

class AdminHandler(webapp.RequestHandler):

    @login_required
    def get(self):
        qs = os.environ.get("QUERY_STRING", "")
        logging.warning("AdminHandler.get: %s" % qs)
        # Handle admin commands 
        if qs == "run_tests":
            from btfs.test import test
            test()
            return
        elif qs == "clear_cache":
            logging.warning("clear_cache: memcache.flush_all()")
            memcache.flush_all()
            self.response.out.write("Memcache deleted! <a href='?'>Back</a>")
            return
        elif qs == "clear_datastore":
            logging.warning("clear_datastore: fs.rmtree('/')")
            from btfs import fs
            # cannot use rmtree("/"), because it prohibits '/'
            fs.rmtree("/") 
#            fs.getdir("/").delete(recursive=True)
            memcache.flush_all()
            fs.initfs()
            self.response.out.write("Removed '/'. <a href='?'>Back</a>")
            return
        elif qs != "":
            raise NotImplementedError("Invalid command: %s" % qs)
        # Show admin page
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        env = []
        for k, v in os.environ.items():
            env.append("%s: '%s'" % (k, v))
        template_values = {
            "nickname": user.nickname(),
            "url": url,
            "url_linktext": url_linktext,
            "memcache_stats": pformat(memcache.get_stats()),
            "environment_dump": "\n".join(env),
            }
    
        path = os.path.join(os.path.dirname(__file__), "admin.html")
        self.response.out.write(template.render(path, template_values))
        return 
  

application = webapp.WSGIApplication([("/_admin", AdminHandler),
#                                      ("/sign", Guestbook),
                                      ],
                                     debug=True)

def main():
    logging.info("admin_handler.__main__")
    logging.getLogger().setLevel(logging.DEBUG)
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
