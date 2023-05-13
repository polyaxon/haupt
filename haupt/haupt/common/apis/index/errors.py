from django.http import HttpResponse
from django.views.generic import View


class StatusView(View):
    status_code = 200

    def get(self, request, *args, **kwargs):
        return HttpResponse(status=self.status_code)


class Handler404View(StatusView):
    status_code = 404


class Handler50xView(StatusView):
    status_code = 500


class Handler403View(StatusView):
    status_code = 403
