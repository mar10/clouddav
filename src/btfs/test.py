# -*- coding: iso-8859-1 -*-

# (c) 2010 Martin Wendt; see CloudDAV http://clouddav.googlecode.com/
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

"""
Implementation of a WsgiDAV provider that implements a virtual filesystem based
on Googles Big Table. 

"""
import logging
from btfs.btfs_dav_provider import BTFSResourceProvider
from btfs import fs

def test():
    logging.info("test.test()")
    
    logging.getLogger().setLevel(logging.DEBUG)

    # Test fs.py
    if fs.exists("/"):
        logging.info("removing /")
        fs.rmtree("/")
    logging.debug("#20")
    assert not fs.exists("/")
    logging.debug("#21")
    fs.initfs()
    logging.debug("#22")
    
    assert fs.isdir("/")
    logging.debug("#23")
    d = fs.getdir("/")
    d1 = fs.mkdir("/dir1")
    assert fs.isdir("/dir1")
    f1 = fs.btopen("/dir1/file1.txt", "w")
    f1.write("file content")
    f1.close()
    assert fs.isfile("/dir1/file1.txt")
    fs.unlink("/dir1/file1.txt")
    assert not fs.isfile("/dir1/file1.txt")

    print "*** fs tests passed ***"
  
    # Test providers 
    provider = BTFSResourceProvider()
    environ = {}
    
    resRoot = provider.getResourceInst("/", environ)
    resRoot.createCollection("folder1")
    assert fs.isdir("/folder1")
    assert not fs.isfile("/folder1")
    resChild = provider.getResourceInst("/folder1", environ)
    assert resChild 
    resFile = resChild.createEmptyResource("file_empty.txt")
    assert resFile 
    assert not fs.isdir("/folder1/file_empty.txt")
    assert fs.isfile("/folder1/file_empty.txt")
    # write
    data = "x" * 1024 
    res = resChild.createEmptyResource("file2.txt")
    f = res.beginWrite()
    f.write(data)
    f.close()
    # copy
    res = provider.getResourceInst("/folder1/file2.txt", environ)
    res.copyMoveSingle("/folder1/file2_copy.txt", False)

    res = provider.getResourceInst("/folder1/file2_copy.txt", environ)
    f = res.getContent()
    assert data == f.read()
    f.close()
    
    print "*** provider tests passed ***"



def profile_test():
    # This is the main function for profiling 
    import cProfile, pstats, StringIO
    prof = cProfile.Profile()
    prof = prof.runctx("test()", globals(), locals())
    stream = StringIO.StringIO()
    stats = pstats.Stats(prof, stream=stream)
#    stats.sort_stats("time")  # Or cumulative
    stats.sort_stats("cumulative")  # Or time
    stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    logging.info("Profile data:\n%s", stream.getvalue())
    print "*** See log for profiling info ***"


if __name__ == "__main__":
#    test()    
    profile_test()
