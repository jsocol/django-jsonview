from __future__ import absolute_import, unicode_literals
import codecs
import json
from unittest import mock

from django import http
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import View

from .decorators import json_view
from .exceptions import BadRequest
from .views import JsonView


JSON = 'application/json'
rf = RequestFactory()


def eq_(a, b, msg=None):
    """From nose.tools.eq_."""
    assert a == b, msg or '%r != %r' % (a, b)


def b(x):
    return codecs.latin_1_encode(x)[0]


class CustomTestEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return o.for_json()
        except AttributeError:
            return super(CustomTestEncoder, self).default(o)


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
        assert 'traceback' in data

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

    @override_settings(DEBUG=True)
    def test_signal_sent_with_propagated_exception(self):
        from django.core.signals import got_request_exception

        def assertion_handler(sender, request, **kwargs):
            for key in ['exception', 'exc_data']:
                assert key in kwargs
            for key in ['error', 'message', 'traceback']:
                assert key in kwargs['exc_data']
            assert isinstance(kwargs['exception'], Exception)

        got_request_exception.connect(assertion_handler)

        @json_view
        def temp(req):
            1/0  # sic.

        temp(rf.get('/'))

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

    @override_settings(JSON_OPTIONS={'cls': None})
    def test_datetime_no_serializer(self):
        now = timezone.now()

        @json_view
        def temp(req):
            return {'datetime': now}

        res = temp(rf.get('/'))
        eq_(500, res.status_code)
        payload = json.loads(res.content.decode('utf-8'))
        eq_(500, payload['error'])

    @override_settings(JSON_OPTIONS={'cls': None})
    def test_dont_mutate_json_settings(self):
        """Don't mutate JSON settings during a request.

        The second request should use the same settings as the first, so we
        should get two 500s in a row.
        """
        now = timezone.now()

        @json_view
        def temp(req):
            return {'datetime': now}

        res = temp(rf.get('/'))
        eq_(500, res.status_code)

        # calling this a second time should still generate a 500 and not
        # use the `DjangoJSONEncoder`
        res2 = temp(rf.get('/'))
        eq_(500, res2.status_code)

    @override_settings(
        JSON_OPTIONS={'cls': 'jsonview.test_jsonview.CustomTestEncoder'})
    def test_json_custom_serializer_string(self):
        payload = json.dumps({'foo': 'Custom JSON'}).encode('utf-8')

        class Obj(object):
            def for_json(self):
                return 'Custom JSON'

        @json_view
        def temp(req):
            return {'foo': Obj()}

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(payload, res.content)

    @override_settings(
        JSON_OPTIONS={'cls': 'jsonview.test_jsonview.CustomTestEncoder'})
    def test_json_custom_serializer_string__no_for_json_function(self):
        payload = json.dumps(
            {"error": 500, "message": "An error occurred"}
        ).encode('utf-8')

        class Obj(object):
            pass

        @json_view
        def temp(req):
            return {'foo': Obj()}

        res = temp(rf.get('/'))
        eq_(500, res.status_code)
        eq_(payload, res.content)

    @override_settings(
        JSON_OPTIONS={'cls': CustomTestEncoder})
    def test_json_custom_serializer_class(self):
        payload = json.dumps({'foo': 'Custom JSON'}).encode('utf-8')

        class Obj(object):
            def for_json(self):
                return 'Custom JSON'

        @json_view
        def temp(req):
            return {'foo': Obj()}

        res = temp(rf.get('/'))
        eq_(200, res.status_code)
        eq_(payload, res.content)

    def test_method_decorator_on_dispatch(self):
        class TV(View):
            @method_decorator(json_view)
            def dispatch(self, *a, **kw):
                return super(TV, self).dispatch(*a, **kw)

            def get(self, request):
                return {'foo': 'bar'}

        view = TV.as_view()
        res = view(rf.get('/'))
        eq_(200, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_('bar', data['foo'])

    def test_method_decorator_on_class(self):
        @method_decorator(json_view, name='dispatch')
        class TV(View):
            def get(self, request):
                return {'foo': 'bar'}

        view = TV.as_view()
        res = view(rf.get('/'))
        eq_(200, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_('bar', data['foo'])

    def test_view_class_get(self):
        class MyView(JsonView):
            def get_context_data(self, **kwargs):
                context = super(MyView, self).get_context_data(**kwargs)
                context['foo'] = 'bar'
                return context

        view = MyView.as_view()

        res = view(rf.get('/'))
        eq_(200, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_('bar', data['foo'])

    def test_view_class_post(self):
        class MyView(JsonView):
            def post(self, request, *args, **kwargs):
                return self.get(request, *args, **kwargs)

        view = MyView.as_view()

        res = view(rf.post('/'))
        eq_(200, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_({}, data)

    def test_wrap_as_view(self):
        class TV(View):
            def get(self, request):
                return {'foo': 'bar'}

        view = json_view(TV.as_view())
        res = view(rf.get('/'))
        eq_(200, res.status_code)
        eq_(JSON, res['content-type'])
        data = json.loads(res.content.decode('utf-8'))
        eq_('bar', data['foo'])
