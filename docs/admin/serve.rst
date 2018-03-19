==============
Server Options
==============

Built-in Web Server (easy)
==========================
aa

Running the built-in server
---------------------------
Run the moin built-in server as follows::

 # easiest for debugging (single-process, single-threaded server):
 ./m run  # Windows:  "m run"

 # or, if you need another configuration file, ip address, or port:
 ./m run --config /path/to/wikiconfig.py --host 1.2.3.4 --port 7777

While the moin server is starting up, you will see some log output, for example::

 bbbbbb

cccc

Stopping the built-in server
----------------------------
To stop the wiki server, either use `Ctrl-C` or close the window.


Using the built-in server for production
----------------------------------------

.. caution:: Using the built-in server for public wikis is not recommended. Should you
 wish to do so, turn off the werkzeug debugger and auto reloader by passing the
 -d and -r flags. The wikiconfig.py settings of `DEBUG = False` and `TESTING = False` are
 ignored by the built-in server. You must use the -d and -r flags.
 See Werkzeug docs for more information.::

 ./m run --host 0.0.0.0 --port 80 -d -r


External Web Server (advanced)
==============================

.. tip:: Check contents of /contrib/wsgi/ for sample wsgi files for your server.
