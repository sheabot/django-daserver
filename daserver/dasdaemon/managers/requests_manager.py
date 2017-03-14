from datetime import datetime
import requests
import threading

from dasdaemon.exceptions import DaSDRequestError
from dasdaemon.logger import log

REQUESTS_MANAGER_DEBUG = False


class RequestNewTokenError(Exception):
    pass


class RequestsManager(object):

    def __init__(self, config):
        # Config
        self.config = config['RequestsManager']
        self.token_url = self.config['token_url']
        self.username = self.config['username']
        self.password = self.config['password']
        self.token_expiration_sec = int(self.config['token_expiration_sec'])
        self.timeout = int(self.config['timeout'])

        # Request token
        self.token = None
        self.token_created = datetime.utcfromtimestamp(0)
        self._lock = threading.Lock()

    def get(self, *args, **kwargs):
        return self._send_request(requests.get, *args, **kwargs)

    def get_json(self, *args, **kwargs):
        return self._send_request_json(requests.get, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._send_request(requests.post, *args, **kwargs)

    def post_json(self, *args, **kwargs):
        return self._send_request_json(requests.post, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._send_request(requests.delete, *args, **kwargs)

    def get_file_stream(self, url, start=0, stop=None):
        headers = {}
        if stop is None:
            headers['Range'] = 'bytes=%d-' % start
        else:
            headers['Range'] = 'bytes=%d-%d' % (start, stop)

        req = self.get(url, stream=True, headers=headers)
        if req.status_code == requests.codes.partial:
            return req
        else:
            raise DaSDRequestError('Request returned %d', req.status_code)

    def _send_request(self, method, *args, **kwargs):
        # Refresh token if necessary
        self._refresh_token()

        # Add Authorization header to request
        headers = kwargs.get('headers', None)
        if headers is None:
            headers = {}
        headers['Authorization'] = 'Token %s' % self.token
        kwargs.update({'headers': headers})

        # Send request
        try:
            r = method(timeout=self.timeout, *args, **kwargs)
        except requests.RequestException:
            log.exception('Request exception')
            return None

        if r.status_code == requests.codes.forbidden:
            # Request failed
            # Refresh token on next iteration
            self._invalidate_token()

        return r

    def _send_request_json(self, method, *args, **kwargs):
        req = self._send_request(method, *args, **kwargs)
        if req is None:
            raise DaSDRequestError('Request is None')
        elif req.status_code != requests.codes.ok:
            raise DaSDRequestError('Request returned %d', req.status_code)
        else:
            try:
                return req.json()
            except:
                raise DaSDRequestError('Malformed data')

    def _token_is_valid(self):
        if not self.token:
            # No token yet
            return False

        # Calculate token age
        token_age = datetime.utcnow() - self.token_created
        return token_age.total_seconds() <= self.token_expiration_sec

    def _update_token_created(self):
        self.token_created = datetime.utcnow()

    def _request_new_token(self):
        # Send post request to dasdremote
        r = requests.post(
            self.token_url,
            data={
                'username': self.username,
                'password': self.password
            }
        )

        if r.status_code != requests.codes.ok:
            # Request error
            raise RequestNewTokenError('Bad response: status_code = %d' % r.status_code)

        try:
            # Get token and update created time
            self.token = r.json()['token']
            self._update_token_created()
        except:
            # Malformed data
            raise RequestNewTokenError('Bad response: Malformed data')

    def _refresh_token(self):
        with self._lock:
            if not self._token_is_valid():
                self._request_new_token()

    def _invalidate_token(self):
        with self._lock:
            # Reset token
            self.token = None


if REQUESTS_MANAGER_DEBUG:
    import logging

    # These two lines enable debugging at httplib level (requests->urllib3->http.client)
    # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger('requests.packages.urllib3')
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
