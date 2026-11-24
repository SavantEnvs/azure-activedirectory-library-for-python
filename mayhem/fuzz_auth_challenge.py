#!/usr/bin/python3
"""Atheris harness: WWW-Authenticate Bearer challenge (RFC 6750) parser.

The bytes are the WWW-Authenticate header a resource server sends with a 401; adal
parses it with create_authentication_parameters_from_response() /
create_authentication_parameters_from_header(). ValueError is the documented rejection.
"""
import logging
import sys

import atheris

with atheris.instrument_imports():
    from adal.authentication_parameters import (
        create_authentication_parameters_from_header,
        create_authentication_parameters_from_response)

logging.disable(logging.CRITICAL)


class _Response(object):
    """The two attributes create_authentication_parameters_from_response reads."""

    def __init__(self, header):
        self.status_code = 401
        self.headers = {'www-authenticate': header}


def TestOneInput(data):
    text = data.decode('utf-8', 'replace')
    try:
        create_authentication_parameters_from_header(text)
    except ValueError:
        pass
    try:
        create_authentication_parameters_from_response(_Response(text))
    except ValueError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == '__main__':
    main()
