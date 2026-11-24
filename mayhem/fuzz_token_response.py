#!/usr/bin/python3
"""Atheris harness: OAuth2 token endpoint response (JSON + id_token JWT).

The bytes are the body the token endpoint returns; OAuth2Client.get_token() hands it to
_handle_get_token_response(), which validates the JSON, parses the optional ints and
decodes the id_token JWT. AdalError is the documented rejection, and ValueError
(JSONDecodeError, a bad int, a bad base64/UTF-8 id_token) is re-raised by adal on purpose.
"""
import logging
import sys

import atheris

with atheris.instrument_imports():
    from adal.adal_error import AdalError
    from adal.authority import Authority
    from adal.oauth2_client import OAuth2Client

logging.disable(logging.CRITICAL)
CALL_CONTEXT = {'log_context': {'correlation_id': 'fuzz'}, 'options': {}}
AUTHORITY = Authority('https://login.microsoftonline.com/common', False)
AUTHORITY.token_endpoint = 'https://login.microsoftonline.com/common/oauth2/token'
AUTHORITY.device_code_endpoint = 'https://login.microsoftonline.com/common/oauth2/devicecode'


def TestOneInput(data):
    text = data.decode('utf-8', 'replace')
    client = OAuth2Client(CALL_CONTEXT, AUTHORITY)
    try:
        client._handle_get_token_response(text)
    except (AdalError, ValueError):
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == '__main__':
    main()
