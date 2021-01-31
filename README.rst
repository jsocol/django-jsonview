===============
django-jsonview
===============

**django-jsonview** is a simple decorator that translates Python objects
to JSON and makes sure your view will always return JSON.

.. image:: https://github.com/jsocol/django-jsonview/workflows/test/badge.svg?branch=main
   :target: https://github.com/jsocol/django-jsonview/actions


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


`Class-based views`_ (CBVs) can inherit from JsonView, use Django's
``@method_decorator`` or wrap the output of ``.as_view()``::

    # inherit from JsonView
    from jsonview.views import JsonView


    class MyView(JsonView):
        def get_context_data(self, **kwargs):
            context = super(MyView, self).get_context_data(**kwargs)
            context['my_key'] = 'some value'
            return context

    # or, method decorator
    from django.utils.decorators import method_decorator
    from jsonview.decorators import json_view


    class MyView(View):
        @method_decorator(json_view)
        def dispatch(self, *args, **kwargs):
            return super(MyView, self).dispatch(*args, **kwargs)

    # or, in URLconf

    patterns = [
        url(r'^/my-view/$', json_view(MyView.as_view())),
    ]


Content Types
-------------

If you need to return a content type other than the standard
``application/json``, you can specify that in the decorator with the
``content_type`` argument, for example::

    from jsonview.decorators import json_view

    @json_view(content_type='application/vnd.github+json')
    def myview(request):
        return {'foo': 'bar'}

The response will have the appropriate content type header.


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

.. note::

   As of v0.4, application exceptions do **not** behave this way if
   ``DEBUG = False``. When ``DEBUG = False``, the ``message`` value is
   always ``An error occurred``. When ``DEBUG = True``, the exception
   message is sent back.


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


Raw Return Values
-----------------

To make it possible to cache JSON responses as strings (and because they
aren't JSON serializable anyway) if you return an ``HttpResponse``
object (or subclass) it will be passed through unchanged, e.g.::

    from django import http
    from jsonview.decorators import JSON

    @json_view
    def caching_view(request):
        kached = cache.get('cache-key')
        if kached:
            return http.HttpResponse(kached, content_type=JSON)
        # Assuming something else populates this cache.
        return {'complicated': 'object'}

.. note::

   ``@require_POST`` and the other HTTP method decorators  work by
   *returning* a response, rather than *raising*, an exception, so
   ``HttpResponseNotAllowed`` is handled specially.


Alternative JSON Implementations
================================

There is a healthy collection of JSON parsing and generating libraries
out there. By default, it will use the old standby, the stdlib ``json``
module. But, if you'd rather use ujson_, or cjson_ or yajl_, you should
go for it. Just add this to your Django settings::

    JSON_MODULE = 'ujson'

Anything, as long as it's a module that has ``.loads()`` and ``.dumps()``
methods.


Configuring JSON Output
-----------------------

Additional keyword arguments can be passed to ``json.dumps()`` via the
``JSON_OPTIONS = {}`` Django setting. For example, to pretty-print JSON
output::

    JSON_OPTIONS = {
        'indent': 4,
    }

Or to compactify it::

    JSON_OPTIONS = {
        'separators': (',', ':'),
    }

jsonview uses ``DjangoJSONEncoder`` by default. To use a different JSON
encoder, use the ``cls`` option::

    JSON_OPTIONS = {
        'cls': 'path.to.MyJSONEncoder',
    }

``JSON_OPTIONS['cls']`` may be a dotted string or a ``JSONEncoder``
class.

**If you are using a JSON module that does not support the ``cls``
kwarg**, such as ujson, set the ``cls`` option to ``None``::

    JSON_OPTIONS = {
        'cls': None,
    }

Default value of content-type is 'application/json'. You can change it
via the ``JSON_DEFAULT_CONTENT_TYPE`` Django settings. For example, to
add charset::

   JSON_DEFAULT_CONTENT_TYPE = 'application/json; charset=utf-8'


Atomic Requests
===============

Because ``@json_view`` catches exceptions, the normal Django setting
``ATOMIC_REQUESTS`` does not correctly cause a rollback. This can be
worked around by explicitly setting ``@transaction.atomic`` *below* the
``@json_view`` decorator, e.g.::

    @json_view
    @transaction.atomic
    def my_func(request):
        # ...


Contributing
============

`Pull requests`_ and issues_ welcome! I ask two simple things:

- Tests, including the new ones you added, must pass. (See below.)
- Coverage should not drop below 100. You can install ``coverage`` with
  pip and run ``./run.sh coverage`` to check.
- The ``flake8`` tool should not return any issues.


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
.. _ujson: https://pypi.python.org/pypi/ujson
.. _cjson: https://pypi.python.org/pypi/python-cjson
.. _yajl: https://pypi.python.org/pypi/yajl
.. _Class-based views: https://docs.djangoproject.com/en/1.9/topics/class-based-views/intro/#decorating-class-based-views
