#!/usr/bin/python3
"""Atheris harness: serialized token cache + device-code response (two small JSON readers).

The first byte selects the reader. TokenCache(state)/deserialize() load the JSON an application persisted; the cache is then
queried, read and re-serialized, and the round-trip must reload. The same bytes are also
fed to OAuth2Client._handle_get_device_code_response(), the reader for the device-code
endpoint's JSON. ValueError (bad JSON, bad int) and AdalError are documented rejections.
"""
import logging
import sys

import atheris

with atheris.instrument_imports():
    from adal.adal_error import AdalError
    from adal.authority import Authority
    from adal.oauth2_client import OAuth2Client
    from adal.token_cache import TokenCache

logging.disable(logging.CRITICAL)
CALL_CONTEXT = {'log_context': {'correlation_id': 'fuzz'}, 'options': {}}
AUTHORITY = Authority('https://login.microsoftonline.com/common', False)
AUTHORITY.token_endpoint = 'https://login.microsoftonline.com/common/oauth2/token'
AUTHORITY.device_code_endpoint = 'https://login.microsoftonline.com/common/oauth2/devicecode'


def _cache(text):
    try:
        cache = TokenCache(text)
    except ValueError:
        return
    cache.find({'_clientId': 'client', 'userId': 'user@example.com', 'isMRRT': True})
    cache.find({})
    list(cache.read_items())
    state = cache.serialize()
    again = TokenCache(state)
    assert len(list(again.read_items())) == len(list(cache.read_items()))


def _device_code(text):
    client = OAuth2Client(CALL_CONTEXT, AUTHORITY)
    try:
        client._handle_get_device_code_response(text)
    except (AdalError, ValueError):
        pass


def TestOneInput(data):
    # First byte picks the reader (even: serialized cache, odd: device-code response), so a
    # valid input for one reader is not fed to the other.
    if not data:
        return
    text = data[1:].decode('utf-8', 'replace')
    if data[0] & 1:
        _device_code(text)
    else:
        _cache(text)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == '__main__':
    main()
