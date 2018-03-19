============
Requirements
============

MoinMoin requires Python 2.7.x. A CPython distribution is
recommended because it will likely be the fastest and most stable.
Most developers use a CPython distribution for testing.
Typical linux distributions will either have Python 2.7 installed by
default or will have a package manager that will install Python 2.7
as a secondary Python.
Windows users may download CPython distributions from  http://www.python.org/ or
http://www.activestate.com/.

An alternative implementation of Python, PyPy, is available
from http://pypy.org/.

The `virtualenv` Python package is also required. The
installation process for `virtualenv` varies with your OS and
Python distribution.
Many linux distributions have a package manager that may do
the installation. Windows users (and perhaps others) may download
setuptools from https://pypi.python.org/pypi/setuptools.
Once setuptools is installed, do "`easy_install virtualenv`".
Current ActiveState distributions include virtualenv in the installation bundle.
If all else fails, try Google.

Mercurial (hg) is required should you wish to contribute
patches to the moin2 development effort. Even if you do not
intend to contribute, Mercurial is highly recommended as it
will make it easy for you to obtain fixes and enhancements
from the moin2 repositories. Mercurial can be installed
with most linux package managers or downloaded
from http://mercurial.selenic.com/. As an alternative,
most Windows users will prefer to install TortoiseHG
(includes Mercurial) from http://tortoisehg.bitbucket.org/.


Servers
=======

For moin2, you can use any server compatible with WSGI:

* the builtin "./m run" or "moin" server is recommended for desktop wikis, testing,
  debugging, development, adhoc-wikis, etc.
* apache with mod_wsgi is recommended for bigger/busier wikis.
* other WSGI-compatible servers or middlewares are usable
* For cgi, fastcgi, scgi, ajp, etc., you can use the "flup" middleware:
  http://trac.saddi.com/flup
* IIS with ISAPI-WSGI gateway is also compatible: http://code.google.com/p/isapi-wsgi/

.. caution:: When using the built-in server for public wikis (not recommended), use
        "./m run -d -r" to turn off the werkzeug debugger and auto reloader. See Werkzeug
        docs for more information.


Dependencies
============

Dependent packages will be automatically downloaded and installed during the
moin2 installation process. For a list of dependencies, see setup.py.


Clients
=======
On the client side, you need:

* a web browser that supports W3C standards HTML 5, CSS 2.1, and JavaScript:

  - any current version of Firefox, Chrome, Opera, Safari, Maxthon, Internet Explorer (IE9 or newer).
  - use of older Internet Explorer versions is not recommended and not supported.

* a Java browser plugin is required only if you want to use the TWikiDraw or AnyWikiDraw drawing applets.
