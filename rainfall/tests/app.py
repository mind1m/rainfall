import os
import asyncio

from rainfall.web import Application, HTTPHandler, WSHandler
from rainfall.http import HTTPError


class HelloHandler(HTTPHandler):

    def handle(self, request):
        return 'Hello!'


class TemplateHandler(HTTPHandler):

    def handle(self, request):
        return self.render('base.html', text='Rendered')


class HTTPErrorHandler(HTTPHandler):

    def handle(self, request):
        return HTTPError(403)


class ExceptionHandler(HTTPHandler):

    def handle(self, request):
        raise Exception('Fail')


class SleepHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request):

        yield from asyncio.sleep(0.1)
        return 'Done'


class ParamHandler(HTTPHandler):

    def handle(self, request, number):
        return number


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


class EtagHandler(HTTPHandler):

    use_etag = True
    payload = "PowerOfYourHeart"

    def handle(self, request):
        return self.payload


class EchoWSHandler(WSHandler):

    @asyncio.coroutine
    def on_message(self, message):
        yield from self.send_message(message)


settings = {
    'template_path': os.path.join(os.path.dirname(__file__), "templates"),
    'host': '127.0.0.1',
}

app = Application(
    {
        r'^/$': HelloHandler,
        r'^/template$': TemplateHandler,

        r'^/http_error$': HTTPErrorHandler,
        r'^/exc_error$': ExceptionHandler,

        r'^/sleep$': SleepHandler,

        r'^/param/(?P<number>\d+)$': ParamHandler,

        r'^/forms/get$': GetFormHandler,
        r'^/forms/post$': PostFormHandler,

        r'^/etag$': EtagHandler,

        r'^/ws$': EchoWSHandler,
    },
    settings=settings,
)

if __name__ == '__main__':
    app.run()
