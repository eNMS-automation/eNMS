.. role:: bolditalic

===============
Markdown Markup
===============

This page introduces you to the most important elements of the Markdown syntax.
For details on the Python implementation of Markdown see https://pythonhosted.org/Markdown/

In addition to being supported by moin2, the Markdown markup language is used by issue trackers
such as those found in Bitbucket and Github. So what you learn here can be used to create or
edit issues on the `moin issue tracker <https://bitbucket.org/thomaswaldmann/moin-2.0/issues>`_.

Features currently not working with moin's Markdown parser are marked with **MDTODO**.

This page, describing the Markdown syntax, is written in RST. Instances where RST cannot
duplicate the same rendering produced by Markdown are flagged with **RST NOTE**.
The RST parser used by Moin and the parser used by Sphinx are different. As noted below there
are several instances where one works and the other fails.

Table of Contents
=================

The table of contents is a supported extension that is distributed with Python Markdown.

**Markup**: ::

    [TOC]

**Result**:

.. contents::

Headings
========

Level 1 and 2 headings may be created by underlining with = and - characters, respectively.

Having equal numbers of characters in the heading and the underline
looks best in raw text, but having fewer or more = or - characters also works.

Heading levels 3 through 6 must be defined by prefixing the heading with a variable number of # characters indicating the heading level.  Heading levels 1 and 2 may be defined in the same manner. It is customary, but not required, to follow the # characters with a single space character. Another option is to append the appropriate number of # characters after the heading text.

**Markup**: ::

    Level 1
    =======
    # Level 1
    Level 2
    -------
    ## Level 2
    --- Levels 1 and 2 are not shown below, see top of page and this section heading.
    ### Level 3
    #### Level 4
    ##### Level 5
    ###### Level 6 ######


**Result**:

Level 3
-------

Level 4
*******

Level 5
:::::::

Level 6
+++++++

Preformatted Code
=================

To show a preformatted block of code, indent all the lines by 4 or more spaces.

**Markup**: ::

 Begin preformatted code

    First line
    Second line
        Third line

 End of preformatted code


**Result**:

Begin preformatted code ::

    First line
    Second line
        Third line

End of preformatted code

Simple text editing
===================

**Markup**: ::

    Paragraphs are separated
    by a blank line.

    To create a line break, end a line
    with 2 spaces.

    Use asterisk characters to create text attributes: *italic*, **bold**, ***bold italics***.
    Or, do the same with underscores: _Italics_, __bold__, ___bold italics___.
    Use backticks to create `monospace`.


**Result**:

Paragraphs are separated
by a blank line.

To create a line break, end a line
with 2 spaces.

Use asterisk characters to create text attributes: *italic*, **bold**, :bolditalic:`bold italics`.
Or, do the same with underscores: *Italics*, **bold**, :bolditalic:`bold italics`.
Use backticks to create ``monospace``.

**RST NOTE**:

RST has no means of forcing a line break, so the above example showing a line ending with 2 spaces fails. RST does not support bold-italics so the above example fails.

Linking
=======

**Markup**: ::

    A simple way to write a link: [MoinMoin](http://moinmo.in) or [PNG](png)
    Another way to write a link is to use a reference: [favorite comic][xkcd]

    References can be defined anywhere in the document, but it will not be visible in the rendered HTML:
    [xkcd]: http://xkcd.com

    Naked URLs like http://moinmo.in are not supported. URLs and email addresses may be enclosed in angle brackets: <http://moinmo.in> and <me@example.com>.


**Result**:

A simple way to write a link: `MoinMoin <http://moinmo.in>`_ or `PNG <png>`_
Another way to write a link is to use a reference: `favorite comic <xkcd>`_

References can be defined anywhere in the document, but it will not be visible in the rendered HTML:

Naked URLs like `http://moinmo.in` are not supported. URLs and email addresses may be enclosed in angle brackets: http://moinmo.in and me@example.com.


Lists
=====

Unordered lists may use `*`, +, or - characters as bullets.  The character used as a bullet does not effect the display.  The display would be the same if `*` characters were used everywhere.

**Markup**: ::

    * apples
    * oranges
    * pears
        - carrot
        - beet
            + man
            + woman


**Result**:

* apples
* oranges
* pears
    - carrot
    - beet
        + man
        + woman

**RST NOTE**: While Sphinx renders the above correctly, the Moin RST parser shows pears and beet in bold text.


Ordered lists use numbers and are incremented in regular order. Neither alpha characters nor roman numerals are supported. Although you may use numbers other than 1 with no adverse effect (as shown below), it is a best practice to always start a list with 1.

**Markup**: ::

    1. apples
    1. oranges
    7. pears
        1. carrot
        1. beet
            1. man
            1. woman


**Result**:

 1. apples
 #. oranges
 #. pears

    1. carrot
    #. beet

        1. man
        #. woman

Lists composed of long paragraphs are easier to read in raw text if the lines are manually wrapped with **optional** hanging indents. If multiple paragraphs are required, separate the paragraphs with blank lines and indent.

**Markup**: ::

    *   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
        Aliquam hendrerit mi posuere lectus. Vestibulum enim wisi,
        viverra nec, fringilla in, laoreet vitae, risus.
    *   Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
        Suspendisse id sem consectetuer libero luctus adipiscing.
    *   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
    Aliquam hendrerit mi posuere lectus. Vestibulum enim wisi,
    viverra nec, fringilla in, laoreet vitae, risus.
    *   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
    Aliquam hendrerit mi posuere lectus. Vestibulum enim wisi,
    viverra nec, fringilla in, laoreet vitae, risus.
    *   Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
    Suspendisse id sem consectetuer libero luctus adipiscing.


**Result**:

 -   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
     Aliquam hendrerit mi posuere lectus. Vestibulum enim wisi,
     viverra nec, fringilla in, laoreet vitae, risus.
 -   Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
     Suspendisse id sem consectetuer libero luctus adipiscing.
 -   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
     Aliquam hendrerit mi posuere lectus. Vestibulum enim wisi,
     viverra nec, fringilla in, laoreet vitae, risus.
 -   Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
     Aliquam hendrerit mi posuere lectus. Vestibulum enim wisi,
     viverra nec, fringilla in, laoreet vitae, risus.
 -   Donec sit amet nisl. Aliquam semper ipsum sit amet velit.
     Suspendisse id sem consectetuer libero luctus adipiscing.

Horizontal Rules
================

To create horizontal rules, use 3 or more -, `*`, or _ on a line. Neither changing the character nor increasing the number of characters will change the width of the rule.
Putting spaces between the characters also works.

**Markup**: ::

    ---

    text

    - - - - - -

    more text

    ******

    more text

    ______


**Result**:

----

text

-----

more text

******

more text

______


Backslash Escapes
=================

Sometimes there is a need to use special characters as literal characters, but Markdown's syntax gets in the way.  Use the backslash character as an escape.

**Markup**: ::

    *hot*

    333. is a float, 333 is an integer.

    \*hot\*

    333\. is a float, 333 is an integer.


**Result**:

*hot*

333. is a float, 333 is an integer.

\*hot\*

333\. is a float, 333 is an integer.

**RST NOTE**: The Moin RST parser flags the use of 333 as a bullet number.


Nested Blockquotes
==================

Advanced blockquotes with nesting are created by starting a line with a > character.

**Markup**: ::

    > A standard blockquote is indented
    > > A nested blockquote is indented more
    > > > > You can nest to any depth.


**Result**:

    A standard blockquote is indented
        A nested blockquote is indented more
            You can nest to any depth.

**RST NOTE**: Moin's RST parser markup confuses nested blockquotes rendering with term: definition syntax. Sphinx renders it correctly.

Images
======

Images are similar to links with both an inline and a reference style, but they start with an exclamation point. Within Markdown, there is no syntax to change the default sizes or positions of transclusions:

**Markup**: ::

    To transclude image from local wiki:
    ![Alt text](png "Optional title")

    Reference-style, where "logo" is a name defined anywhere within this item:
    ![Alt text][logo]

    Image references are defined using syntax identical to link references and
    do not appear in the rendered HTML:
    [logo]: png  "Optional title attribute"

    To transclude image from remote site:
    ![remote image](http://static.moinmo.in/logos/moinmoin.png)

    Transcluding a page from a remote site works, but there is no way to change the browser's default size:

    ![Alt text](http://test.moinmo.in/png)

**Result**:

To transclude image from local wiki:

.. image:: png
   :alt: Alt text
   :align: right

Reference-style, where "logo" is a name defined anywhere within this item:

.. image:: png
   :alt: Alt text
   :align: right

Image references are defined using syntax identical to link references and
do not appear in the rendered HTML:

To transclude image from remote site:

.. image:: http://static.moinmo.in/logos/moinmoin.png
   :alt: remote image
   :align: right

Transcluding a page from a remote site works, but there is no way to change the browser's default size:

.. image:: http://test.moinmo.in/png
   :alt: Alt text
   :align: center

**RST NOTE**: The Moin RST parser renders all four images above. The Sphinx parser renders only the external png image from http://static.moinmo.in/logos/moinmoin.png. RST syntax does allow the rendering of inline images, nor the use of a title attribute. The logos above are floated right, in Markdown the logos would appear as inline images.

Inline HTML
===========

**Note:** This feature is dependent upon configuration settings. See configuration docs for information on allow_style_attributes.

You may embed a small subset of HTML tags directly into your markdown documents. ::

    <a>              - hyperlink.
    <b>              - bold, use as last resort <h1>-<h3>, <em>, and <strong> are preferred.
    <blockquote>     - specifies a section that is quoted from another source.
    <code>           - defines a piece of computer code.
    <del>            - delete, used to indicate modifications.
    <dd>             - describes the item in a <dl> description list.
    <dl>             - description list.
    <dt>             - title of an item in a <dl> description list.
    <em>             - emphasized.
    <h1>, <h2>, <h3> - headings.
    <i>              - italic.
    <img>            - specifies an image tag.
    <kbd>            - shows keyboard input.
    <li>             - list item in an ordered list <ol> or an unordered list <ul>.
    <ol>             - ordered list.
    <p>              - paragraph.
    <pre>            - pre-element displayed in a fixed width font and unchanged line breaks.
    <s>              - strikethrough.
    <sup>            - superscript text appears 1/2 character above the baseline used for footnotes and other formatting.
    <sub>            - subscript appears 1/2 character below the baseline.
    <strong>         - defines important text.
    <strike>         - strikethrough is deprecated, use <del> instead.
    <ul>             - unordered list.
    <br>             - line break.
    <hr>             - defines a thematic change in the content, usually via a horizontal line.

**Markup**: ::

    E = MC<sup>2</sup>

    This word is <b>bold</b>.

    This word is <em>italic</em>.

    This word is <strong>bold</strong>.

    This word is <strong style="color:red;background-color:yellow">bold</strong>; colors depend upon configuration settings.

**Result**:

E = MC<sup>2</sup>

This word is <b>bold</b>.

This word is <em>italic</em>.

This word is <strong>bold</strong>.

This word is <strong style="color:red;background-color:yellow">bold</strong>; colors depend upon configuration settings.

**RST NOTE**: The RST parser does not allow inline HTML markup so none of the above examples are rendered as they would be in Moin's Markdown.

Extensions
==========

In addition to the TOC extension shown near the top of this page, the following features are installed as part of the "extras" extension.


Tables
------

All tables must have one heading row. By default table headings are centered and table body cells are aligned left. Use a ":" character on the left, right or both sides of the heading-body separator to change the alignment. Changing the alignment changes both the heading and table body cells.

As shown in the second table below, use of outside borders and neat alignment of the cells do not effect the display. Markup within the table cells is supported.

**Markup**: ::

    |Tables            |Are            |Very  |Cool    |
    |------------------|:-------------:|-----:|:-------|
    |col three is      |right-aligned  |$1600 |Necklace|
    |col 2 is          |centered       |$12   |Gloves  |
    |col 4 is          |left-aligned   |$100  |Hat     |

    `Tables`            |*Are*            |Very  |Cool
    ------------|:-------------:|-----:|:-------
    `col three is`|*right-aligned*|$1600|Necklace
    `col 2 is`|*centered*|$12|Gloves
    `col 4 is`|*left-aligned*|$100|Hat


**Result**:

**RST NOTE**: RST tables are broken on the Moin RST parser. Although table rendering on Sphinx is correct, there is no means of specifying cell alignment; therefore, none of the examples are shown.


Syntax Highlighting of Preformatted Code
----------------------------------------

A second way to create a block of preformatted code without indenting every line is to wrap the block in triple backticks.

To highlight code syntax, wrap the code in triple backtick characters and specify the language on the first line.  Many languages are supported.

**Markup**: ::

    ``` javascript
    var s = "JavaScript syntax highlighting";
    alert(s);
    ```

**Result**: ::

    var s = "JavaScript syntax highlighting";
    alert(s);

**MDTODO**: Syntax highlighting is not working. [#169](https://bitbucket.org/thomaswaldmann/moin-2.0/issue/169/highlight-python-does-not-work) documents a similar issue for the moinwiki converter.


Fenced Code
-----------

Another way to display a block of preformatted code is to "fence" the code with lines starting with three ~ characters.

**Markup**: ::

    ~~~
    ddd
    eee
    fff
    ~~~

**Result**: ::

   ddd
   eee
   fff

Smart Strong
------------

The smart strong extension prevents words with embedded double underscores from being converted. e.g.
`double__underscore__words` is wanted, not `double`**underscore**`words`.

**Markup**: ::

    Text with double__underscore__words.

    __Strong__ still works.

    __this__works__too__.

**Result**:

Text with double__underscore__words.

**Strong** still works.

**this__works__too**.



Attribute Lists
---------------

**Markup**: ::

    A class of green (that will create a green background per a CSS rule) is
    added to this paragraph.
    {: class="green"}

**Result**:

A class of green (that will create a green background per a CSS rule) is
added to this paragraph.

**RST NOTE**: The background of the above paragraph is not green because there is no option in RST syntax to assign a class.

Definition Lists
----------------

**Markup**: ::

    Apple
    :   Pomaceous fruit of plants of the genus Malus in
        the family Rosaceae.
    :   An american computer company.

    Orange
    :   The fruit of an evergreen tree of the genus Citrus.

**Result**:

Apple
    Pomaceous fruit of plants of the genus Malus in the family Rosaceae.
    An american computer company.

Orange
    The fruit of an evergreen tree of the genus Citrus.

**RST NOTE**: Two line definition lists do not render as two line definitions in RST.

Footnotes
---------

The syntax for footnotes in Markdown is rather unique.[^unique] Place any unique label after the characters "[^"  and close the label with a "]". The footnote text may be placed after the reference on a new line using the label, followed by a ":", followed by the footnote text. All footnotes are placed at the bottom of the document under a horizontal rule in the order defined.

[^unique]: Markdown footnotes are unique.

**Markup**: ::

    Footnotes[^1] have a label[^label] and a definition[^!DEF].

    [^1]: This is a footnote
    [^label]: A footnote on "label"
    [^!DEF]: The footnote for definition

**Result**:

Footnotes [1]_ have a label [#label]_ and a definition [#DEF]_.

.. [1] This is a footnote

.. [#label] A footnote on "label"

.. [#DEF] The footnote for definition
