=======
Indexes
=======

General
=======
MoinMoin relies strongly on indexes that accelerate access to item metadata and
data, and makes it possible to have simple backends, because the index layer
is doing all the hard and complex work.

Indexes are used internally for many operations like item lookup, history,
iterating over items, search, interactive search, etc.

MoinMoin won't be able to start with damaged, inaccessible or non-existing indexes.
As a result, you will need to configure and initialize indexing correctly first.

moin will automatically update the index when items are created, updated, deleted,
destroyed, or renamed via the storage api of moin, indexing layer or above.

Configuration
=============
Your need to have a ``index_storage`` entry in your wiki config.

We use whoosh for indexing and as whoosh supports multiple storage backends,
this entry is made to potentially support any storage supported by whoosh.

In general, this entry has the form of::

    index_storage = kind, (p1, p2, ...), {kw1=..., kw2=..., ...}

Currently, we only support the 'FileStorage' kind of index storage, which only
has one parameter - the index directory::

    index_storage = 'FileStorage', ("/path/to/moin-2.0/wiki/index", ), {}

**Notes for FileStorage:**

* The path MUST be absolute, writable and should be on a fast, local filesystem.
* Moin will use `index.temp` directory as well, if you build an index at
  the `temporary location`.


moin index script reference
===========================
You can use the ``moin index-*`` group of script commands to manage indexes.

Many of the script commands for index management support a `--tmp` option to use
the temporary index location. This is useful if you want to do index operations
in parallel to a running wiki which is still using the index at the normal
index location.

moin index-create
-----------------
Creates an empty but valid index.

**Note:** the moin WSGI application needs an index to successfully start up.
As the moin index-* script commands are also based on the moin WSGI application,
this can lead to a chicken and egg problem. To solve this, the moin command has
a ``-i`` (``--index-create``) option that will trigger index creation on startup.

Additionally, if the storage is also non-existent yet, one might also need
``-s`` (``--storage-create``) to create an empty storage on startup.

moin index-build
----------------
Process all revisions of the wiki and add the indexable documents to the index.

**Note:**

* For big wikis, this can take rather long; consider using --tmp.
* index-build does NOT clear the index at the beginning.
* index-build does not check the current contents of the index. Therefore you must not run
  index-build multiple times for the same data or the same wiki.

moin index-update
-----------------
Compare an index to the current storage contents and update the index as
needed (add, remove, update) to reflect the current storage contents.

**Note:** You can use this after building at the tmp location to get
the changes that happened to the wiki while building the index as well. You can run
index-update multiple times to keep even more caught up.

moin index-destroy
------------------
Destroy an index, such that nothing left at the respective location.

moin index-move
---------------
Move the index from the temporary location to the normal location.

moin index-optimize
-------------------
Optimize an index:: see Whoosh docs for more details.

moin index-dump
---------------
Output index contents in human readable form, e.g. for debugging purposes.

**Note:** only fields with attribute ``stored=True`` can be displayed.


Building an index for a single wiki
===================================

If your wiki is fresh and empty
-------------------------------
Use::

    moin index-create --storage-create --index-create
    moin index-create -s -i  # same, but shorter

Storage and index are now initialized and both empty.

If you add data to your wiki, the index will get updated automatically.


If your wiki has data and is shut down
--------------------------------------
If index needs a rebuild for some reason, e.g. index lost, index damaged,
incompatible upgrade, etc., use::

    moin index-create -i
    moin index-build  # can take a while...


If your wiki has data and should stay online
--------------------------------------------
Use::

     moin index-create -i --tmp
     moin index-build --tmp  # can take a while...
     moin index-update --tmp  # should be quicker, make sure we have 99.x%
     # better shut down the wiki now or at least make sure it is not changed
     moin index-update --tmp  # make sure we have indexed all content, should be even quicker.
     moin index-move  # instantaneously
     # start the wiki again or allow changes now again

**Note:** Indexing puts load onto your server, so if you like to do regular
index rebuilds, schedule them at some time when your server is not too busy.


Building an index for a wiki farm
=================================
If you run a wiki farm (multiple related wikis), you may share the index
between the wikis, so users will be able to search in one wiki
and also see results from the other wikis.

Before you start, you must prepare your wiki configs. For example, for a company
that uses two farm wikis, such as ``Sales`` and ``Engineering``, Their respective
wiki configs could look like:

``Sales``::

      interwikiname = u"Sales"
      index_storage = 'FileStorage', ("/path/to/moin-2.0/wiki/index", ), {}


``Engineering``::

      interwikiname = u"Engineering"
      index_storage = 'FileStorage', ("/path/to/moin-2.0/wiki/index", ), {}


Now do the initial index building::

     moin index-create -i  # create an empty index
     # now add the indexes from both other wikis:
     moin index-build  # with Sales wiki configuration
     moin index-build  # with Engineering wiki configuration

Now you should have a shared index for all wikis.

**Note:** Do not build indexes for multiple wikis in parallel. This is not
supported.
