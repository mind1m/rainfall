from email.utils import formatdate
from http import client

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

    def __init__(self, body='', code=client.OK, additional_headers={}):
        self.body = body
        self.code = code
        self.headers = {
            'Content-Type': 'text/html; charset=utf-8',
            'Server': 'hurricane/python',
            'Date': formatdate(timeval=None, localtime=False, usegmt=True),
        }
        self.headers.update(additional_headers)

    def compose(self):
        header = 'HTTP/1.1 {code} {name}\r\n'.format(code=self.code, name=client.responses[self.code])
        for head, value in self.headers.items():
            header += '{}: {}\r\n'.format(head, value)
        return '{}\r\n{}'.format(header, self.body)
