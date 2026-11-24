#!/usr/bin/python3
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import atheris
import sys
import binascii
with atheris.instrument_imports():
     from adal.util import *

def TestInput(data):
    fdp = atheris.FuzzedDataProvider(data)

    # The parsers (copy_url -> urlparse, base64_urlsafe_decode) take their input first. Upstream
    # fed them last, after ~20 ConsumeString() calls had eaten the whole input, so they only ever
    # saw '' and the fuzzer never found a second path (Mayhem: edges=0). Same calls, same checks.
    url = fdp.ConsumeString(100)
    b64 = fdp.ConsumeUnicodeNoSurrogates(100)

    is_http_success(fdp.ConsumeInt(10))

    class DummyClass(object):
        _call_context = {
            'log_context':{'correlation_id':fdp.ConsumeString(20)},
            'options':{'http':{
                fdp.ConsumeString(10):fdp.ConsumeString(100),
                fdp.ConsumeString(10):fdp.ConsumeString(100),
                fdp.ConsumeString(10):fdp.ConsumeString(100)
            }}
        }

        def geturl(self):
           return url

    create_request_options(DummyClass(),{
        fdp.ConsumeString(10):fdp.ConsumeString(100),
        fdp.ConsumeString(10):fdp.ConsumeString(100),
        fdp.ConsumeString(10):fdp.ConsumeString(100),
        'headers':{
            fdp.ConsumeString(10):fdp.ConsumeString(100),
            fdp.ConsumeString(10):fdp.ConsumeString(100),
            fdp.ConsumeString(10):fdp.ConsumeString(100)
        }
    })

    try:
        copy_url(url)
        copy_url(DummyClass())
    except ValueError:
        # urlsplit's rejections of a malformed URL. Upstream allow-listed two messages; Python
        # >= 3.12 adds more (bracketed-host / IPvFuture checks), all ValueError by contract.
        pass

    try:
        base64_urlsafe_decode(b64)
    except UnicodeEncodeError:
        pass  # .encode('ascii') rejects non-ASCII input; adal's callers catch it as ValueError
    except binascii.Error as e:
        # binascii's rejections of non-base64 input ("Incorrect padding" is how Python >= 3.13
        # reports a length of 4n+1, which older versions called "Invalid base64-encoded string").
        if ("Invalid base64-encoded string" not in str(e) and
            "Incorrect padding" not in str(e)):
            raise e

def main():
    atheris.Setup(sys.argv, TestInput, enable_python_coverage=True)
    atheris.Fuzz()

if __name__ == "__main__":
    main()

