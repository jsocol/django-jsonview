import json
import logging
from functools import wraps

from django import http
from django.core.exceptions import PermissionDenied
from django.core.signals import got_request_exception

from .exceptions import BadRequest


JSON = 'application/json'
logger = logging.getLogger('django.request')


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
    >>> def example(request):
    >>>    return {'foo': 'bar'}, 418

    """

    @wraps(f)
    def _wrapped(req, *a, **kw):
        try:
            status = 200
            headers = {}
            ret = f(req, *a, **kw)

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
            res = http.HttpResponse(blob, status=status, content_type=JSON)
            for k in headers:
                res[k] = headers[k]
            return res
        except http.Http404 as e:
            blob = json.dumps({
                'error': 404,
                'message': str(e),
            })
            return http.HttpResponseNotFound(blob, content_type=JSON)
        except http.HttpResponseNotAllowed as e:
            blob = json.dumps({
                'error': 405,
                'message': str(e),
            })
            return http.HttpResponseNotAllowed(blob, content_type=JSON)
        except PermissionDenied as e:
            blob = json.dumps({
                'error': 403,
                'message': str(e),
            })
            return http.HttpResponseForbidden(blob, content_type=JSON)
        except BadRequest as e:
            blob = json.dumps({
                'error': 400,
                'message': str(e),
            })
            return http.HttpResponseBadRequest(blob, content_type=JSON)
        except Exception as e:
            blob = json.dumps({
                'error': 500,
                'message': str(e),
            })
            logger.exception(str(e))
            return http.HttpResponseServerError(blob, content_type=JSON)
    return _wrapped
