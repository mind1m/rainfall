# -*- coding: utf-8 -*-
import asyncio
import signal
import jinja2
import datetime

from .utils import TerminalColors
from .http import HTTPResponse, HTTPRequest


class HTTPHandler(object):

    @asyncio.coroutine
    def handle(self, request):
        raise NotImplementedError

    def render(self, text, **kwargs):
        result = ''
        if kwargs:
            template = jinja2.Template(text)
            result = template.render(kwargs)
        return result or text

    @asyncio.coroutine
    def __call__(self, request):
        response = HTTPResponse(code=200)
        if getattr(self.handle, '_is_coroutine', False):
            body = yield from self.handle(request)
        else:
            body = self.handle(request)
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
        task = asyncio.Task(self._call_handler(request))
        task.add_done_callback(self._finalize_request)

    def _finalize_request(self, *args, **kwargs):
        self.transport.close()
        self.h_timeout.cancel()

    @asyncio.coroutine
    def _call_handler(self, request):
        response = None
        # TODO: regex here
        if request.path in self._handlers:
            response = yield from self._handlers[request.path](request)
        else:
            response = HTTPResponse(code=404)
        self.transport.write(response.compose().encode())
        print(datetime.datetime.now(), request.method, request.path, response.code)

    def connection_lost(self, exc):
        self.h_timeout.cancel()


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
        self._greet(s.sockets[0].getsockname())

    def _greet(self, sock_name):
        print(
            TerminalColors.GREEN, '\nHurricane is starting...',TerminalColors.WHITE,'\n',
            """
        ( ~~~~)
       (~      ~~~)
      (~          ~~)
      ( ~~~~~~~~~~~)
        """, TerminalColors.LIGHTBLUE,
        """
         \ \ \ \ \ \\
          \ \ \ \ \ \\
           ` ` ` ` ` `

            """,
            # TerminalColors.OKBLUE,  '\nBrace yourself\n\n',
            TerminalColors.NORMAL, '\nServing on', sock_name, ':'
        )
