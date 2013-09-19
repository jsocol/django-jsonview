===============
django-jsonview
===============


**django-jsonview** is a simple decorator that translates Python objects
to JSON and makes sure your view will always return JSON.

I've copied and pasted this so often I decided I just wanted to put it
in a package.


Installation
============

Just install with ``pip``::

    pip install django-jsonview

No need to add to ``INSTALLED_APPS`` or anything.


Usage
=====

Just import the decorator, use, and return a JSON-serializable object::

    from jsonview.decorators import json_view

    @json_view
    def my_view(request):
        return {
            'foo': 'bar',
        }


Return Values
-------------

The default case is to serialize your return value and respond with HTTP
200 and a Content-Type of ``application/json``.

The ``@json_view`` decorator will handle many exceptions and other
cases, including:

* ``Http404``
* ``PermissionDenied``
* ``HttpResponseNotAllowed`` (e.g. ``require_GET``, ``require_POST``)
* ``jsonview.exceptions.BadRequest`` (see below)
* Any other exception (logged to ``django.request``).

Any of these exceptions will return the correct status code (i.e., 404,
403, 405, 400, 500) a Content-Type of ``application/json``, and a
response body that looks like::

    json.dumps({
        'error': STATUS_CODE,
        'message': str(exception),
    })


``BadRequest``
--------------

HTTP does not have a great status code for "you submitted a form that
didn't validate," and so Django doesn't support it very well. Most
examples just return 200 OK.

Normally, this is fine. But if you're submitting a form via Ajax, it's
nice to have a distinct status for "OK" and "Nope." The HTTP 400 Bad
Request response is the fallback for issues with a request
not-otherwise-specified, so let's do that.

To cause ``@json_view`` to return a 400, just raise a
``jsonview.exceptions.BadRequest`` with whatever appropriate error
message.


Exceptions
----------

If your view raises an exception, ``@json_view`` will catch the
exception, log it to the normal ``django.request`` logger_, and return a
JSON response with a status of 500 and a body that looks like the
exceptions in the `Return Values`_ section.

.. note::

   Because the ``@json_view`` decorator handles the exception instead of
   propagating it, any exception middleware will **not** be called, and
   any response middleware **will** be called.


Status Codes
------------

If you need to return a different HTTP status code, just return two
values instead of one. The first is your serializable object, the second
is the integer status code::

    @json_view
    def myview(request):
        if not request.user.is_subscribed():
            # Send a 402 Payment Required status.
            return {'subscribed': False}, 402
        # Send a 200 OK.
        return {'subscribed': True}


Extra Headers
-------------

You can add custom headers to the response by returning a tuple of three
values: an object, a status code, and a dictionary of headers.

::

    @json_view
    def myview(request):
        return {}, 200, {'X-Server': 'myserver'}

Custom header values may be overwritten by response middleware.


Alternative JSON Implementations
================================

There is a healthy collection of JSON parsing and generating libraries
out there. By default, it will use the old standby, the stdlib ``json``
module. But, if you'd rather use ujson_, or cjson_ or yajl_, you should
go for it. Just add this to your Django settings::

    JSON_MODULE = 'ujson'

Anything, as long as it's a module that has ``.loads()`` and ``.dumps()``
methods, it.


Contributing
============

`Pull requests`_ and issues_ welcome! I ask two simple things:

* Tests, including the new ones you added, must pass. (See below.)
* The ``flake8`` tool should not return any issues.


Running Tests
-------------

To run the tests, you probably want to create a virtualenv_, then
install Django and Mock with ``pip``::

    pip install Django==${DJANGO_VERSION} mock==1.0.1

Then run the tests with::

    ./run.sh test


.. _logger:
   https://docs.djangoproject.com/en/dev/topics/logging/#django-request
.. _Pull requests: https://github.com/jsocol/django-jsonview/pulls
.. _issues: https://github.com/jsocol/django-jsonview/issues
.. _virtualenv: http://www.virtualenv.org/
