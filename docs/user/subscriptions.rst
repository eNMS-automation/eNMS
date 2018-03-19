==================
User Subscriptions
==================

Users can subscribe to moin items in order to receive notifications about item
changes. Item changes include:

 * creation of a new item
 * modification of an existing item
 * renaming of an item
 * reverting an item's revision
 * copying of an item
 * deletion of an item
 * destruction of a revision
 * destruction of all item's revisions

Make sure that Moin is able to send E-Mails, see :ref:`mail-configuration`.

Types of subscriptions
======================

There are 5 types of subscriptions:

 * by itemid (`itemid:<itemid value>`)

   This is the most common subscription to a single item. The user will be notified
   even after the item is renamed, because itemid doesn't change. If you click on
   *Subscribe* on item's page, then you will be subscribed using this type.
 * by item name (`name:<namespace>:<name value>`),

   The user will be notified, if the name matches any of the item names and also
   its namespace. Keep in mind that an item can be renamed and notifications for
   this item would stop working if the new name doesn't match any more.
 * by tag name (`tags:<namespace>:<tag value>`)

   The user will be notified, if the tag name matches any of the item tags and
   its namespace.
 * by a prefix name (`nameprefix:<namespace>:<name prefix>`)

   Used for subscription to a set of items. The user will be notified, if at least
   one of the item names starts with the given prefix and matches item's namespace.
   For example if you want to receive notifications about all the items from the
   default namespace whose name starts with `foo`, you can use `nameprefix::foo`.
 * by a regular expression (`namere:<namespace>:<name regexp>`)

   Used for subscription to a set of items. The user will be notified, if the
   regexp matches any of the item names and also its namespace. For example,
   if you want to receive notifications about all the items on wiki from the default
   namespace, then you can use `namere::.*`


Editing subscriptions
=====================

The itemid subscription is the most common one and will be used if you click on
*Subscribe* on item's page. Respectively the *Unsubscribe* will remove the itemid
subscription.

If you were subscribed to an item by some other way rather than itemid subscription,
then on *Unsubscribe* you will be told that it is impossible to remove the subscription
and you need to edit it manually in the User Settings.

All the subscriptions can be added/edited/removed in the User Settings,
Subscriptions tab. Each subscription is listed on a single line and is
case-sensitive. Empty lines are ignored.

For itemid subscriptions, we additionally show the current first item name in
parentheses (this is purely for your information, the name is not stored or used
in any way).
