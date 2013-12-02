import asyncio

from hurricane.web import Application, HTTPHandler


class HelloHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request):
        return self.render("Hello World!!")


class IncNumberHandler(HTTPHandler):
    @asyncio.coroutine
    def handle(self, request, number):
        number = int(number)
        return self.render("Number is {}, increased is {}.".format(number, number + 1))


app = Application({
    r'^/$': HelloHandler(),
    r'^/inc/(?P<number>\d+)$': IncNumberHandler(),
})
app.run()