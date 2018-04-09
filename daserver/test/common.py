import json
import os

import responses

from dasdaemon.config import DaSDConfig


_CONFIG_FILE_NAME = os.getenv('DASD_CONFIG', 'dasd.cfg')


class ConfigFileNotFoundError(Exception):
    pass


def load_test_config(config_file_name=_CONFIG_FILE_NAME):
    # Get path to config file
    working_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(working_dir, 'config', config_file_name)

    # Parse config
    dasd_config = DaSDConfig()
    config = dasd_config.read(config_file_path)
    if config == []:
        raise ConfigFileNotFoundError
    return dasd_config.get_all()

def mock_requests_manager():
    config = load_test_config()
    responses.add(
        responses.POST, config['RequestsManager']['token_url'],
        body=json.dumps({'token': 'mocked_token'}), status=200,
        content_type='application/json'
    )


class TestHelper(object):

    def __init__(self, config, requests_manager):
        self.config = config['TestHelper']
        self.completed_torrents_url = self.config['completed_torrents_url']
        self.packaged_torrents_url = self.config['packaged_torrents_url']
        self.requests_manager = requests_manager

    def create_completed_torrent(self, torrent, file_count=1, total_size=1024):
        return self.requests_manager.post(
            self.completed_torrents_url,
            data={
                'torrent': torrent,
                'file_count': file_count,
                'total_size': total_size
            }
        )

    def delete_completed_torrent(self, torrent):
        return self.requests_manager.delete(
            self.completed_torrents_url,
            data={
                'torrent': torrent
            }
        )

    def delete_all_completed_torrents(self):
        return self.requests_manager.delete(
            self.completed_torrents_url,
            data={
                'torrent': 'all',
                'delete_all': True
            }
        )

    def create_packaged_torrent(self, torrent, file_count=1, total_size=1024):
        return self.requests_manager.post(
            self.packaged_torrents_url,
            data={
                'torrent': torrent,
                'file_count': file_count,
                'total_size': total_size
            }
        )

    def delete_packaged_torrent(self, torrent):
        return self.requests_manager.delete(
            self.packaged_torrents_url,
            data={
                'torrent': torrent
            }
        )

    def delete_all_packaged_torrents(self):
        return self.requests_manager.delete(
            self.packaged_torrents_url,
            data={
                'torrent': 'all',
                'delete_all': True
            }
        )

    def delete_remote_torrents(self):
        self.delete_all_completed_torrents()
        self.delete_all_packaged_torrents()
