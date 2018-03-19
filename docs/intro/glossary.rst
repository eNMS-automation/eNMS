:orphan:

.. _glossary:

Glossary
========

.. glossary::
   :sorted:

   acl
      Access Control List - you can use it to specify who may do what in
      your wiki.

   contenttype
      A formal, standardized way of specifying of which type some data is.
      E.g. 'text/plain;charset=utf-8' is the contenttype for some simple piece
      of text (encoded using utf-8 encoding), 'image/png' is the contenttype
      for a PNG image.

   item
      A generic, revisioned object stored in your wiki storage.

   revision
      Part of an item's history, has metadata and data created for this item
      at some specific time in its history. If you create an item, you create
      its first revision. If you edit it and save, you create its next
      revision.

   data
      Just the raw data, no more, no less; can be some text, an image, a pdf.

   metadata
      Additional information related to or about some data. For example, if
      you create a new PDF item revision, the revision data will be the PDF
      file's content, but moin will also additionally store revision metadata
      that tells that this revision is in fact a PDF (its contenttype - we do not
      rely on or require .pdf extension on the item name), when it was saved,
      maybe some comment you gave when saving, etc.

   session
      As the protocol (http) used by a web browser is stateless, a means
      to keep state is needed. This is usually done by using a cookie stored
      within the user's browser. It is used for example to stay logged-in into your
      user account or store the trail of items you visited and for easier
      navigation.

   wiki engine
      Software used to run a wiki site.

   wiki farm
      Running multiple wikis together on one server. Often, there is some
      shared, common configuration inherited by all wikis, so each
      individual wiki's configuration becomes rather small.

   wiki instance
      All configuration and data related to a single wiki.

   wiki item
      A single content item within a wiki site.

   wiki page
      A single content item within a wiki site, possibly used for text-like items.

   wiki site
      A web site implemented using a wiki engine.

   WSGI
      Web Server Gateway Interface. It is a specification about how web servers,
      like e.g. Apache with mod_wsgi, communicate with web applications, like
      MoinMoin. It is a Python standard, described in detail in PEP 333.

   emeraldtree
      An XML / tree processing library used by moin.

   flask
      A micro framework used by moin.

   jinja
      A templating engine used by moin.

   sqlalchemy
      An SQL database abstraction library used by moin.

   sqlite
      An easy-to-use SQL database used by moin.

   werkzeug
      A WSGI library used by moin.
