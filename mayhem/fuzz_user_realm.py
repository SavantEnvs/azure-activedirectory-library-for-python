#!/usr/bin/python3
"""Atheris harness: user realm discovery response (JSON).

The bytes are the body of GET <authority>/common/UserRealm/<user>; UserRealm.discover()
passes it to _parse_discovery_response(), which decides managed vs federated and the
federation protocol/metadata URL. ValueError (bad JSON) and AdalError are the
documented rejections; anything else (e.g. a KeyError on a missing field) is a finding.
"""
import logging
import sys

import atheris

with atheris.instrument_imports():
    from adal.adal_error import AdalError
    from adal.user_realm import UserRealm

logging.disable(logging.CRITICAL)
CALL_CONTEXT = {'log_context': {'correlation_id': 'fuzz'}, 'options': {}}


def TestOneInput(data):
    text = data.decode('utf-8', 'replace')
    realm = UserRealm(CALL_CONTEXT, 'user@example.com', 'https://login.microsoftonline.com/common')
    try:
        realm._parse_discovery_response(text)
    except (AdalError, ValueError):
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == '__main__':
    main()
