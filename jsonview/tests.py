import json

from django import http
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.views.decorators.http import require_POST

import mock

from .decorators import json_view
from .exceptions import BadRequest


JSON = 'application/json'
rf = RequestFactory()


def eq_(a, b, msg=None):
    """From nose.tools.eq_."""
    assert a == b, msg or '%r != %r' % (a, b)


class JsonViewTests(TestCase):
    def test_object(self):
        data = {
            'foo': 'bar',
            'baz': 'qux',
            'quz': [{'foo': 'bar'}],
        }
        expect = json.dumps(data)

        @json_view
        def temp(req):
            return data

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(expect, res.content)
        eq_(JSON, res['content-type'])

    def test_list(self):
        data = ['foo', 'bar', 'baz']
        expect = json.dumps(data)

        @json_view
        def temp(req):
            return data

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(expect, res.content)
        eq_(JSON, res['content-type'])

    def test_404(self):
        @json_view
        def temp(req):
            raise http.Http404('foo')

        res = temp(rf.get('/'))
        eq_(404, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content)
        eq_(404, data['error'])
        eq_('foo', data['message'])

    def test_permission(self):
        @json_view
        def temp(req):
            raise PermissionDenied('bar')

        res = temp(rf.get('/'))
        eq_(403, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content)
        eq_(403, data['error'])
        eq_('bar', data['message'])

    def test_bad_request(self):
        @json_view
        def temp(req):
            raise BadRequest('baz')

        res = temp(rf.get('/'))
        eq_(400, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content)
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
        data = json.loads(res.content)
        eq_(405, data['error'])

    def test_server_error(self):
        @json_view
        def temp(req):
            raise TypeError('fail')

        res = temp(rf.get('/'))
        eq_(500, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content)
        eq_(500, data['error'])
        eq_('fail', data['message'])

    def test_http_status(self):
        @json_view
        def temp(req):
            return {}, 402
        res = temp(rf.get('/'))
        eq_(402, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content)
        eq_({}, data)

    def test_headers(self):
        @json_view
        def temp(req):
            return {}, 302, {'X-Foo': 'Bar'}
        res = temp(rf.get('/'))
        eq_(302, res.status_code)
        eq_(JSON, res['content-type'])
        eq_('Bar', res['X-Foo'])
        data = json.loads(res.content)
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
            raise http.Http404(u'page \xe7\xe9 not found')

        res = temp(rf.get(u'/\xe7\xe9'))
        eq_(404, res.status_code)
        data = json.loads(res.content)
        assert u'\xe7\xe9' in data['message']
