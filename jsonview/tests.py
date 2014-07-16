from __future__ import unicode_literals
import json
import sys

from django import http
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.views.decorators.http import require_POST

import mock

from .decorators import json_view
from .exceptions import BadRequest


JSON = 'application/json'
rf = RequestFactory()


def eq_(a, b, msg=None):
    """From nose.tools.eq_."""
    assert a == b, msg or '%r != %r' % (a, b)

if sys.version < '3':
    def b(x):
        return x
else:
    import codecs

    def b(x):
        return codecs.latin_1_encode(x)[0]


class JsonViewTests(TestCase):
    def test_object(self):
        data = {
            'foo': 'bar',
            'baz': 'qux',
            'quz': [{'foo': 'bar'}],
        }

        @json_view
        def temp(req):
            return data

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(data, json.loads(res.content.decode('utf-8')))
        eq_(JSON, res['content-type'])

    def test_list(self):
        data = ['foo', 'bar', 'baz']

        @json_view
        def temp(req):
            return data

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(data, json.loads(res.content.decode('utf-8')))
        eq_(JSON, res['content-type'])

    def test_404(self):
        @json_view
        def temp(req):
            raise http.Http404('foo')

        res = temp(rf.get('/'))
        eq_(404, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_(404, data['error'])
        eq_('foo', data['message'])

    def test_permission(self):
        @json_view
        def temp(req):
            raise PermissionDenied('bar')

        res = temp(rf.get('/'))
        eq_(403, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_(403, data['error'])
        eq_('bar', data['message'])

    def test_bad_request(self):
        @json_view
        def temp(req):
            raise BadRequest('baz')

        res = temp(rf.get('/'))
        eq_(400, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_(400, data['error'])
        eq_('baz', data['message'])

    def test_not_allowed(self):
        @json_view
        @require_POST
        def temp(req):
            return {}

        res = temp(rf.get('/'))
        eq_(405, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_(405, data['error'])

        res = temp(rf.post('/'))
        eq_(200, res.status_code)

    @override_settings(DEBUG=True)
    def test_server_error_debug(self):
        @json_view
        def temp(req):
            raise TypeError('fail')

        res = temp(rf.get('/'))
        eq_(500, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_(500, data['error'])
        eq_('fail', data['message'])

    @override_settings(DEBUG=False)
    def test_server_error_no_debug(self):
        @json_view
        def temp(req):
            raise TypeError('fail')

        res = temp(rf.get('/'))
        eq_(500, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_(500, data['error'])
        eq_('An error occurred', data['message'])

    def test_http_status(self):
        @json_view
        def temp(req):
            return {}, 402
        res = temp(rf.get('/'))
        eq_(402, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_({}, data)

    def test_headers(self):
        @json_view
        def temp(req):
            return {}, 302, {'X-Foo': 'Bar'}
        res = temp(rf.get('/'))
        eq_(302, res.status_code)
        eq_(JSON, res['content-type'])
        eq_('Bar', res['X-Foo'])
        data = json.loads(res.content.decode('utf-8'))
        eq_({}, data)

    def test_signal_sent(self):
        from . import decorators

        @json_view
        def temp(req):
            [][0]  # sic.

        with mock.patch.object(decorators, 'got_request_exception') as s:
            res = temp(rf.get('/'))

        assert s.send.called
        eq_(JSON, res['content-type'])

    def test_unicode_error(self):
        @json_view
        def temp(req):
            raise http.Http404('page \xe7\xe9 not found')

        res = temp(rf.get('/\xe7\xe9'))
        eq_(404, res.status_code)
        data = json.loads(res.content.decode('utf-8'))
        assert '\xe7\xe9' in data['message']

    def test_override_content_type(self):
        testtype = 'application/vnd.helloworld+json'
        data = {'foo': 'bar'}

        @json_view(content_type=testtype)
        def temp(req):
            return data

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(data, json.loads(res.content.decode('utf-8')))
        eq_(testtype, res['content-type'])

    def test_passthrough_response(self):
        """Allow HttpResponse objects through untouched."""
        payload = json.dumps({'foo': 'bar'}).encode('utf-8')

        @json_view
        def temp(req):
            return http.HttpResponse(payload, content_type='text/plain')

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(payload, res.content)
        eq_('text/plain', res['content-type'])

    def test_datetime(self):
        now = timezone.now()

        @json_view
        def temp(req):
            return {'datetime': now}

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        payload = json.dumps({'datetime': now}, cls=DjangoJSONEncoder)
        eq_(b(payload), res.content)

    @override_settings(JSON_USE_DJANGO_SERIALIZER=False)
    def test_datetime_no_serializer(self):
        now = timezone.now()

        @json_view
        def temp(req):
            return {'datetime': now}

        res = temp(rf.get('/'))
        eq_(500, res.status_code)
        payload = json.loads(res.content.decode('utf-8'))
        eq_(500, payload['error'])
