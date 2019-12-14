# -*- coding: iso-8859-1 -*-
# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
Implementation of a WsgiDAV provider that implements a virtual file system based
on Googles datastore (Bigtable). 
"""
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from btfs.memcache_lock_storage import LockStorageMemcache
from wsgidav.lock_manager import LockManager, lock_string
import logging
from btfs.btfs_dav_provider import BTFSResourceProvider
from btfs import fs

def test():
    logging.info("test.test()")
    
    logging.getLogger().setLevel(logging.DEBUG)


    # Test fs.py
    fs.initfs()
    assert fs.isdir("/")

    rootpath = "/test"
    if fs.exists(rootpath):
        logging.info("removing "+rootpath)
        fs.rmtree(rootpath)
    assert not fs.exists(rootpath)
    
    fs.mkdir(rootpath)
    assert fs.isdir(rootpath)
    
    data = "file content"
    fs.mkdir(rootpath+"/dir1")
    assert fs.isdir(rootpath+"/dir1")
    f1 = fs.btopen(rootpath+"/dir1/file1.txt", "w")
    f1.write(data)
    f1.close()
    assert fs.isfile(rootpath+"/dir1/file1.txt")

    #fs.unlink(rootpath+"/dir1/file1.txt")
    #assert not fs.isfile(rootpath+"/dir1/file1.txt")

    print("*** fs tests passed ***")
  
    # Test providers 
    provider = BTFSResourceProvider()
    lockman = LockManager(LockStorageMemcache())
    provider.set_lock_manager(lockman)
    environ = {"wsgidav.provider": provider}
    
    resRoot = provider.get_resource_inst(rootpath+"/", environ)
    resRoot.create_collection("folder1")
    assert fs.isdir(rootpath+"/folder1")
    assert not fs.isfile(rootpath+"/folder1")
    resChild = provider.get_resource_inst(rootpath+"/folder1", environ)
    assert resChild 
    resFile = resChild.create_empty_resource("file_empty.txt")
    assert resFile 
    assert not fs.isdir(rootpath+"/folder1/file_empty.txt")
    assert fs.isfile(rootpath+"/folder1/file_empty.txt")
    # write
    data = "x" * 1024
    res = resChild.create_empty_resource("file2.txt")
    f = res.begin_write()
    f.write(data)
    f.close()
    # copy
    res = provider.get_resource_inst(rootpath+"/folder1/file2.txt", environ)
    res.copy_move_single(rootpath+"/folder1/file2_copy.txt", False)

    res = provider.get_resource_inst(rootpath+"/folder1/file2_copy.txt", environ)
    f = res.get_content()
    assert data == f.read()
    f.close()
    
    print("*** provider tests passed ***")
    
    lock = provider.lock_manager.acquire(rootpath+"/folder1",
                                        "write", "exclusive", "infinity", 
                                        "test_owner", timeout=100, 
                                        principal="martin", token_list=[])
    assert lock["root"] == rootpath+"/folder1"
    lock = provider.lock_manager.get_lock(lock["token"])
    print(lock_string(lock))
    assert lock["root"] == rootpath+"/folder1"

    locklist = provider.lock_manager.get_indirect_url_lock_list(rootpath+"/folder1/file2.txt")
    print(locklist)
    assert len(locklist) == 1
    
    print("*** lock tests passed ***")


def profile_test():
    # This is the main function for profiling 
    import cProfile, pstats, io
    prof = cProfile.Profile()
    prof = prof.runctx("test()", globals(), locals())
    stream = io.StringIO()
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
#    test()    
    profile_test()
