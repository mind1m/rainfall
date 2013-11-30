#!/usr/bin/env python3
import asyncio
import signal
import jinja2
import datetime
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


class HTTPHandler(object):

    def handler(self, request):
        raise NotImplementedError()

    def render(self, text, **kwargs):
        result = ''
        if kwargs:
            template = jinja2.Template(text)
            result = template.render(kwargs)
        return result or text

    def __call__(self, request):
        response = HTTPResponse(code=200)
        body = self.handler(request)
        if body:
            response.body = body
        return response


class HTTPServer(asyncio.Protocol):

    TIMEOUT = 5.0
    _handlers = {}

    def timeout(self):
        #print('connection timeout, closing.')
        self.transport.close()

    def connection_made(self, transport):
        self.transport = transport

        # start 5 seconds timeout timer
        self.h_timeout = asyncio.get_event_loop().call_later(
            self.TIMEOUT, self.timeout
        )

    def data_received(self, data):
        decoded_data = data.decode()
        request = HTTPRequest(decoded_data)

        response = None
        # TODO: regex here
        if request.path in self._handlers:
            response = self._handlers[request.path](request)
        else:
            response = HTTPResponse(code=404)
        
        self.transport.write(response.compose().encode())

        self.transport.close()
        self.h_timeout.cancel()

        print(datetime.datetime.now(), request.method, request.path, response.code)

    def connection_lost(self, exc):
        self.h_timeout.cancel()


class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


class Application(object):
    def __init__(self, handlers):
        self._handlers = handlers
        HTTPServer._handlers = handlers

    def run(self, host='127.0.0.1', port='8888'):
        loop = asyncio.get_event_loop()
        if signal is not None:
            loop.add_signal_handler(signal.SIGINT, loop.stop)

        self._start_server(loop, host, port)

        loop.run_forever()

    def _start_server(self, loop, host, port):
        f = loop.create_server(HTTPServer, host, port)
        s = loop.run_until_complete(f)
        self.greet(s.sockets[0].getsockname())

    def greet(self, sock_name):
        print(
            TerminalColors.OKGREEN, '\nStarting Hurricane...\n', 
            # TerminalColors.OKBLUE,  '\nBrace yourself\n\n',
            TerminalColors.ENDC, '\nServing on ', sock_name,
        )
