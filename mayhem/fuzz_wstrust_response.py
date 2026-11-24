#!/usr/bin/python3
"""Atheris harness: WS-Trust RSTR (SOAP/SAML) response parser.

The bytes are what an ADFS/STS server returns to adal's username/password flow
(WSTrustRequest.acquire_token -> WSTrustResponse(...).parse()). Each input is parsed
as a WS-Trust 1.3 and as a WS-Trust 2005 response. AdalError is adal's documented
"bad RSTR" error; anything else escaping parse() is a finding.
"""
import logging
import sys

import atheris

with atheris.instrument_imports():
    from adal.adal_error import AdalError
    from adal.constants import WSTrustVersion
    from adal.wstrust_response import WSTrustResponse

logging.disable(logging.CRITICAL)
CALL_CONTEXT = {'log_context': {'correlation_id': 'fuzz'}, 'options': {}}


def TestOneInput(data):
    text = data.decode('utf-8', 'replace')
    for version in (WSTrustVersion.WSTRUST13, WSTrustVersion.WSTRUST2005):
        try:
            WSTrustResponse(CALL_CONTEXT, text, version).parse()
        except AdalError:
            pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == '__main__':
    main()
