===============================
Password Resetting/Invalidation
===============================
There might be circumstances when the wiki admin wants or needs to reset one
user's or all users' password (hash).

For example:

* you had a security breach on your wiki server (or somewhere else) and the
  old password hashes (or passwords) were exposed
* you want to make sure some user or all users set a new password, e.g. if:

  - your password policy has changed (requiring longer passwords for example)
  - you changed your passlib configuration and want to immediately have all
    hashes upgraded

Note: if we say "reset a password" (to use a commonly used term), we mean to
"invalidate the password hash" (so that no password exists that validates
against that hash). MoinMoin does not keep user passwords in cleartext.

The files we refer to below are located in docs/examples/password-reset/...


Resetting one or few password(s)
================================
If you somehow interact with the users corresponding to the user accounts in
question (by phone or directly), you don't need the extensive procedure as
described below, just use::

    moin account-password --name JoeDoe

That will reset JoeDoe's password. Tell him to visit the login URL and use
the "forgot my password" functionality to define a new password.

If that doesn't work (e.g. if e-mail is not enabled for your wiki or he has
a non-working e-mail address in his profile), you can also set a password for
him::

    moin account-password --name JoeDoe --password uIkV9.-a3

Choose a rather complicated password to make sure they change it a minute
afterwards (to another, hopefully safe password).


Resetting many or all password(s)
=================================
If you have a lot of passwords to reset, you need a better procedure that
avoids having to deal with too many users individually.


Preparing your users
--------------------
Tell your users beforehands that you will be doing a password reset, otherwise
they might find the automatically generated E-Mail they'll get suspicious and
you'll have to explain it to them individually that the E-Mail is legitimate.

Also, remind your users that having a valid E-Mail address in their user
settings is essential for getting a password recovery E-Mail.

If an active user does somehow not get such a mail, you likely will have to
manually define a valid E-Mail address (or even password) for that user.


Make sure E-Mail functionality works
------------------------------------
If you know you have working E-Mail functionality, skip this section.

Password recovery and password reset notification work via E-Mail, so you
should have it configured::

    # the E-Mail address used for From: (consider using an address that
    # can be directly replied to, at least while doing the pw reset):
    mail_from = 'wiki@example.org'
    # your smtp mail server hostname:port (default is 25)
    mail_smarthost = 'mail.example.org:587'
    # the login there, if authentication is needed
    mail_username = 'wiki@example.org'
    mail_password = 'SuperSecretSMTPPassword'

You can try whether it works by using the "forgot my password" functionality
on the login page.


Editing mailtemplate.txt
------------------------
If you edit mailtemplate.txt, please be very careful and follow these rules
(otherwise you might just see the script command crashing):

The contents must be utf-8 (or ascii, which is a subset of utf-8).
In case of doubt, just use plain English.

Some places you likely should edit are marked with XXX.

Do not use any % character in your text (except for the placeholders).
If you need a verbatim % character, you need to write %%.

It is a very good idea to give some URL (e.g. of a web or wiki page) in
the text where users can read more information.

Of course the information at that URL should be readable without requiring
a wiki login (you just have invalidated his/her password!), so the user can
get informed before clicking links he got from someone via E-Mail.

We have added a wikitemplate.txt you can use to create such a wiki page.

Instead of creating a web or wiki page with the information, you could
also write all the stuff into the mail template directly, but please consider
that E-Mail delivery to some users might fail for misc. reasons, so having
some information on the web/wiki is usually better.


Editing wikitemplate.txt
------------------------
Just copy & paste it to some public page in your wiki, e.g. "PasswordReset".

Some places you likely should edit are marked with XXX.


Doing the password reset
------------------------
Maybe first try it with a single user account::

    moin account-password --name JoeDoe --notify --subject 'Wiki password reset' --text-from-file mailtemplate.txt

Use some valid name, maybe a testing account of yourself. You should now have
mail. If that worked ok, you can now do a global password reset for your wiki::

    moin account-password --verbose --all-users --notify --subject 'Wiki password reset' --text-from-file mailtemplate.txt

The subject may contain a placeholder for the sitename, which is useful for
wiki farms (showing the builtin default here)::

    '[%(sitename)s] Your wiki account data'
