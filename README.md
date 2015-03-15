# clouddav
Automatically exported from code.google.com/p/clouddav

> CloudDAV is a WebDAV application that implements a virtual file system built on Google App Engine's data store ('Big Table').

The implementation is based on [WsgiDAV](http://code.google.com/p/wsgidav/) and 
also uses some code from the currently inactive [gaedav](http://code.google.com/p/gaedav/) project.

### Status

  * This is still alpha. Do *not* use this in a production environment, or you may loose data!
  * There is currently no support for dead properties
  * Google seems to not _officially_ support HTTP methods that are specific to WebDAV (such as PROPFIND). So Google may decide to drop this feature at any time!
  * *Note:* I had to [migrate to the new HRD format](https://developers.google.com/appengine/docs/adminconsole/migration) in August 2012, so sample content was reset.


### Example

A running sample instance is available here:
  http://clouddav-test-hrd.appspot.com/

You can open it in the browser or connect with a WebDAV client. Example (Windows):
```
>net use x: http://clouddav-test-hrd.appspot.com/ 
>dir x:
```

See here for some [details on Windows clients](http://docs.wsgidav.googlecode.com/hg/html/run-access.html#windows-clients).


### Usage
6 steps to your free 1 GB cloud drive:

  1. [https://appengine.google.com/ Sign up] for an account on [http://code.google.com/appengine/ Google App Engine].
  1. Download the [http://code.google.com/appengine/downloads.html#Google_App_Engine_SDK_for_Python GAE SDK]
  1. Download the [http://code.google.com/p/clouddav/source/checkout CloudDAV source].
  1. Rename and edit [http://code.google.com/p/clouddav/source/browse/src/app.yaml.template app.yaml.template] that comes with the project.
  1. [http://code.google.com/appengine/docs/python/gettingstarted/uploading.html Deploy the project] to GAE.
  1. Configure the authorized users in the CloudDAV User Administration page ([http://wiki.clouddav.googlecode.com/hg/img/clouddav_useradmin.png screenshot]).

*Note:* Since Google seems to not _officially_ support HTTP methods that are specific to WebDAV, 
such as PROPFIND, you cannot test it, when running inside the Local App Server and 
Google App Engine Launcher. (It currently works when deployed to GAE though.)
