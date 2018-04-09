import json
import responses
import time

from dasdaemon.managers import RequestsManager

import test.common as common
from test.integration import DaServerIntegrationTest


class RequestsManagerTests(DaServerIntegrationTest):

    def setUp(self):
         # Get test config
        self.config = common.load_test_config()
        self.token_url = self.config['RequestsManager']['token_url']
        self.token_expiration_sec = self.config['RequestsManager']['token_expiration_sec']
        self.test_url = self.config['RequestsManager']['test_url']

        # Create requests manager
        self.rm = RequestsManager(config=self.config)

    def _mock_token_request(self, token, status=200):
        responses.reset()
        responses.add(
            responses.POST, self.token_url, match_querystring=True,
            body=json.dumps({'token': token}), status=status,
            content_type='application/json'
        )

    def test_token_is_valid(self):
        # Verify token is not valid on startup
        self.assertFalse(self.rm._token_is_valid())

        # Set token and update created time
        self.rm.token = 'whatever'
        self.rm._update_token_created()

        # Verify token is valid
        self.assertTrue(self.rm._token_is_valid())

        # Sleep longer than the expiration
        time.sleep(int(self.token_expiration_sec))

        # Verify token is not valid
        self.assertFalse(self.rm._token_is_valid())

    @responses.activate
    def test_request_new_token(self):
        token = 'whatever'
        self._mock_token_request(token)

        # Get new token
        self.rm._request_new_token()

        # Verify token
        self.assertEqual(self.rm.token, token)

        # Verify token is valid
        self.assertTrue(self.rm._token_is_valid())

    def test_get(self):
        # Send get request
        params = {'key1': 'value1'}
        r = self.rm.get(self.test_url, params=params)

        # Verify request
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'data': params})

    def test_post(self):
        # Send post request
        data = {'key1': 'value1'}
        r = self.rm.post(self.test_url, data=data)

        # Verify request
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'data': data})

    def test_get_nonexistant_url(self):
        # Send get request
        r = self.rm.get('http://does.not.exist')

        # Verify request
        self.assertIsNone(r)
