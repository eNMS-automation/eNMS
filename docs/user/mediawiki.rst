.. role:: underline
.. role:: strikethrough
.. role:: bolditalic

=========================
Mediawiki markup overview
=========================

Features currently not working with moin's mediawiki parser are marked with **MWTODO**.

Features currently not working with moin's rst parser are marked with **RSTTODO**.

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

**Intentionally not rendered as level 1 so it does not interfere with Sphinx's indexing**

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

Text formatting
===============

These markups can be used within text to apply character style.

+------------------------------------+------------------------------------+
| Markup                             | Result                             |
+====================================+====================================+
| ``'''Bold text'''``                | **Bold text**                      |
+------------------------------------+------------------------------------+
| ``''Italic text''``                | *Italic text*                      |
+------------------------------------+------------------------------------+
| ``'''''Bold and italic text'''''`` | :bolditalic:`Bold and italic text` |
+------------------------------------+------------------------------------+
| ``<nowiki>no ''markup''</nowiki>`` | ``no ''markup''``                  |
+------------------------------------+------------------------------------+
| ``<u>underline</u>``               | :underline:`underline`             |
+------------------------------------+------------------------------------+
| | ``<del>strikethrough</del>``     | :strikethrough:`strikethrough`     |
| | or                               |                                    |
| | ``<s>striketrough</s>``          |                                    |
+------------------------------------+------------------------------------+
| | ``<code>Fixed width</code>``     | ``Fixed width``                    |
| | or                               |                                    |
| | ``<tt>Fixed width</tt>``         |                                    |
+------------------------------------+------------------------------------+
| | ``<pre>Preformatted text``       | | ``Preformatted text``            |
| | ``without '''markups'''</pre>``  | | ``without '''markups'''``        |
+------------------------------------+------------------------------------+

**RSTTODO**
table headers are not formatted as headers
(see "Tables" section for corresponding MWTODO)

Hyperlinks
==========

Internal links
--------------

**RSTTODO**
These link targets are not interpreted.
(The examples shown here result in empty links)

.. These are the link targets for the examples:
.. __:
.. __:

**RSTTODO**
Comments (lines starting with ``..``) are printed

+---------------------------------------+--------------------------+-------------------------------------+
| Markup                                | Result                   | Comment                             |
+=======================================+==========================+=====================================+
| ``[[Item name]]``                     | `Item name`__            | Link to an item                     |
+---------------------------------------+--------------------------+-------------------------------------+
| ``[[Item name|alternative text]]``    | `alternative text`__     | Link with alternative text          |
+---------------------------------------+--------------------------+-------------------------------------+
| ``[[#anchor]]``                       | `#anchor`__              | Link to an anchor on this item      |
+---------------------------------------+--------------------------+-------------------------------------+
| ``[[#anchor|alternative text]]``      | `alternative text`__     | Link to an anchor with alternative  |
|                                       |                          | text                                |
+---------------------------------------+--------------------------+-------------------------------------+
| ``[[Item name#anchor]]``              | `Item name#anchor`__     | Link to an anchor on another item   |
+---------------------------------------+--------------------------+-------------------------------------+
| ``<div id="anchor">text</div>``       | .. __:                   | Definition of an anchor **MWTODO**  |
|                                       | .. __:                   | (div tag is not interpreted)        |
|                                       |                          |                                     |
|                                       | text                     |                                     |
+---------------------------------------+--------------------------+-------------------------------------+
| ``[[/subitem]]``                      | `/subitem`__             | Link to a subitem                   |
+---------------------------------------+--------------------------+-------------------------------------+
| ``[[media:image.jpg]]``               | `media:image.jpg`__      | Link to a file **MWTODO**           |
|                                       |                          | (irrelevant for moin?)              |
+---------------------------------------+--------------------------+-------------------------------------+

.. __:
.. __:
.. __:

External links
--------------

+-------------------------------------+--------------------------+-------------------------------------+
| Markup                              | Result                   | Comment                             |
+=====================================+==========================+=====================================+
| ``http://www.example.com``          | http://www.example.com   | External link **MWTODO**            |
|                                     |                          | (not converted into a hyperlink)    |
+-------------------------------------+--------------------------+-------------------------------------+
| ``[http://www.example.com text]``   | text_                    | External link with alternative text |
+-------------------------------------+--------------------------+-------------------------------------+
| ``[http://www.example.com]``        | `[1]`_                   | External link with number **MWTODO**|
|                                     |                          | (no numbering, normal link)         |
+-------------------------------------+--------------------------+-------------------------------------+
| ``[mailto:test@example.com mail]``  | mail_                    | Mailto link                         |
+-------------------------------------+--------------------------+-------------------------------------+

.. _text: http://www.example.com
.. _[1]: http://www.example.com
.. _mail: mailto:test@example.com

Images
======

**MWTODO**
Use of ``[[File:...]]`` causes this error:
``AttributeError: 'unicode' object has no attribute 'keyword'``

Syntax
------

The syntax for inserting an image is as follows: ::

 [[File:<filename>|<options>|<caption>]]

The *options* field can be empty or can contain one or more of
the following options separated by pipes (``|``).

Format option:
    Controls how the image is formatted in the item.

    one of ``border`` and/or ``frameless``, ``frame`` or ``thumb``
Resizing option:
    Controls the display size of the picture.
    The aspect ratio cannot be changed.

    one of ``<width>px``, ``x<height>px``, ``<width>x<height>px`` or ``upright``
Horizontal alignment option:
    Controls the horizontal alignment of an image.

    one of ``left``, ``right``, ``center`` or ``none``
Vertical alignment option:
    Controls the vertical alignment of a non-floating inline image.

    one of ``baseline``, ``sub``, ``super``, ``top``, ``text-top``, ``middle`` (default), ``bottom`` or ``text-bottom``
Link option:
    The option ``link=<target>`` allows to change the
    target of the link represented by the picture.
    The image will not be clickable if ``<target>`` is left empty.

    Please note that the link option cannot be used with one of the options ``thumb`` or ``frame``.
Other options:
    The ``alt=<alternative text>`` option sets the alternative
    text (HTML attribute ``alt=``) of the image.

    The option ``page=<number>`` sets the number of the page
    of a .pdf or .djvu file    to be rendered.

Examples
--------

+-----------------------------------------+---------------------------------+
| Markup                                  | Description                     |
+=========================================+=================================+
| ``[[File:example.png]]``                | Displays an image without       |
|                                         | further options.                |
+-----------------------------------------+---------------------------------+
| ``[[File:example.png|border]]``         | Displays the image with a       |
|                                         | thin border.                    |
+-----------------------------------------+---------------------------------+
| ``[[File:example.png|frame|text]]``     | Displays the image in a         |
|                                         | frame (not inline) and shows    |
|                                         | *text* as caption.              |
+-----------------------------------------+---------------------------------+
| ``[[File:example.png|thumb|text]]``     | Displays a thumbnail of the     |
|                                         | image (not inline) and shows    |
|                                         | *text* as caption.              |
+-----------------------------------------+---------------------------------+
| ``[[File:example.png|frameless]]``      | Like ``thumb`` but inline       |
|                                         | and without border and frame    |
+-----------------------------------------+---------------------------------+

Paragraphs
==========

**Markup**: ::

 You can leave an empty line to start a new paragraph.

 Single breaks are ignored.
 To force a line break, use the <br /> HTML tag.

**Result**:

You can leave an empty line to start a new paragraph.

| Single breaks are ignored. To force a line break, use the
| HTML tag.

Horizontal rules
================

**Markup**: ::

 A horizontal rule can be added by typing four dashes.

 ----

 This text will be displayed below the rule.

**Result**:

A horizontal rule can be added by typing four dashes.

----

This text will be displayed below the rule.

**RSTTODO**
Horizontal rule is not interpreted.

Preformatted text
=================

**Markup**: ::

 ␣Each line that starts
 ␣with a space
 ␣is preformatted. It is ''possible''
 ␣to use inline '''markups'''.

**Result**:

| Each line that starts
| with a space
| is preformatted. It is *possible*
| to use inline **markups**.

**MWTODO**
Preformatted text is not interpreted.

**RSTTODO**
Line blocks (lines starting with ``|``) are not interpreted.

Comments
========

**Markup**: ::

 <!-- This is a comment -->
 Comments are only visible in the modify window.

**Result**:

Comments are only visible in the modify window.

**MWTODO**
This is not interpreted (i.e. comments are printed).

**MWTODO**
A line starting with ``##`` is treated as comment, although
it should be treated as part of an ordered list (see section "Ordered lists").

**MWTODO**
It seems that ``/*…*/`` is treated as comment,
whereas this is not intended in mediawiki syntax.

Symbol entities
===============

A special character can be placed by using a symbol entity.
The following table shows some examples for symbol entities:

+-----------+-----------+
| Entity    | Character |
+===========+===========+
|``&mdash;``| —         |
+-----------+-----------+
| ``&larr;``| ←         |
+-----------+-----------+
| ``&rarr;``| →         |
+-----------+-----------+
| ``&lArr;``| ⇐         |
+-----------+-----------+
| ``&rArr;``| ⇒         |
+-----------+-----------+
| ``&copy;``| ©         |
+-----------+-----------+

It is also possible to use numeric entities like ``&#xnnnn;``
where "nnnn" stands for a hexadecimal number.

Lists
=====

Ordered lists
-------------

Ordered lists are formed of lines that start with number signs (``#``).
The count of number signs at the beginning of a line determines the level.

**Markup**: ::

 # First item
 # Second item
 ## First item (second level)
 ## Second item (second level)
 ### First item (third level)
 # Third item

**Result**:

1. First item
2. Second item

 #. First item (second level)
 #. Second item (second level)

  #. First item (third level)

3. Third item

Unordered lists
---------------

**Markup**: ::

 * List item
 * List item
 ** List item (second level)
 *** List item (third level)
 * List item

**Result**:

- List item
- List item

 - List item (second level)

  - List item (third level)

- List item

Definition lists
----------------

**Markup**: ::

 ;term
 : definition
 ;object
 : description 1
 : description 2

**Result**:

term
  definition

object
  description 1

  description 2

Mixed lists
-----------

It is possible to combine different types of lists.

**Markup**: ::

 # first item
 # second item
 #* point one
 #* point two
 # third item
 #; term
 #: definition
 #: continuation of the definition
 # fourth item

**Result**:

1. first item
2. second item

 - point one
 - point two

3. third item

 term
  definition

  continuation of the definition

4. fourth item

Indentations
============

Definition lists can also be used to indent text.

**Markup**: ::

 : single indent
 :: double indent
 :::: multiple indent

**Result**:

 single indent
  double indent
    multiple indent

Footnotes
=========

Footnotes can be used for annotations and citations rolled out of the
continuous text.

**Markup**: ::

 This is a footnote <ref>This description will be placed at the item's bottom.</ref>

**Result**:

This is a footnote [1].

[1] This description will be placed at the item's bottom.

Tables
======

Syntax
------

+-----------+-------------------------------------------------------+
| Markup    | Description                                           |
+===========+=======================================================+
| ``{|``    | **table start** (required)                            |
+-----------+-------------------------------------------------------+
| ``|+``    | **table caption** (optional) **MWTODO**               |
|           | (not interpreted)                                     |
|           |                                                       |
|           | only between table start and first row                |
+-----------+-------------------------------------------------------+
| ``|-``    | **table row** (optional)                              |
|           |                                                       |
|           | This is not necessary for the first row.              |
+-----------+-------------------------------------------------------+
| ``|``     | **table data** (required)                             |
|           |                                                       |
|           | Start each line that contains table data with ``|``   |
|           | or separate data on the same line with ``||``         |
+-----------+-------------------------------------------------------+
| ``!``     | **table header** (optional) **MWTODO**                |
|           | (not formatted as header)                             |
|           |                                                       |
|           | Start each line that represents a table               |
|           | header with ``!``                                     |
|           | or separate different headers on the same line        |
|           | with ``!!``.                                          |
+-----------+-------------------------------------------------------+
| ``|}``    | **table end** (required)                              |
+-----------+-------------------------------------------------------+

Basic tables
------------

Note that the following tables do not have visible borders
as this has to be done with XHTML attributes.

**MWTODO**
Tables should be borderless by default, the ``border`` attribute is not interpreted.

**Markup**: ::

 {|
 |row 1, column 1
 |row 1, column 2
 |-
 |row 2, column 1
 |row 2, column 2
 |}

**Result**:

=============== ===============
row 1, column 1 row 1, column 2
row 2, column 1 row 2, column 2
=============== ===============

**Markup**: ::

 {|
 !header 1
 !header 2
 |-
 |A
 |B
 |-
 |C
 |D
 |}

Alternative syntax: ::

 {|
 !header 1!!header 2
 |-
 |A||B
 |-
 |C||D
 |}

**Result**:

======== ========
header 1 header 2
======== ========
A        B
C        D
======== ========

It is possible to use other elements inside tables:

**Markup**: ::

 {|
 !header 1
 !header 2
 |-
 |A line break<br />can be done with the XHTML tag.
 |A pipe symbol has to be inserted like this: <nowiki>|</nowiki>
 |-
 |
 * This
 * is a bullet list
 * in a table cell.
 |[http://www.example.com Hyperlink]
 |}

**Result**:

+-----------------------------------+-----------------------------+
| header 1                          | header 2                    |
+===================================+=============================+
| | A line break                    | A pipe symbol has           |
| | can be done with the XHTML tag. | to be inserted like this: | |
+-----------------------------------+-----------------------------+
| - This                            | Hyperlink_                  |
| - is a bullet list                |                             |
| - in a table cell                 |                             |
+-----------------------------------+-----------------------------+

.. _Hyperlink: http://www.example.com

**MWTODO**
Lists cannot be used inside cells.

XHTML attributes
----------------

It is allowed to use XHTML attributes
(border, align, style, colspan, rowspan, …) inside tables.

**Markup**: ::

 {|border="1"
 |This table has a border width of 1.
 |align="left" | This cell is left aligned.
 |-
 |colspan="2" | This cell has a colspan of 2.
 |}

**Result**:

+-----------------------------+-----------------------------+
| This table has a border     | This cell is left aligned.  |
| width of 1.                 |                             |
+-----------------------------+-----------------------------+
| This cell has a colspan of 2.                             |
+-----------------------------------------------------------+

**MWTODO**
attributes ``border`` and ``align`` are not interpreted

**RSTTODO**
colspan is not interpreted
