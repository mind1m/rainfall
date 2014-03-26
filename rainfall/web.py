# -*- coding: utf-8 -*-
import re
import io
import email
import sys
import signal
import asyncio
import hashlib
import traceback
import logging

from http import client
from jinja2 import Environment, FileSystemLoader
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import InvalidHandshake
from websockets.handshake import check_request, build_response

from .utils import TerminalColors, RainfallException, NotModified, match_dict_regexp, maybe_yield
from .http import HTTPResponse, HTTPRequest, HTTPError, read_request, USER_AGENT
from .handlers import HTTPHandler, WSHandler


logger = logging.getLogger(__name__)
MAX_HEADERS = 256


class RainfallProtocol(WebSocketServerProtocol):

    """
    This is a subclass of WebSocketServerProtocol with HTTP flavour.
    The idea is following: try to parse websocket handshake, if it goes right,
    use websockets, else - call HTTPHandler.
    """

    _http_handlers = {}
    _ws_handlers = {}
    settings = {}

    def __init__(self):
        self._type = 'WS' # swithes to HTTP if needed
        super().__init__()

    @asyncio.coroutine
    def handler(self):
        """
        Presents the whole protocol flow.
        Copy of WebSocketServerProtocol.handler with HTTP flavour.
        """
        # try to figure out what we have, websockets or http.
        # self._type in changed in self.handshake()
        try:
            method, url, headers, body = yield from self.general_handshake()
        except Exception as exc:
            logger.info("Exception in opening handshake: {}".format(traceback.format_exc()))
            self.writer.write_eof()
            self.writer.close()
            return

        if self._type == 'HTTP':
            # falling to HTTP
            yield from self.process_http(method, url, headers, body)
            self.writer.write_eof()
            self.writer.close()
            return

        # continue with websockets
        ws_handler_cls, _ = match_dict_regexp(self._ws_handlers, url)
        if ws_handler_cls:
            ws_handler = ws_handler_cls(self)
        else:
            yield from self.fail_connection(1011, "No corresponding url found")
            return

        yield from maybe_yield(ws_handler.on_open)

        try:
            yield from ws_handler._check_messages()
        except Exception:
            logger.info("Exception in connection handler", exc_info=True)
            yield from self.fail_connection(1011)
            return

        yield from maybe_yield(ws_handler.on_close)

        try:
            yield from self.close()
        except Exception as exc:
            logger.info("Exception in closing handshake: {}".format(exc))
            self.writer.write_eof()
            self.writer.close()

    @asyncio.coroutine
    def general_handshake(self):
        """
        Try to perform the server side of the opening websocket handshake.
        If it fails, switch self._type to HTTP and return.

        Returns the (method, url, headers, body)

        Copy of WebSocketServerProtocol.handshake with HTTP flavour.
        """
        # Read handshake request.
        try:
            method, url, headers, body = yield from read_request(self.reader)
        except Exception as exc:
            raise HTTPError(code=500) from exc

        get_header = lambda k: headers.get(k, '')
        try:
            key = check_request(get_header)
        except InvalidHandshake:
            self._type = 'HTTP'  # switching to HTTP here
            return (method, url, headers, body)

        # Send handshake response. Since the headers only contain ASCII
        # characters, we can keep this simple.
        response = ['HTTP/1.1 101 Switching Protocols']
        set_header = lambda k, v: response.append('{}: {}'.format(k, v))
        set_header('Server', USER_AGENT)
        build_response(set_header, key)
        response.append('\r\n')
        response = '\r\n'.join(response).encode()
        self.writer.write(response)

        self.state = 'OPEN'
        self.opening_handshake.set_result(True)

        return ('GET', url, None, None)


    @asyncio.coroutine
    def process_http(self, method, url, headers, body):
        request = HTTPRequest(
            method=method, path=url,
            headers=headers, body=body,
        )

        response = None
        path = request.path.split('?')[0]  # stripping GET params
        exc = None

        http_handler_cls, match_result = match_dict_regexp(self._http_handlers, path)
        if http_handler_cls:
            try:
                http_handler = http_handler_cls(self.settings)
                code, headers, body = yield from http_handler(
                    request, **match_result.groupdict()
                )
                response = HTTPResponse(code, headers, body)
            except NotModified as e:
                response = HTTPResponse(304, e.args[0])
            except Exception as e:
                response = HTTPResponse(client.INTERNAL_SERVER_ERROR)
                exc = sys.exc_info()
        else:
            response = HTTPResponse(client.NOT_FOUND)

        if response.code != 200:
            response.body = "<h1>{} {}</h1>".format(
                response.code, client.responses[response.code]
            )

        self.writer.write(response.compose().encode())
        logging.info('{} {} {}'.format(
            request.method, request.path, response.code)
        )

        if exc:
            logging.error(''.join(traceback.format_exception(*exc)))


class Application(object):

    """
    The core class that is used to create and start server

    :param handlers: dict with url keys and HTTPHandler or WSHandler subclasses
    :param settings: dict of app settings, defaults are
        settings = {
            'host': '127.0.0.1',
            'port': 8888,
            'logfile_path': None,
            'template_path': None,
        }

    Example::

        app = Application({
            '/': HelloHandler,
        })
        app.run()

    """

    def __init__(self, handlers, settings=None):
        """
        Creates an Application that can be started or tested
        """
        self.settings = settings or {}

        if not 'host' in self.settings:
            self.settings['host'] = '127.0.0.1'

        if not 'port' in self.settings:
            self.settings['port'] = '8888'

        self.settings['jinja_env'] = Environment(
            loader=FileSystemLoader(self.settings.get('template_path', ''))
        )


        # configure protocol
        RainfallProtocol._http_handlers = {
            url: h for url, h in handlers.items() if issubclass(h, HTTPHandler)}
        RainfallProtocol._ws_handlers = {
            url: h for url, h in handlers.items() if issubclass(h, WSHandler)}
        RainfallProtocol.settings = self.settings.copy()

    def run(self, process_queue=None, greeting=True):
        """
        Starts server on host and port given in settings,
        adds Ctrl-C signal handler.

        :param process_queue: SimpleQueue, used by testing framework
        :param greeting: bool, wheather to print to strout or not
        """
        self.host = self.settings['host']
        self.port = self.settings['port']

        # logging config
        logfile_path = self.settings.get('logfile_path', None)
        if logfile_path:
            logging.basicConfig(
                filename=logfile_path, level=logging.INFO,
                format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p'
            )

        loop = asyncio.get_event_loop()

        if signal is not None:
            loop.add_signal_handler(signal.SIGINT, loop.stop)

        self._start_server(loop, self.host, self.port)

        if process_queue:
            # used in tests for multiprocess communication
            process_queue.put('started')

        if greeting:
            self._greet(self.host + ':' + self.port, logfile_path)

        loop.run_forever()

    def _start_server(self, loop, host, port):
        f = loop.create_server(RainfallProtocol, host, port)
        s = loop.run_until_complete(f)

    def _greet(self, sock_name, logfile_path):
        # works with print only
        print(
            TerminalColors.LIGHTBLUE, '\nRainfall is starting...', '\u2602 ',
            TerminalColors.NORMAL, '\nServing on', sock_name, '\n'
        )
        if logfile_path:
            print('Logging set to {}'.format(logfile_path))
