# -*- coding: utf-8 -*-
import re
import sys
import signal
import asyncio
import hashlib
import traceback
import logging

from http import client
from jinja2 import Environment, FileSystemLoader

from .utils import TerminalColors, RainfallException, NotModified
from .http import HTTPResponse, HTTPRequest, HTTPError


class HTTPHandler(object):
    """
    Used by HTTPServer to react for some url pattern.

    All handling happens in handle method.
    """

    use_etag = True

    def __init__(self):
        self._headers = {}

    def set_header(self, header_name, header_value):
        """
        Set (or unset) a particular header for response
        :param header_name: Name of header to set
        :param header_value: Value of header to set; if None, unsets header
        """
        if header_value is not None:
            self._headers[header_name] = header_value
        elif header_name in self._headers:
            del self._headers[header_name]

    @asyncio.coroutine
    def handle(self, request, **kwargs):
        """
        May be an asyncio.coroutine or a regular function

        :param request: :class:`rainfall.http.HTTPRequest`
        :param kwargs: arguments from url if any

        :rtype: str (may be rendered with self.render()) or :class:`rainfall.http.HTTPError`
        """
        raise NotImplementedError

    def render(self, template_name, **kwargs):
        """
        Uses jinja2 to render a template

        :param template_name: what file to render
        :param kwargs: arguments to pass to jinja's render

        :rtype: rendered string
        """
        template = HTTPServer._jinja_env.get_template(template_name)
        result = template.render(kwargs)
        return result

    @asyncio.coroutine
    def __call__(self, request, **kwargs):
        """
        Is called by :class:`rainfall.web.HTTPServer`

        :rtype: (code, body)
        """
        code = 200
        body = ''
        # this check is taken form asyncio sources
        if getattr(self.handle, '_is_coroutine', False):
            handler_result = yield from self.handle(request, **kwargs)
        else:
            handler_result = self.handle(request, **kwargs)

        if handler_result:
            if isinstance(handler_result, HTTPError):
                code = handler_result.code
            elif isinstance(handler_result, str):
                body = handler_result
                if self.use_etag:
                    etag_value = '"' + hashlib.sha1(body.encode('utf-8')).hexdigest() + '"'
                    self.set_header('ETag', etag_value)
                    if request.headers.get('If-None-Match') == etag_value:
                        raise NotModified(self._headers)
            else:
                raise RainfallException(
                    "handle() result must be rainfall.web.HTTPServer or str, found {}".format(
                        type(handler_result)
                    )
                )
        return code, self._headers, body


class HTTPServer(asyncio.Protocol):
    """
    Http server itself, uses asyncio.Protocol.
    Not meant to be created manually, but by `rainfall.web.Application` class.
    """
    TIMEOUT = 5.0
    _handlers = {}
    _static_path = ''
    _jinja_env = ''

    def timeout(self):
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
        path = request.path.split('?')[0]  # stripping GET params
        exc = None

        response = HTTPResponse()
        for pattern, handler in self._handlers.items():
            result = re.match(pattern, path)
            if result:
                try:
                    code, headers, body = yield from handler(
                        request, **result.groupdict()
                    )
                    response.additional_headers = headers
                    response.code = code
                    response.body = body
                except NotModified as e:
                    response.code = 304
                    response.additional_headers = e.args[0]
                except Exception as e:
                    response.code = client.INTERNAL_SERVER_ERROR
                    exc = sys.exc_info()
                finally:
                    break
        else:
            response.code = client.NOT_FOUND

        if response.code != 200:
            response.body = "<h1>{} {}</h1>".format(
                response.code, client.responses[response.code]
            )
        elif response.code == 304:
            response.body = ""

        self.transport.write(response.compose().encode())
        logging.info('{} {} {}'.format(
            request.method, request.path, response.code)
        )

        if exc:
            logging.error(''.join(traceback.format_exception(*exc)))

    def connection_lost(self, exc):
        self.h_timeout.cancel()


class Application(object):
    """
    The core class that is used to create and start server

    :param handlers: dict with url keys and HTTPHandler instance values
    :param settings: dict of app settings, defaults are
        settings = {
            'host': '127.0.0.1',
            'port': 8888,
            'logfile_path': None,
            'template_path': None,
        }

    Example::

        app = Application({
            '/': HelloHandler(),
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

        HTTPServer._jinja_env = Environment(
            loader=FileSystemLoader(self.settings.get('template_path', ''))
        )
        HTTPServer._handlers = handlers

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
        f = loop.create_server(HTTPServer, host, port)
        s = loop.run_until_complete(f)

    def _greet(self, sock_name, logfile_path):
        # works with print only
        print(
            TerminalColors.LIGHTBLUE, '\nRainfall is starting...', '\u2602 ',
            TerminalColors.NORMAL, '\nServing on', sock_name, '\n'
        )
        if logfile_path:
            print('Logging set to {}'.format(logfile_path))
