from hurricane import Application, HTTPHandler
import asyncio

class HelloHandler(HTTPHandler):
    # @asyncio.coroutine
    def handler(self, request):
        return self.render("Hello World!!")


test = Application({
    '/': HelloHandler(),
})
test.run()