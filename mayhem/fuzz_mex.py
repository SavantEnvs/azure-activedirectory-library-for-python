#!/usr/bin/python3
"""Atheris harness: federation metadata exchange (MEX / WSDL) document parser.

Mirrors Mex.discover() after its HTTP GET: the fetched document is parsed into a DOM
and Mex._parse() selects the username/password WS-Trust endpoint from its policies,
bindings and ports. An XML ParseError and AdalError are the documented rejections.
"""
import logging
import sys
from xml.etree import ElementTree as ET

import atheris

with atheris.instrument_imports():
    from adal.adal_error import AdalError
    from adal.mex import Mex

logging.disable(logging.CRITICAL)
CALL_CONTEXT = {'log_context': {'correlation_id': 'fuzz'}, 'options': {}}


def TestOneInput(data):
    text = data.decode('utf-8', 'replace')
    mex = Mex(CALL_CONTEXT, 'https://example.com/mex')
    try:
        # Same three steps as Mex.discover() on a successful response.
        mex._mex_doc = text
        mex._dom = ET.fromstring(mex._mex_doc)
        mex._parents = {c: p for p in mex._dom.iter() for c in p}
        mex._parse()
    except (ET.ParseError, AdalError):
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == '__main__':
    main()
