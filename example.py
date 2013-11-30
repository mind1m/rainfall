from hurricane import Application, HTTPHandler


class HelloHandler(HTTPHandler):
    def handler(self, request):
        return self.render("Hello World!!")


test = Application({
    '/': HelloHandler(),
})
test.run()