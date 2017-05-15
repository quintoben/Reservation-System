# Reservation

This is a full featured web-based application, one that implements akin to Open Table, where instead of just having restaurants, users can add any "resource" that is reservable (e.g. classroom, library book, car share, video game, etc).

(1)It is written in Python and deployed with App Engine.
(2)It stores data in Google App Engine's  data store  (NDB). It renders HTML with templates, preferably Jinja2.

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [NDB Datastore API][3]
- [Users API][4]

## Dependencies
- [webapp2][5]
- [jinja2][6]
- [Twitter Bootstrap][7]

[1]: https://developers.google.com/appengine
[2]: https://python.org
[3]: https://developers.google.com/appengine/docs/python/ndb/
[4]: https://developers.google.com/appengine/docs/python/users/
[5]: http://webapp-improved.appspot.com/
[6]: http://jinja.pocoo.org/docs/
[7]: http://twitter.github.com/bootstrap/

 GAE_PROJECT=your-project-id
     make

To manually run, install the requirements

    pip install -r e2e/requirements-dev.txt

Set the environment variable to point to your deployed app:

    export GUESTBOOK_URL="http://guestbook-test-dot-useful-temple-118922.appspot.com/"

Finally, run the test

    python e2e/test_e2e.py
