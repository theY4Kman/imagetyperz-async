from typing import Generator
from urllib.parse import parse_qsl, urlencode

import httpx
from httpx._content import encode_request


class TokenDataAuth(httpx.Auth):
    """Pass an access token in a POST body, or as a GET param"""

    ###
    # Since this auth scheme mutates POST bodies to introduce the token, we
    # require access to the body.
    #
    # Ref: https://www.python-httpx.org/advanced/#customizing-authentication
    #
    requires_request_body = True

    def __init__(self, access_token: str):
        self.access_token = access_token

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        if request.method == 'POST':
            self.add_token_to_post_body(request)
        elif request.method == 'GET':
            self.add_token_to_get_params(request)

        yield request

    def add_token_to_post_body(self, request: httpx.Request):
        data = dict(parse_qsl(request.content))
        data['token'] = self.access_token
        headers, request.stream = encode_request(data=data)

        # Ensure our Content-Length header is updated to new value
        request.headers.update(headers)

    def add_token_to_get_params(self, request: httpx.Request):
        params = dict(parse_qsl(request.content))
        params['token'] = self.access_token
        request.url.query = urlencode(params)
