import logging
from functools import wraps

from django import http
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.handlers.base import BaseHandler
from django.core.signals import got_request_exception
from django.utils.importlib import import_module

from .exceptions import BadRequest

json = import_module(getattr(settings, 'JSON_MODULE', 'json'))
JSON = 'application/json'
logger = logging.getLogger('django.request')
logger.info('Using %s JSON module.', json.__name__)


def json_view(f):
    """Ensure the response content is well-formed JSON.

    Views wrapped in @json_view can return JSON-serializable Python objects,
    like lists and dicts, and the decorator will serialize the output and set
    the correct Content-type.

    Views may also throw known exceptions, like Http404, PermissionDenied, etc,
    and @json_view will convert the response to a standard JSON error format,
    and set the status code and content type.

    If you return a two item tuple, the first is a JSON-serializable object and
    the second is an integer used for the HTTP status code, e.g.:

    >>> @json_view
    ... def example(request):
    ...    return {'foo': 'bar'}, 418

    """

    @wraps(f)
    def _wrapped(request, *a, **kw):
        try:
            status = 200
            headers = {}
            ret = f(request, *a, **kw)

            if isinstance(ret, tuple):
                if len(ret) == 3:
                    ret, status, headers = ret
                else:
                    ret, status = ret

            # Some errors are not exceptions. :\
            if isinstance(ret, http.HttpResponseNotAllowed):
                blob = json.dumps({
                    'error': 405,
                    'message': 'HTTP method not allowed.'
                })
                return http.HttpResponse(blob, status=405, content_type=JSON)
            blob = json.dumps(ret)
            response = http.HttpResponse(blob, status=status,
                                         content_type=JSON)
            for k in headers:
                response[k] = headers[k]
            return response
        except http.Http404 as e:
            blob = json.dumps({
                'error': 404,
                'message': unicode(e),
            })
            logger.warning('Not found: %s', request.path,
                           extra={
                               'status_code': 404,
                               'request': request,
                           })
            return http.HttpResponseNotFound(blob, content_type=JSON)
        except PermissionDenied as e:
            logger.warning('Forbidden (Permission denied): %s', request.path,
                           extra={
                               'status_code': 403,
                               'request': request,
                           })
            blob = json.dumps({
                'error': 403,
                'message': unicode(e),
            })
            return http.HttpResponseForbidden(blob, content_type=JSON)
        except BadRequest as e:
            blob = json.dumps({
                'error': 400,
                'message': unicode(e),
            })
            return http.HttpResponseBadRequest(blob, content_type=JSON)
        except Exception as e:
            blob = json.dumps({
                'error': 500,
                'message': unicode(e),
            })
            logger.exception(unicode(e))

            # Here we lie a little bit. Because we swallow the exception, the
            # BaseHandler doesn't get to send this signal. It sets the sender
            # argument to self.__class__, in case the BaseHandler is
            # subclassed.
            got_request_exception.send(sender=BaseHandler, request=request)
            return http.HttpResponseServerError(blob, content_type=JSON)
    return _wrapped
