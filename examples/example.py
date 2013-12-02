import os
import asyncio

from hurricane.web import Application, HTTPHandler


class HelloHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request):
        return self.render('base.html')


class BenchHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request):
        return 'Hello!'


class IncNumberHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request, number):
        number = int(number)
        return self.render('base.html', number=number)


settings = {
    'template_path': os.path.join(os.path.dirname(__file__), "templates"),
}
app = Application(
    {
        r'^/$': HelloHandler(),
        r'^/bench$': BenchHandler(),
        r'^/inc/(?P<number>\d+)$': IncNumberHandler(),
    },
    settings=settings,
)
app.run()