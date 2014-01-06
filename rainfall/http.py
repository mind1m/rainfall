from urllib import parse
from email.utils import formatdate
from http import client

from .utils import RainfallException


class HTTPRequest(object):
    """
    Rainfall implementation of the http request.

    :param raw: raw text of full http request
    """
    def __init__(self, raw):
        self.raw = raw
        self.__headers = {}
        self.__body = ''
        self.__method = ''
        self.__path = ''
        self.__GET = {}
        self.__POST = {}

    @property
    def body(self):
        """
        :rtype: str, http body
        """
        if not self.__body:
            self.__body = self.raw.split('\r\n\r\n')[1]
        return self.__body

    @property
    def method(self):
        """
        :rtype: str, http method
        """
        if not self.__method:
            self.__method = self.raw.split('\r\n')[0].split(' ')[0]
        return self.__method

    @property
    def path(self):
        """
        :rtype: str, http url
        """
        if not self.__path:
            self.__path = self.raw.split('\r\n')[0].split(' ')[1]
        return self.__path

    @property
    def headers(self):
        """
        :rtype: dict, http headers
        """
        if not self.__headers:
            raw_headers = self.raw.split('\r\n\r\n')[0].split('\r\n')
            # skipping first line with path and method
            raw_headers = raw_headers[1:]
            for raw_header in raw_headers:
                parts = raw_header.split(':')
                self.__headers[parts[0].strip()] = parts[1].strip()
        return self.__headers

    @property
    def POST(self):
        """
        :rtype: dict, POST arguments
        """
        if not self.__POST and self.method == 'POST':
            self.__POST = parse.parse_qs(self.body)
            for k, v in self.__POST.items():
                self.__POST[k] = v[0]
        return self.__POST

    @property
    def GET(self):
        """
        :rtype: dict, GET arguments
        """
        if not self.__GET and self.method == 'GET' and len(self.path.split('?')) == 2:
            self.__GET = parse.parse_qs(self.path.split('?')[1])
            for k, v in self.__GET.items():
                self.__GET[k] = v[0]
        return self.__GET


class HTTPResponse(object):
    """
    Rainfall implementation of the http response.

    :param body: response body
    :param code: response code
    :param additional_headers:
    """
    def __init__(self, body='', code=client.OK, additional_headers=None):
        self.body = body
        self.code = code
        self.headers = {
            'Content-Type': 'text/html; charset=utf-8',
            'Server': 'rainfall/python',
            'Date': formatdate(timeval=None, localtime=False, usegmt=True),
        }
        if additional_headers:
            self.headers.update(additional_headers)

    def compose(self):
        """
        Composes http response from code, headers and body

        :rtype: str, composed http response
        """
        header = 'HTTP/1.1 {code} {name}\r\n'.format(
            code=self.code, name=client.responses[self.code]
        )
        for head, value in self.headers.items():
            header += '{}: {}\r\n'.format(head, value)
        return '{}\r\n{}'.format(header, self.body)


class HTTPError(RainfallException):
    """
    Representes different http errors that you can return in handlers.

    :param code: http error code
    """
    def __init__(self, code=client.INTERNAL_SERVER_ERROR, *args, **kwargs):
        self.code = code
        super().__init__(*args, **kwargs)
