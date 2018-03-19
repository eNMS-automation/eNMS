=============================
Markups Supported by MoinMoin
=============================

.. toctree::
   :maxdepth: 1

   moinwiki
   creolewiki
   rest
   docbook
   mediawiki
   markdown

.. _MoinWiki: https://moinmo.in/HelpOnMoinWikiSyntax
.. _WikiCreole: http://www.wikicreole.org/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Docbook: http://www.docbook.org/
.. _MediaWiki: http://www.mediawiki.org/wiki/Help:Formatting
.. _Markdown: http://daringfireball.net/projects/markdown/syntax

In Moin2, you specify the item's markup language when you create the document.
Its markup language can also be changed at any time by modifying the item's ``contenttype`` metadata.
Currently Moin2 supports `MoinWiki`_, `WikiCreole`_, `reStructuredText`_, `Docbook`_,
`MediaWiki`_ and `Markdown`_ markups.

**MOINTODO**: Currently the use of ``{{{#!syntax content}}}`` parsers crashes moin.
This should be looked into.

**MOINTODO**: The creation of items/editing of an item's metadata is not yet documented.
This is beyond the scope of this index page and should be looked into.
