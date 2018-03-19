===============================
ReST (ReStructured Text) Markup
===============================

..
 This document is duplicated within Moin2 as `/docs/user/rest.rst` and
 `contrib/sample/rst.data`. Please update both.

Depending upon your source, this document may have been created by
the Moin2 ReST parser (Docutils) or the Sphinx ReST parser. These parsers
have slight differences in the rendering of ReST markup, some of those differences
are noted below.

The purpose of this document is to define the features of the Moin2 ReST (Docutils)
parser. The Sphinx extensions to ReST markup that are not supported
by the Docutils parser are not included here.

See the the Docutils Restructured Text documentation for more information.

Headings
========

Rather than imposing a fixed number and order of section title adornment styles,
the order enforced will be the order as encountered.
The first style encountered will be an outermost title (like HTML H1), the
second style will be a subtitle, the third will be a subsubtitle, and so on.

The underline below the title must at least be equal to the length of the title itself.
Failure to comply results in messages on the server log. Skipping a heading
(e.g. putting an H5 heading directly under an H3) results in a rendering error and an
error message will be displayed instead of the expected page.

If any markup appears before the first heading on a page, then the first heading
will be an H2 and all subsequent headings will be demoted by 1 level.

**Markup**::

 =======
 Level 1
 =======

 Level 2
 =======

 # levels 1 and 2 are not shown below, see top of page and this section heading.

 Level 3
 -------

 Level 4
 *******

 Level 5
 :::::::

 Level 6
 +++++++


**Result**:


Level 3
-------

Level 4
*******

Level 5
:::::::

Level 6
+++++++


Table of Contents
=================

**Markup**::

    .. contents::

**Result**:

.. contents::

The table of contents may appear above or floated to the right side due to CSS styling.


Text formatting
===============

The following is a table of inline markup that can be used to format text in Moin.

+----------------------------------------+------------------------------------+
|Markup                                  |Result                              |
+========================================+====================================+
|``**Bold Text**``                       |**Bold text**                       |
+----------------------------------------+------------------------------------+
|``*Italic*``                            |*Italic*                            |
+----------------------------------------+------------------------------------+
|````Inline Literals````                 |``Inline Literals``                 |
+----------------------------------------+------------------------------------+
|``***nested markup is not supported***``|***nested markup is not supported***|
+----------------------------------------+------------------------------------+

Hyperlinks
==========

External Links
--------------

+----------------------------------------------------------------+------------------------------------------------------------+
|Markup                                                          |Result                                                      |
+================================================================+============================================================+
|``http://www.python.org/``                                      |http://www.python.org/                                      |
+----------------------------------------------------------------+------------------------------------------------------------+
|``External hyperlinks, like `Python <http://www.python.org/>`_``|External hyperlinks, like `Python <http://www.python.org/>`_|
+----------------------------------------------------------------+------------------------------------------------------------+
|``External hyperlinks, like Moin_.``                            |External hyperlinks, like Moin_.                            |
|                                                                |                                                            |
|``.. _Moin: http://moinmo.in/``                                 |.. _Moin: http://moinmo.in/                                 |
+----------------------------------------------------------------+------------------------------------------------------------+

Internal Links
--------------

.. _myanchor:

+----------------------------------------------------------------+------------------------------------------------------------+
|Markup                                                          |Result                                                      |
+================================================================+============================================================+
|``http:Home`` link to a page in this wiki                       |http:Home link to a page in this wiki                       |
+----------------------------------------------------------------+------------------------------------------------------------+
|```Home <http:Home>`_`` link to a page in this wiki             |`Home <http:Home>`_ link to a page in this wiki             |
+----------------------------------------------------------------+------------------------------------------------------------+
|``Headings_`` link to heading anchor on this page               |Headings_ link to heading anchor on this page               |
+----------------------------------------------------------------+------------------------------------------------------------+
|```Internal Links`_`` link to heading with embedded blanks      |`Internal Links`_ link to heading with embedded blanks      |
+----------------------------------------------------------------+------------------------------------------------------------+
|``.. _myanchor:`` create anchor, real anchor is above this table|create anchor, real anchor is above this table              |
+----------------------------------------------------------------+------------------------------------------------------------+
|``myanchor_`` link to above anchor                              |myanchor_ link to above anchor                              |
+----------------------------------------------------------------+------------------------------------------------------------+

**Notes:**
 - If this page was created by Sphinx, none of the above internal link examples work correctly.
 - The ".. _myanchor:" directive must begin in column one.
 - Section titles (or headings) automatically generate hyperlink targets (the title
   text is used as the hyperlink name).

Images
======

Images may be positioned by using the align parameter with a value of left, center, or right.
There is no facility to embed an image within a paragraph. There must be a blank line before
and after the image declaration. Images are not enclosed within a block level element so
several images declared successively without any positioning will display in a horizontal row.

**Markup**::

    Before text.

    .. image:: png
       :height: 100
       :width: 200
       :scale: 50
       :alt: alternate text png
       :align: center

    After text.

**Result**:

Before text.

.. image:: png
   :height: 100
   :width: 200
   :scale: 50
   :alt: alternate text png
   :align: center

After text.

**Notes:**
 - The Sphinx parser does not have an image named "png" so the alternate text
   will be displayed.

Figures
=======

Figures display graphics like images, but have the added feature of supporting captions
and explanatory text. Figures are block elements, so figures declared successively
will display in a column.

**Markup**::

    Before text.

    .. figure:: png
       :height: 100
       :width: 200
       :scale: 50
       :alt: alternate text png

       Moin Logo

       This logo replaced the "MoinMoin Man"
       logo long ago.

    After text.

**Result**:

Before text.

.. figure:: png
   :height: 100
   :width: 200
   :scale: 50
   :alt: alternate text png

   Moin Logo

   This logo replaced the "MoinMoin Man"
   logo long ago.

After text.

**Notes:**
 - The Sphinx parser does not have an image named "png" so the alternate text
   will be displayed.
 - The Sphinx parser does not support figures so the caption and explanatory text
   will not display correctly.

Blockquotes and Indentations
============================

To create a blockquote, indent all lines of a paragraph or paragraphs with an
equal number of spaces. To add an attribution, begin the last indented paragraph
with "-- ".

**Markup**::

 Text introducing a blockquote:

  If you chase two rabbits, you will lose them both.

**Result**:

Text introducing a blockquote:

  If you chase two rabbits, you will lose them both.

**Markup**::

  This is an ordinary paragraph, introducing a block quote.

    "It is my business to know things.  That is my trade."

    -- Sherlock Holmes

**Result**:

This is an ordinary paragraph, introducing a block quote.

    "It is my business to know things.  That is my trade."

    -- Sherlock Holmes

Lists
=====

Unordered Lists
---------------

**Markup**::

 - item 1
 - item 2

   - item 2.1
   - item 2.2

     - item 2.2.1
     - item 2.2.2

 - item 3

**Result**:

- item 1
- item 2

  - item 2.1
  - item 2.2

    - item 2.2.1
    - item 2.2.2

- item 3

Ordered Lists
---------------

**Markup**::

 1. item 1
 #. item 2

    (A) item 2.1
    (#) item 2.2

        i) item 2.2.1
        #) item 2.2.2

 #. item 3

**Result**:

 1. item 1
 #. item 2

    (A) item 2.1
    (#) item 2.2

        i) item 2.2.1
        #) item 2.2.2

 #. item 3

**Notes**:
 - Ordered lists can be automatically enumerated using the ``#`` character as
   demonstrated above. Note that the first item of an ordered list
   auto-enumerated in this fashion must use explicit numbering notation
   (e.g. ``1.``) in order to select the enumeration sequence type
   (e.g. Roman numerals, Arabic numerals, etc.), initial number
   (for lists which do not start at "1") and formatting type
   (e.g. ``1.`` or ``(1)`` or ``1)``). More information on
   enumerated lists can be found in the `reStructuredText documentation
   <http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#enumerated-lists>`_.
 - One or more blank lines are required before and after reStructuredText lists.
 - The Moin2 parser requires a blank line between items when changing indentation levels.
 - Formatting types (A) and i) are rendered as A. and A. by Sphinx and as A. and i. by Moin2.

Definition Lists
================

Definition lists are formed by an unindented one line term followed by an indented definition.

**Markup**::

 term 1
  Definition 1.

 term 2 : classifier
  Definition 2.

 term 3 : classifier one : classifier two
  Definition 3.

**Result**:

term 1
 Definition 1.

term 2 : classifier
 Definition 2.

term 3 : classifier one : classifier two
 Definition 3.

Field Lists
===========

Field lists are part of an extension syntax for directives usually intended for further processing.

**Markup**::

    :Date: 2001-08-16
    :Version: 1
    :Authors: Joe Doe

**Result**:

:Date: 2001-08-16
:Version: 1
:Authors: Joe Doe

Option lists
============

Option lists are intended to document Unix or DOS command line options.

**Markup**::

    -a      command definition
    --a     another command definition
    /S      dos command definition

**Result**:

-a      command definition
--a     another command definition
/S      dos command definition

Transitions
===========

Transitions, or horizontal rules, separate other body elements. A transition should
not begin or end a section or document, nor should two transitions be immediately
adjacent. The syntax for a transition marker is a horizontal line of 4 or more
repeated punctuation characters. The syntax is the same as section title
underlines without title text. Transition markers require blank lines before and after.

**Markup**::

    Text

    ----

    Text


**Result**:

Text

----

Text

Backslash Escapes
=================

Sometimes there is a need to use special characters as literal characters,
but ReST's syntax gets in the way. Use the backslash character as an escape.

**Markup**::

    *hot*

    333. is a float, 333 is an integer.

    \*hot\*

    333\. is a float, 333 is an integer.

**Result**:

*hot*

333. is a float, 333 is an integer.

\*hot\*

333\. is a float, 333 is an integer.

**Notes**:
 - The Moin2 ReST parser changes the 333. to a 1. and inserts an error message into the document.
 - The Sphinx ReST parser begins an ordered list with 333. The visual effect is a dedented line.

Tables
======

Simple Tables
-------------

Easy markup for tables consisting of two rows. This syntax can have no more than two rows.

**Markup**::

 ======= ======= =======
  A       B       C
 ======= ======= =======
  1       2       3
 ======= ======= =======

**Result**:

 ======= ======= =======
  A       B       C
 ======= ======= =======
  1       2       3
 ======= ======= =======


**Markup**::

 ======= ======= =======
       foo         Bar
 --------------- -------
  A       B       C
 ======= ======= =======
  1       2       3
 ======= ======= =======

**Result**:

 ======= ======= =======
       foo         Bar
 --------------- -------
  A       B       C
 ======= ======= =======
  1       2       3
 ======= ======= =======

Grid Tables
-----------

Complex tables can have any number of rows or columns. They are made by ``|``, ``+``, ``-`` and ``=``.

**Markup**::

 +----------------+---------------+
 | A              |               |
 +----------------+ D             |
 | B              |               |
 +================+===============+
 | C                              |
 +--------------------------------+

**Result**:

 +----------------+---------------+
 | A              |               |
 +----------------+ D             |
 | B              |               |
 +================+===============+
 | C                              |
 +--------------------------------+

One difference between the Sphinx and Moin ReST parsers is demonstrated below.
With the Spinx parser, grid table column widths can be expanded by adding spaces.

**Markup**::

 +---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
 | minimal width | maximal width (will take the maximum screen space)                                                                                                           |
 +---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Result**:

 +---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
 | minimal width | maximal width (will take the maximum screen space)                                                                                                           |
 +---------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Notes:**
 - The Moin2 ReST parser does not add the <colgroup><col width="9%"><col width="91%">
   HTML markup added by the Sphinx parser (the width attribute generates an HTML
   validation error), nor does it use Javascript to adjust the width of tables.
 - Under Moin2, tables and table cells will be of minimal width
   (unless there is CSS styling to set tables larger).

Admonitions
===========

Admonitions are used to draw the reader's attention to an important paragraph.
There are nine admonition types: attention, caution, danger, error, hint,
important, note, tip, and warning.

The ReST parser uses "error" admonitions to highlight some ReST syntax errors.

**Markup**::

    .. caution:: Be careful!
    .. danger:: Watch out!
    .. note:: Phone home.


**Result**:

.. caution:: Be careful!
.. danger:: Watch out!
.. note:: Phone home.

Comments
========

Comments are not shown on the page. Some parsers may create HTML comments
(``<!-- -->``). The Sphinx parser suppresses comments in the HTML output.
Within the Moin2 wiki, comments may be made visible/invisible by clicking the
Comments link within item views.

**Markup**::

 .. This is a comment
 ..
  _so: is this!
 ..
  [and] this!
 ..
  this:: too!
 ..
  |even| this:: !

**Result**:

 .. This is a comment
 ..
  _so: is this!
 ..
  [and] this!
 ..
  this:: too!
 ..
  |even| this:: !

Literal Blocks
==============

Literal blocks are used to show text as-it-is. i.e no markup processing is done within a literal block.
A minimum (1) indentation is required for the text block to be recognized as a literal block.

**Markup**::

 Paragraph with a space before two colons ::

  Literal block

 Paragraph with no space before two colons::

  Literal block

**Result**:

 Paragraph with a space between preceding two colons ::

  Literal block

 Paragraph with no space between text and two colons::

  Literal block

Line Blocks
===========

.. Copied from http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#line-blocks

Line blocks are useful for address blocks, verse (poetry, song lyrics), and
unadorned lists, where the structure of lines is significant. Line blocks
are groups of lines beginning with vertical bar ("|") prefixes. Each vertical
bar prefix indicates a new line, so line breaks are preserved. Initial
indents are also significant, resulting in a nested structure. Inline markup
is supported. Continuation lines are wrapped portions of long lines; they
begin with a space in place of the vertical bar. The left edge of a
continuation line must be indented, but need not be aligned with the left
edge of the text above it. A line block ends with a blank line.

**Markup**::

 Take it away, Eric the Orchestra Leader!

    | A one, two, a one two three four
    |
    | Half a bee, philosophically,
    |     must, *ipso facto*, half not be.
    | But half the bee has got to be,
    |     *vis a vis* its entity.  D'you see?
    |
    | But can a bee be said to be
    |     or not to be an entire bee,
    |         when half the bee is not a bee,
    |             due to some ancient injury?
    |
    | Singing...

**Result**:

Take it away, Eric the Orchestra Leader!

    | A one, two, a one two three four
    |
    | Half a bee, philosophically,
    |     must, *ipso facto*, half not be.
    | But half the bee has got to be,
    |     *vis a vis* its entity.  D'you see?
    |
    | But can a bee be said to be
    |     or not to be an entire bee,
    |         when half the bee is not a bee,
    |             due to some ancient injury?
    |
    | Singing...
