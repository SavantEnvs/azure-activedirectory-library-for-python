#!/usr/bin/env python3
"""Functional oracle for adal: upstream's own unittest suite plus known-answer checks.

Runs every upstream test module under tests/ (network calls are mocked by httpretty) and a few
known-answer checks on the parsers the fuzz targets drive. Prints one line
`ORACLE_RESULT passed=<n> failed=<n> skipped=<n>` that mayhem/test.sh turns into CTRF; a neutered
program prints nothing and fails test.sh.
"""
import io
import os
import sys
import unittest

SRC = os.environ.get('SRC', '/mayhem')
sys.path.insert(0, SRC)
os.chdir(SRC)


class KnownAnswer(unittest.TestCase):
    CC = {'log_context': {'correlation_id': 'oracle'}, 'options': {}}

    def test_challenge(self):
        from adal.authentication_parameters import create_authentication_parameters_from_header
        p = create_authentication_parameters_from_header(
            'Bearer authorization_uri="https://login.example.com/tenant", resource="https://res"')
        self.assertEqual(p.authorization_uri, 'https://login.example.com/tenant')
        self.assertEqual(p.resource, 'https://res')

    def test_user_realm(self):
        from adal.user_realm import UserRealm
        u = UserRealm(self.CC, 'a@b.com', 'https://login.microsoftonline.com/common')
        u._parse_discovery_response(
            '{"account_type":"Federated","federation_protocol":"WSTrust",'
            '"federation_metadata_url":"https://adfs/mex","federation_active_auth_url":"https://adfs/a"}')
        self.assertEqual(u.account_type, 'federated')
        self.assertEqual(u.federation_protocol, 'wstrust')
        self.assertEqual(u.federation_metadata_url, 'https://adfs/mex')

    def test_token_response(self):
        import base64
        import json
        from adal.authority import Authority
        from adal.oauth2_client import OAuth2Client
        a = Authority('https://login.microsoftonline.com/common', False)
        a.token_endpoint = 'https://x/token'
        a.device_code_endpoint = 'https://x/dc'

        def b64(d):
            return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip('=')
        idt = b64({'alg': 'none'}) + '.' + b64({'upn': 'u@contoso.com', 'tid': 'T1', 'oid': 'O1',
                                                 'given_name': 'G'}) + '.'
        r = OAuth2Client(self.CC, a)._handle_get_token_response(json.dumps(
            {'token_type': 'Bearer', 'access_token': 'AT', 'expires_in': '3600',
             'refresh_token': 'RT', 'id_token': idt}))
        self.assertEqual(r['accessToken'], 'AT')
        self.assertEqual(r['tokenType'], 'Bearer')
        self.assertEqual(r['expiresIn'], 3600)
        self.assertEqual(r['userId'], 'u@contoso.com')
        self.assertEqual(r['tenantId'], 'T1')

    def test_token_cache_roundtrip(self):
        from adal.token_cache import TokenCache
        state = ('[{"_authority":"https://a","resource":"r","_clientId":"C","userId":"U","isMRRT":true},'
                 '{"_authority":"https://a","resource":"r2","_clientId":"D","userId":"V"}]')
        t = TokenCache(state)
        self.assertEqual(len(t.find({'_clientId': 'c'})), 1)
        self.assertEqual(len(t.find({'isMRRT': True})), 1)
        self.assertEqual(len(TokenCache(t.serialize()).find({})), 2)


# Upstream tests that fail at upstream HEAD for reasons outside adal's parsers; reported as skipped.
KNOWN_BROKEN = {
    # Upstream's own last commit ("deprecation", e546d35) made AuthenticationContext() emit a
    # deprecation warning, so these two "no warning is raised" tests fail upstream too.
    'tests.test_api_version.TestAuthenticationContextApiVersionBehavior.test_api_version_default_value':
        'fails upstream since the adal deprecation warning (e546d35)',
    'tests.test_api_version.TestAuthenticationContextApiVersionBehavior.test_explicitly_turn_off_api_version':
        'fails upstream since the adal deprecation warning (e546d35)',
    # Asserts httpretty 0.8's default body text; httpretty >= 1.0 (the oldest that runs on
    # Python 3.13) sends a JSON default body instead.
    'tests.test_mex.Test_Mex.test_failed_request':
        'asserts httpretty 0.8 default body text',
}


def _flatten(suite):
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from _flatten(t)
        else:
            yield t


def _skip(reason):
    def f(self):
        raise unittest.SkipTest(reason)
    return f


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(KnownAnswer))
    suite.addTests(loader.discover(os.path.join(SRC, 'tests'), pattern='test_*.py', top_level_dir=SRC))
    for t in _flatten(suite):
        if t.id() in KNOWN_BROKEN:
            setattr(t, t._testMethodName, _skip(KNOWN_BROKEN[t.id()]).__get__(t))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    sys.stdout.write(stream.getvalue())
    bad = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
    skipped = len(result.skipped)
    passed = result.testsRun - bad - skipped
    print('ORACLE_RESULT passed=%d failed=%d skipped=%d' % (passed, bad, skipped))


if __name__ == '__main__':
    main()
