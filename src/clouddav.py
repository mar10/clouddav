# -*- coding: iso-8859-1 -*-

# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

import logging 
from wsgidav.wsgidav_app import WsgiDAVApp, DEFAULT_CONFIG
#from wsgidav.samples.virtual_dav_provider import VirtualResourceProvider
from btfs.btfs_dav_provider import BTFSResourceProvider
from btfs.memcache_lock_storage import LockStorageMemcache
#from wsgidav.version import __version__

from google.appengine.ext.webapp.util import run_wsgi_app

def real_main():
    logging.info("real_main")
#    provider = VirtualResourceProvider()
    provider = BTFSResourceProvider()
    lockstorage = LockStorageMemcache()

    config = DEFAULT_CONFIG.copy()
    config.update({
        "provider_mapping": {"/": provider},
        "user_mapping": {},
        "verbose": 2,
        "enable_loggers": [],
        "propsmanager": False,      # True: use property_manager.PropertyManager                    
        "locksmanager": lockstorage,      # True: use lock_storage.LockStorageDict                   
        "domaincontroller": None,  # None: domain_controller.WsgiDAVDomainController(user_mapping)
        })
    app = WsgiDAVApp(config)
    run_wsgi_app(app)


def profile_main():
    # This is the main function for profiling 
    # We've renamed our original main() above to real_main()
    import cProfile, pstats, StringIO
    prof = cProfile.Profile()
    prof = prof.runctx("real_main()", globals(), locals())
    stream = StringIO.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    stats.sort_stats("time")  # Or cumulative
    stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    logging.info("Profile data:\n%s", stream.getvalue())


#===============================================================================
# main()
# http://code.google.com/intl/en/appengine/docs/python/runtime.html#App_Caching
# "App caching provides a significant benefit in response time. 
#  We recommend that all applications use a main() routine, ..."
#===============================================================================
main = profile_main



if __name__ == "__main__":
    logging.info("__main__")
    logging.getLogger().setLevel(logging.DEBUG)
    main()
