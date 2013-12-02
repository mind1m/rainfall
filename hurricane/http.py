from email.utils import formatdate


class HTTPRequest(object):

    def __init__(self, raw):
        self.raw = raw

    @property
    def body(self):
        pass

    @property
    def method(self):
        return self.raw.split('\r\n')[0].split(' ')[0]

    @property
    def path(self):
        return self.raw.split('\r\n')[0].split(' ')[1]

    @property
    def headers(self):
        pass


class HTTPResponse(object):

    def __init__(self, body='', code=200, additional_headers={}):
        self.body = body
        self.code = code
        self.headers = {
            'Content-Type': 'text/html; charset=utf-8',
            'Server': 'hurricane/python',
            'Date': formatdate(timeval=None, localtime=False, usegmt=True),
        }
        self.headers.update(additional_headers)

    def compose(self):
        header = 'HTTP/1.1 {code} OK\r\n'.format(code=self.code)
        for head, value in self.headers.items():
            header += '{}: {}\r\n'.format(head, value)
        return '{}\r\n{}'.format(header, self.body)
