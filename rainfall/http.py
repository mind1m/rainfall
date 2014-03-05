import io
import email
import asyncio

from urllib import parse
from email.utils import formatdate
from http import client
from websockets.http import read_line

from .utils import RainfallException


MAX_HEADERS = 256
USER_AGENT = 'rainfall/python'

@asyncio.coroutine
def read_message(stream):
    """
    Read an HTTP message from `stream`.
    Return `(start_line, headers, body)` where `start_line` is :class:`bytes`.
    `headers` is a :class:`~email.message.Message` and body is :class:`str`.

    Copy of websocket.http.read_message with body support.
    """
    start_line = yield from read_line(stream)
    header_lines = io.BytesIO()
    for num in range(MAX_HEADERS):
        header_line = yield from read_line(stream)
        header_lines.write(header_line)
        if header_line == b'\r\n':
            break
    else:
        raise ValueError("Too many headers")
    header_lines.seek(0)
    headers = email.parser.BytesHeaderParser().parse(header_lines)

    # there's not EOF in case of POST, so using read() here
    content_length = int(headers.get('Content-Length', 0))
    body = yield from stream.read(content_length)
    body = body.decode("utf-8")

    return start_line, headers, body


@asyncio.coroutine
def read_request(stream):
    """
    Read an HTTP/1.1 request from `stream`.

    Return `(method, uri, headers, body)` `uri` isn't URL-decoded.

    Raise an exception if the request isn't well formatted.

    Copy of websocket.http.read_request with body support.
    """
    request_line, headers, body = yield from read_message(stream)
    method, uri, version = request_line[:-2].decode().split(None, 2)
    return method, uri, headers, body


class HTTPRequest(object):
    """
    Rainfall implementation of the http request.

    :param raw: raw text of full http request
    """
    def __init__(self, method, path, headers=None, body=None):
        self.headers = headers or {}
        self.body = body or ''
        self.method = method or ''
        self.path = path or ''
        self.__GET = {}
        self.__POST = {}

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

    _default_headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Server': USER_AGENT,
    }

    def __init__(self, code=client.OK, headers=None, body=None):
        self.body = body or ''
        self.code = code
        self.headers = headers or {}
        self.additional_headers = None

    def compose(self):
        """
        Composes http response from code, headers and body

        :rtype: str, composed http response
        """
        header = 'HTTP/1.1 {code} {name}\r\n'.format(
            code=self.code, name=client.responses[self.code]
        )
        self.headers.update(self._default_headers)
        self.headers.update(
            Date=formatdate(timeval=None, localtime=False, usegmt=True)
        )
        if self.additional_headers:
            self.headers.update(self.additional_headers)
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
