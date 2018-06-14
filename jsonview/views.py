from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import ContextMixin

from jsonview.decorators import json_view


class JsonView(ContextMixin, View):

    def get_context_data(self, **kwargs):
        return {}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return context

    @method_decorator(json_view)
    def dispatch(self, *args, **kwargs):
        return super(JsonView, self).dispatch(*args, **kwargs)
