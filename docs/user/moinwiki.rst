.. role:: underline
.. role:: strikethrough
.. role:: sup
.. role:: sub
.. role:: bolditalic
.. role:: smaller
.. role:: larger


==========================
Moin Wiki markup overview
==========================

The report follows the moin 1.9 help page and reports syntaxes that do not match 1.9 help syntax documentation.
The structure and order has been matched with other markup rst files namely creoleWiki.rst and mediaWiki.rst at http://hg.moinmo.in/moin/2.0-dev/file/42d8cde592fb/docs/user

Features currently not working with moin's Wiki parser are marked with **MOINTODO**.

Table Of Contents
=================

Table of contents:

``<<TableOfContents()>>``

Table of contents (up to 2nd level headings only):

``<<TableOfContents(2)>>``

Headings
========

**Markup**: ::

 = Level 1 =
 == Level 2 ==
 === Level 3 ===
 ==== Level 4 ====
 ===== Level 5 =====
 ====== Level 6 ======

**Result**:

Level 1
=======

**Intentionally not rendered as level 1 so as to not interfere with Sphinx's indexing**

Level 2
=======

Level 3
-------

Level 4
*******

Level 5
:::::::

Level 6
+++++++

**Notes**:
 - Closing equals signs are compulsory.
 - Also, whitespace between the first word of the heading and the opening equals sign will not be shown in the output (ie. leading whitespace is stripped).

Text formatting
===============

The following is a table of inline markup that can be used to control text formatting in Moin.

+-------------------------------------+---------------------------------------+
| Markup                              | Result                                |
+=====================================+=======================================+
| ``'''Bold Text'''``                 | **Bold text**                         |
+-------------------------------------+---------------------------------------+
| ``''Italic''``                      | *Italic*                              |
+-------------------------------------+---------------------------------------+
| ``'''''Bold Italic'''''``           | :bolditalic:`Bold Italic`             |
+-------------------------------------+---------------------------------------+
| ```Monospace```                     | ``Monospace``                         |
+-------------------------------------+---------------------------------------+
| ``{{{Code}}}``                      | ``Code``                              |
+-------------------------------------+---------------------------------------+
| ``__Underline__``                   | :underline:`Underline`                |
+-------------------------------------+---------------------------------------+
| ``^Super^Script``                   | :sup:`Super` Script                   |
+-------------------------------------+---------------------------------------+
| ``,,Sub,,Script``                   | :sub:`Sub` Script                     |
+-------------------------------------+---------------------------------------+
| ``~-Smaller-~``                     | :smaller:`Smaller`                    |
+-------------------------------------+---------------------------------------+
| ``~+Larger+~``                      | :larger:`Larger`                      |
+-------------------------------------+---------------------------------------+
| ``--(Stroke)--``                    | :strikethrough:`Stroke`               |
+-------------------------------------+---------------------------------------+

Hyperlinks
==========

Internal Links
--------------

+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| Markup                                    | Result                                      | Comments                                    |
+===========================================+=============================================+=============================================+
| ``[[ItemName]]``                          | `ItemName <ItemName>`_                      | Link to an item                             |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[ItemName|Named Item]]``               | `Named Item <ItemName>`_                    | Named link to an internal item              |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[#AnchorName]]``                       | `#AnchorName <#AnchorName>`_                | Link to an anchor in the current item       |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[#AnchorName|AnchorName]]``            | `AnchorName <#AnchorName>`_                 | Link to a named anchor                      |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[ItemName#AnchorName]]``               | `ItemName#AnchorName <ItemName#AnchorName>`_| Link to an anchor in an internal item       |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[ItemName#AnchorName|Named Item1]]``   | `Named Item1 <ItemName#AnchorName>`_        | Named link to an anchor in an internal item |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[../SiblingItem]]``                    | `../SiblingItem <../SiblingItem>`_          | Link to a sibling of the current item       |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[/SubItem]]``                          | `/SubItem </SubItem>`_                      | Link to a sub-item of current item          |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[Home/ItemName]]``                     | `Home/ItemName <Home/ItemName>`_            | Link to a subitem of Home item              |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+
| ``[[/filename.txt]]``                     | `/filename.txt </filename.txt>`_            | Link to a sub-item called Filename.txt      |
+-------------------------------------------+---------------------------------------------+---------------------------------------------+

External Links
--------------

+----------------------------------------------------------------+------------------------------------------------------------------------------+------------------------------------------+
| Markup                                                         | Result                                                                       | Comments                                 |
+================================================================+==============================================================================+==========================================+
| ``[[https://moinmo.in/]]``                                     | https://moinmo.in/                                                           | External link                            |
+----------------------------------------------------------------+------------------------------------------------------------------------------+------------------------------------------+
| ``[[https://moinmo.in/|MoinMoin Wiki]]``                       | `MoinMoin Wiki <https://moinmo.in/>`_                                        | Named External link                      |
+----------------------------------------------------------------+------------------------------------------------------------------------------+------------------------------------------+
| ``[[MeatBall:InterWiki]]``                                     | `MeatBall:InterWiki <http://www.usemod.com/cgi-bin/mb.pl?InterWiki>`_        | Link to an item on an external Wiki      |
+----------------------------------------------------------------+------------------------------------------------------------------------------+------------------------------------------+
| ``[[MeatBall:InterWiki|InterWiki page on MeatBall]]``          | `InterWiki page on MeatBall <http://www.usemod.com/cgi-bin/mb.pl?InterWiki>`_| Named link to an item on an external Wiki|
+----------------------------------------------------------------+------------------------------------------------------------------------------+------------------------------------------+
| ``[[mailto:user@example.com]]``                                | `mailto:user@example.com <mailto:user@example.com>`_                         | Mailto link                              |
+----------------------------------------------------------------+------------------------------------------------------------------------------+------------------------------------------+


Images and Transclusions
========================

+----------------------------------------------------+---------------------------------------+
| Markup                                             | Comment                               |
+====================================================+=======================================+
| ``{{example.png}}``                                | Embed example.png inline              |
+----------------------------------------------------+---------------------------------------+
| ``{{https://static.moinmo.in/logos/moinmoin.png}}``| Embed example.png inline              |
+----------------------------------------------------+---------------------------------------+
| ``{{ItemName}}``                                   | Transclude (embed the contents of)    |
|                                                    | ItemName inline.                      |
+----------------------------------------------------+---------------------------------------+
| ``{{/SubItem}}``                                   | Transclude SubItem inline.            |
+----------------------------------------------------+---------------------------------------+
| ``{{ example.jpg || width=20, height=100 }}``      | Resizes example.png by using HTML     |
|                                                    | tag attributes                        |
+----------------------------------------------------+---------------------------------------+
| ``{{ example.jpg || &w=20 }}``                     | Resizes example.png by using server-  |
|                                                    | side compression, PIL needs to be     |
|                                                    | installed.                            |
+----------------------------------------------------+---------------------------------------+
| ``{{ https://moinmo.in/ || width=800 }}``          | Resizes the ``object`` which is       |
|                                                    | embedded using HTML tags. Also markup |
|                                                    | involving '&' parameters like ``&w``  |
|                                                    | doesn't make much sense.              |
+----------------------------------------------------+---------------------------------------+

**Extra Info**:

Markup like ``{{ example.jpg || &w=20 }}``, simply adds ``&w`` to the ``src`` URL of the image, the Python Imaging Library (PIL)
understands that it has to compress the image on the server side and render as shrinked to size ``20``.

For markup like ``{{ example.jpg || width=20, height=100 }}`` we currently allow only the ``width`` and ``height`` (anything
else is ignored) to be added as attributes in the HTML, however one can, add anything to the query URL using ``&``, like ``&w`` in the example above.

Most browsers will display a large blank space when a web page using an https protocol is transcluded into a page using http protocol.
Transcluding a png image using an https protocol into an http protocol page displays OK in all browsers.


Blockquotes and Indentations
============================

**Markup**: ::

 indented text
  text indented to the 2nd level

**Result**:

 indented text
  text indented to the 2nd level


Lists
=====

.. warning::
   All Moin Wiki list syntax (including that for unordered lists, ordered lists and definition lists) requires a leading space before each item in the list.
   Unfortunately, reStructuredText does not allow leading whitespace in code samples, so the example markup here will not work if copied verbatim, and requires
   that each line of the list be indented by one space in order to be valid Moin Wiki markup.
   This is also an **RSTTODO**

Unordered Lists
---------------

**Markup**: ::

 * item 1
 * item 2 (preceding white space)
  * item 2.1
   * item 2.1.1
 * item 3
  . item 3.1 (bulletless)
 . item 4 (bulletless)
  * item 4.1
   . item 4.1.1 (bulletless)

**Result**:

 - item 1

 - item 2 (preceding white space)

  - item 2.1

   - item 2.1.1

 - item 3

  - item 3.1 (bulletless)

 - item 4 (bulletless)

  - item 4.1

   - item 4.1.1 (bulletless)

**Note**:
 - moin markup allows a square, white and a bulletless item for unordered lists, these cannot be chosen in rst

Ordered Lists
---------------

With Numbers
************

**Markup**: ::

 1. item 1
   1. item 1.1
   1. item 1.2
 1. item 2

**Result**:

 1. item 1

   1. item 1.1

   2. item 1.2

 2. item 2

With Roman Numbers
******************

**Markup**: ::

 I. item 1
   i. item 1.1
   i. item 1.2
 I. item 2

**Result**:

 I. item 1

   i. item 1.1

   ii. item 1.2

 II. item 2

With Letters
************

**Markup**: ::

 A. item 1
   a. item 1.1
   a. item 1.2
 A. item 2

**Result**:

 A. item 1

   a. item 1.1

   b. item 1.2

 B. item 2

Definition Lists
================

**Markup**: ::

 term:: definition
 object::
 :: description 1
 :: description 2

**Result**:

 term
  definition
 object
  | description 1
  | description 2

**Notes**:
 - reStructuredText does not support multiple definitions for a single term, so a line break has been forced to illustrate the appearance of several definitions.
   Using the prescribed Moin Wiki markup will, in fact, produce two separate definitions in MoinMoin (using separate ``<dd>`` tags).

Tables
======

Moin wiki markup supports table headers and footers. To indicate the first row(s) of a table is a header, insert a line of 3 or more = characters. To indicate a footer, include a second line of = characters after the body of the table.

**Markup**: ::

 ||Head A ||Head B ||Head C ||
 =============================
 ||a      ||b      ||c      ||
 ||x      ||y      ||z      ||

**Result**:

====== ====== ======
Head A Head B Head C
====== ====== ======
a      b      c
x      y      z
====== ====== ======

Table Styling
-------------

To add styling to a table, enclose one or more parameters within angle
brackets at the start of any table cell. Options for tables must be
within first cell of first row. Options for rows must be within first
cell of the row. Separate multiple options with a blank character.

================================== ===========================================================
Markup                             Effect
================================== ===========================================================
<tableclass="zebra moin-sortable"> Adds one or more CSS classes to the table
<rowclass="orange">                Adds one or more CSS classes to the row
<class="green">                    Adds one or more CSS classes to the cell
<tablestyle="color: red;">         Add CSS styling to table
<rowstyle="font-size: 140%; ">     Add CSS styling to row
<style="text-align: right;">       Add CSS styling to cell
<bgcolor="#ff0000">                Add CSS background color to cell
<rowbgcolor="#ff0000">             Add CSS background color to row
<tablebgcolor="#ff0000">           Add CSS background color to table
width                              Add CSS width to cell
tablewidth                         Add CSS width to table
id                                 Add HTML ID to cell
rowid                              Add HTML ID to row
tableid                            Add HTML ID to table
rowspan                            Add HTML rowspan attribute to cell
colspan                            Add HTML colspan attribute to cell
caption                            Add HTML caption attribute to table
<80%>                              Set cell width, setting one cell effects entire table column
<(>                                Align cell contents left
<)>                                Align cell contents right
<:>                                Center cell contents
`<|2>`                             Cell spans 2 rows (omit a cell in next row)
<-2>                               Cell spans 2 columns (omit a cell in this row)
<#0000FF>                          Change background color of a table cell
<rowspan="2">                      Same as `<|2>` above
<colspan="2">                      Same as <-2> above
-- no content --                   An empty cell has same effect as <-2> above
`===`                              A line of 3+ "=" separates table header, body and footer
================================== ===========================================================

Table Styling Example
---------------------

**Markup**: ::

 ||Head A||Head B||
 ===
 ||normal text||normal text||
 ||<|2>cell spanning 2 rows||cell in the 2nd column||
 ||cell in the 2nd column of the 2nd row||
 ||<rowstyle="font-weight: bold;" class="monospaced">monospaced text||bold text||

**Result**:


+----------------------+---------------------------------------+
|Head A                |Head B                                 |
+======================+=======================================+
| normal text          |normal text                            |
+----------------------+---------------------------------------+
| cell spanning 2 rows | cell in the 2nd column                |
|                      +---------------------------------------+
|                      | cell in the 2nd column of the 2nd row |
+----------------------+---------------------------------------+
|``monospaced text``   |**bold text**                          |
+----------------------+---------------------------------------+



Verbatim Display
----------------

To show plain text preformatted code, just enclose the text in three or more curly braces.

**Markup**: ::

 {{{
 no indentation example
 }}}

    {{{{
    {{{
    indentation; using 4 curly braces to show example with 3 curly braces
    }}}
    }}}}

**Result**: ::

 no indentation example

    {{{
    indentation; using 4 curly braces to show example with 3 curly braces
    }}}

Parsers
=======

Syntax Highlighting
-------------------

**Markup**: ::

 {{{#!highlight python
 def hello():
    print "Hello World!"
 }}}

**Result**:

.. code-block:: python

    def hello():
        print "Hello, world!"

creole, rst, markdown, docbook, and mediawiki
---------------------------------------------

To add a small section of markup using another parser, follow the example below replacing "creole" with the target parser name. The moinwiki parser does not have the facility to place table headings in the first column, but the creole parser can be used to create the desired table.

**Markup**: ::

 {{{#!creole
 |=X|1
 |=Y|123
 |=Z|12345
 }}}

**Result**:

======= =======
 X       1
 Y       123
 Z       12345
======= =======

csv
---

The default separator for CSV cells is a semi-colon (;). The example below specifies a comma (,) is to be used as the separator.

**Markup**: ::

 {{{#!csv ,
 Fruit,Color,Quantity
 apple,red,5
 banana,yellow,23
 grape,purple,126
 }}}

**Result**:

======= ======= =======
 Fruit   Color   Quantity
======= ======= =======
 apple   red     5
 banana  yellow  23
 grape   purple  126
======= ======= =======

wiki
----

The wiki parser is the moinwiki parser. If there is a need to emphasize a section, pass some predefined classes to the wiki parser.

**Markup**: ::

 {{{#!wiki solid/orange
 * plain
 * ''italic''
 * '''bold'''
 * '''''bold italic.'''''
 }}}

**Result**:

 - plain
 - ''italic''
 - '''bold'''
 - '''''bold italic.'''''

Admonitions
-----------

Admonitions are used to draw the reader's attention to an important paragraph. There are nine admonition types: attention, caution, danger, error, hint, important, note, tip, and warning.


**Markup**: ::

 {{{#!wiki caution
 '''Don't overuse admonitions'''

 Admonitions should be used with care. A page riddled with admonitions will look restless and will be harder to follow than a page where admonitions are used sparingly.
 }}}

**Result**:

.. caution::
 '''Don't overuse admonitions'''

 Admonitions should be used with care. A page riddled with admonitions will look restless and will be harder to follow than a page where admonitions are used sparingly.

CSS classes for use with the wiki parser
----------------------------------------

 - Background colors: red, green, blue, yellow, or orange
 - Borders: solid, dashed, or dotted
 - Text-alignment: left, center, right, or justify
 - Admonitions: caution, important, note, tip, warning
 - Comments: comment

Variables
=========

Variables within the content of a moin wiki item are transformed when the item is saved. An exception is if the item has a tag of '''template''', then no variables are processed. This makes variables particularly useful within template items. Another frequent use is to add signatures (@SIG@) to a comment within a discussion item.

Variable expansion is global and happens everywhere within an item, including code displays, comments, tables, headings, inline parsers, etc.. Variables within transclusions are not expanded because they are not part of the including item's content.

**TODO:** Allow wiki admins and users to add custom variables. There is no difference between system date format and user date format in Moin 2, fix code or docs.

Predefined Variables
--------------------

+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|Variable   |Description                              |Resulting Markup                           |Example Rendering                                    |
+===========+=========================================+===========================================+=====================================================+
|@PAGE@     |Name of the item (useful for templates)  |HelpOnPageCreation                         |HelpOnPageCreation                                   |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@ITEM@     |Name of the item (useful for templates)  |HelpOnPageCreation                         |HelpOnPageCreation                                   |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@TIMESTAMP@|Raw time stamp                           |2004-08-30T06:38:05Z                       |2004-08-30T06:38:05Z                                 |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@DATE@     |Current date in the system format        |<<Date(2004-08-30T06:38:05Z)>>             |<<Date(2004-08-30T06:38:05Z)>>                       |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@TIME@     |Current date and time in the user format |<<DateTime(2004-08-30T06:38:05Z)>>         |<<DateTime(2004-08-30T06:38:05Z)>>                   |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@ME@       |user's name or "anonymous"               |TheAnarcat                                 |TheAnarcat                                           |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@USERNAME@ |user's name or his domain/IP             | TheAnarcat                                |TheAnarcat                                           |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@USER@     |Signature "-- loginname"                 |-- TheAnarcat                              |-- TheAnarcat                                        |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@SIG@      |Dated Signature "-- login name date time"|-- TheAnarcat <<DateTime(...)>>            |-- TheAnarcat <<DateTime(2004-08-30T06:38:05Z)>>     |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@EMAIL@    |<<MailTo()>> macro, obfuscated email     |<<MailTo(user AT example DOT com)          |user@example.com OR user AT example DOT com          |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+
|@MAILTO@   |<<MailTo()>> macro                       |<<MailTo(testuser@example.com)             |testuser@example.com, no obfuscation                 |
+-----------+-----------------------------------------+-------------------------------------------+-----------------------------------------------------+

**Notes:**

 - @PAGE@ and @ITEM@ results are identical, item being a moin 2 term and page a moin 1.x term.

 - If an editor is not logged in, then any @EMAIL@ or @MAILTO@ variables in the content are made harmless by inserting a space character. This prevents a subsequent logged in editor from adding his email address to the item accidentally.

Macros
======

Macros are extensions to standard markup that allow developers to add extra features. The following is a table of MoinMoin's macros.

+-------------------------------------------+------------------------------------------------------------+
| Markup                                    | Comment                                                    |
+===========================================+============================================================+
| ``<<Anchor(anchorname)>>``                | Inserts an anchor named "anchorname"                       |
+-------------------------------------------+------------------------------------------------------------+
| ``<<BR>>``                                | Inserts a forced linebreak                                 |
+-------------------------------------------+------------------------------------------------------------+
| ``<<Date()>>``                            | Inserts current date, or unix timestamp or ISO 8601 date   |
+-------------------------------------------+------------------------------------------------------------+
| ``<<DateTime()>>``                        | Inserts current datetime, or unix timestamp or ISO 8601    |
+-------------------------------------------+------------------------------------------------------------+
| ``<<GetText(Settings)>>``                 | Loads I18N texts, Einstellungen if browser is set to German|
+-------------------------------------------+------------------------------------------------------------+
| ``<<GetVal(WikiDict,var1)>>``             | Loads var1 value from metadata of item named WikiDict      |
+-------------------------------------------+------------------------------------------------------------+
| ``<<FootNote(Note here)>>``               | Inserts a footnote saying "Note here"                      |
+-------------------------------------------+------------------------------------------------------------+
| ``<<FontAwesome(name,color,size)>>``      | displays Font Awsome icon, color and size are optional     |
+-------------------------------------------+------------------------------------------------------------+
| ``<<Icon(my-icon.png)>>``                 | displays icon from /static/img/icons                       |
+-------------------------------------------+------------------------------------------------------------+
| ``<<Include(ItemOne/SubItem)>>``          | Embeds the contents of ``ItemOne/SubItem`` inline          |
+-------------------------------------------+------------------------------------------------------------+
| ``<<MailTo(user AT example DOT org,       | If the user is logged in this macro will display           |
| write me)>>``                             | ``user@example.org``, otherwise it will display the        |
|                                           | obfuscated email address supplied                          |
|                                           | (``user AT example DOT org``)                              |
|                                           | The second parameter containing link text is optional.     |
+-------------------------------------------+------------------------------------------------------------+
| ``<<PageNameList()>>``                    | Inserts names of all wiki items                            |
+-------------------------------------------+------------------------------------------------------------+
| ``<<RandomItem(3)>>``                     | Inserts names of 3 random items                            |
+-------------------------------------------+------------------------------------------------------------+
| ``<<ShowIcons()>>``                       | displays all icons in /static/img/icons directory          |
+-------------------------------------------+------------------------------------------------------------+
| ``<<TableOfContents(2)>>``                | Shows a table of contents up to level 2                    |
+-------------------------------------------+------------------------------------------------------------+
| ``<<Verbatim(`same` __text__)>>``         | Inserts text as entered                                    |
+-------------------------------------------+------------------------------------------------------------+

Smileys and Icons
=================

This table shows moin smiley markup, the rendering of smiley icons cannot be shown in Rest markup.

+---------+---------+---------+---------+
| ``X-(`` | ``:D``  | ``<:(`` | ``:o``  |
+---------+---------+---------+---------+
| ``:(``  | ``:)``  | ``B)``  | ``:))`` |
+---------+---------+---------+---------+
| ``;)``  | ``/!\`` | ``<!>`` | ``(!)`` |
+---------+---------+---------+---------+
| ``:-?`` | ``:\``  | ``>:>`` | ``|)``  |
+---------+---------+---------+---------+
| ``:-(`` | ``:-)`` | ``B-)`` | ``:-))``|
+---------+---------+---------+---------+
| ``;-)`` | ``|-)`` | ``(./)``| ``{OK}``|
+---------+---------+---------+---------+
| ``{X}`` | ``{i}`` | ``{1}`` | ``{2}`` |
+---------+---------+---------+---------+
| ``{3}`` | ``{*}`` | ``{o}`` |         |
+---------+---------+---------+---------+

Comments
--------

**Markup**: ::

 {{{#!wiki comment/dotted
 This is a wiki parser section with class "comment dotted" (see HelpOnParsers).

 Its visibility gets toggled the same way.
 }}}

**Result**:

+--------------------------------------------------------------------------------+
| This is a wiki parser section with class "comment dotted" (see HelpOnParsers). |
|                                                                                |
| Its visibility gets toggled the same way.                                      |
+--------------------------------------------------------------------------------+

**Notes**:
 - reStructuredText has no support for dotted borders, so a table cell is used to illustrate the border which will be produced. This markup will actually produce a dotted border in MoinMoin.
 - The toggle display feature does not work yet
