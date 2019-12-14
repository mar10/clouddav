# -*- coding: iso-8859-1 -*-

# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

import webapp2
import jinja2
from google.appengine.api import users, memcache
from google.appengine.ext.db import stats
from btfs.model import Path, Dir, File, Chunk
from pprint import pformat
import os
import logging


JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def db_get_count(model, limit=1000):
    return model.all(keys_only=True).count(limit)


def db_get_stats(model, limit=1000):
    stats = {
        'kind': model.kind(),
        'properties': model.properties(),
        'count': db_get_count(model, limit)
    }
    for name in stats['properties']:
        proptype = type(stats['properties'][name]).__name__
        stats['properties'][name] = proptype.replace('google.appengine.ext.', '')
    if stats['count'] == limit:
        stats['count'] = str(limit) + '+'
    return stats


class AdminHandler(webapp2.RequestHandler):

    #@login_required
    def get(self):
        if not users.is_current_user_admin():
            self.response.out.write(
                "You need to login as administrator <a href='%s'>Login</a>" %
                    users.create_login_url(self.request.uri)
            )
            return
        qs = os.environ.get("QUERY_STRING", "")
        logging.warning("AdminHandler.get: %s" % qs)
        # Handle admin commands 
        if qs == "run_tests":
            from btfs.test import test
            test()
            self.response.out.write("Tests run! <a href='?'>Back</a>")
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
            try:
                fs.rmtree("/")
            except Exception as e:
                logging.warning(e)
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
        for k, v in list(os.environ.items()):
            env.append("%s: '%s'" % (k, v))
        datastore_stats = {}
        datastore_stats['Stats'] = stats.GlobalStat.all().fetch(1)
        #datastore_stats['Stats'] = []
        #for stat in stats.KindPropertyNamePropertyTypeStat.all():
        #    datastore_stats['Stats'].append(stat)
        datastore_stats['Path'] = db_get_stats(Path)
        datastore_stats['Dir'] = db_get_stats(Dir)
        datastore_stats['File'] = db_get_stats(File)
        datastore_stats['Chunk'] = db_get_stats(Chunk)
        paths = []
        for item in Path.all().fetch(10):
            paths.append(item._entity)
        chunks = []
        for item in Chunk.all().fetch(10):
            info = item._entity
            if len(info['data']) > 100:
                info['data'] = '%s... (%s bytes)' % (info['data'][:100], len(info['data']))
            chunks.append(info)
        template_values = {
            "nickname": user.nickname(),
            "url": url,
            "url_linktext": url_linktext,
            "memcache_stats": pformat(memcache.get_stats()),
            "datastore_stats": pformat(datastore_stats),
            "path_samples": pformat(paths),
            "chunk_samples": pformat(chunks),
            "environment_dump": "\n".join(env),
            }
    
        template = JINJA_ENV.get_template('admin.html')
        self.response.out.write(template.render(template_values))
        return 
  

app = webapp2.WSGIApplication([("/_admin", AdminHandler)],
                              debug=True)

def main():
    logging.info("admin_handler.__main__")
    logging.getLogger().setLevel(logging.DEBUG)
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(app)

if __name__ == "__main__":
    main()
