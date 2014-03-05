# -*- coding: utf-8 -*-
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


class HTTPHandler:

    """
    Used by RainfallProtocol to react for some url pattern.

    All handling happens in handle method.
    """

    use_etag = True

    def __init__(self, settings=None):
        self.settings = settings or {}
        self._headers = {}

    @asyncio.coroutine
    def handle(self, request, **kwargs):
        """
        May be an asyncio.coroutine or a regular function

        :param request: :class:`rainfall.http.HTTPRequest`
        :param kwargs: arguments from url if any

        :rtype: str (may be rendered with self.render()) or :class:`rainfall.http.HTTPError`
        """
        raise NotImplementedError

    def set_header(self, header_name, header_value=None):
        """
        Set (and unset) a particular header for response

        :param header_name: Name of header to set
        :param header_value: Value of header to set; If None, unsets header.
        """
        if header_value is not None:
            self._headers[header_name] = header_value
        elif header_name in self._headers:
            del self._headers[header_name]

    def render(self, template_name, **kwargs):
        """
        Uses jinja2 to render a template

        :param template_name: what file to render
        :param kwargs: arguments to pass to jinja's render

        :rtype: rendered string
        """
        template = self.settings['jinja_env'].get_template(template_name)
        result = template.render(kwargs)
        return result

    @asyncio.coroutine
    def __call__(self, request, **kwargs):
        """
        Is called by :class:`rainfall.web.RainfallProtocol`

        :rtype: (code, headers, body)
        """
        code = 200
        body = ''

        handler_result = yield from maybe_yield(self.handle, request, **kwargs)

        if isinstance(handler_result, HTTPError):
            code = handler_result.code
        elif isinstance(handler_result, str):
            body = handler_result
            if self.use_etag:
                etag_value = '"' + \
                    hashlib.sha1(body.encode('utf-8')).hexdigest() + '"'
                self.set_header('ETag', etag_value)
                if request.headers.get('If-None-Match') == etag_value:
                    raise NotModified(self._headers)
        else:
            raise RainfallException(
                "handle() result must be rainfall.http.HttpError or str, found {}".format(
                    type(handler_result)
                )
            )
        return code, self._headers, body


class WSHandler:
    """
    Used by RainfallProtocol to react for websocket url pattern.
    """

    def __init__(self, protocol):
        self.protocol = protocol

    def send_message(self, message):
        """
        Send a :param message to websocket
        """
        self.protocol.send(message)

    @asyncio.coroutine
    def on_open(self):
        """
        Is called when websocket is opened.
        """
        pass

    @asyncio.coroutine
    def on_close(self):
        """
        Is called when websocket is closed.
        """
        pass

    @asyncio.coroutine
    def on_message(self, message):
        """
        Is called when message is receieved in websocket
        """
        pass

    @asyncio.coroutine
    def _check_messages(self):
        while True:
            msg = yield from self.protocol.recv()

            if not msg:
                # that's all folks
                return
            yield from maybe_yield(self.on_message, msg)
