import os
import asyncio

from hurricane.web import Application, HTTPHandler
from hurricane.http import HTTPError


class HelloHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request):
        return self.render('base.html')


class BenchHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request):
        return 'Hello!'


class ExceptionHandler(HTTPHandler):
    def handle(self, request):
        return HTTPError(403)


class IncNumberHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request, number):
        number = int(number)
        return self.render('base.html', number=number)


class GetFormHandler(HTTPHandler):
    def handle(self, request):
        data = {}
        if request.GET:
            data = request.GET
        return self.render('form.html', method='GET', data=data)


class PostFormHandler(HTTPHandler):
    def handle(self, request):
        data = {}
        if request.POST:
            data = request.POST
        return self.render('form.html', method='POST', data=data)


settings = {
    'template_path': os.path.join(os.path.dirname(__file__), "templates"),
}
app = Application(
    {
        r'^/$': HelloHandler(),
        r'^/exc$': ExceptionHandler(),
        r'^/bench$': BenchHandler(),
        r'^/inc/(?P<number>\d+)$': IncNumberHandler(),
        r'^/forms/get$': GetFormHandler(),
        r'^/forms/post$': PostFormHandler(),
    },
    settings=settings,
)
app.run()