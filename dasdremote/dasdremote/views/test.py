import os
import shutil

from django.conf import settings
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotFound
)
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from dasdremote.authentication import DaSDRemoteTokenAuthentication
from dasdremote.permissions import IsAuthenticatedTest
from dasdremote.serializers import (
    TestCreateTorrentSerializer,
    TestDeleteTorrentSerializer
)
import dasdremote.utils as utils


class DaSDRemoteTestView(APIView):
    authentication_classes = (DaSDRemoteTokenAuthentication,)
    permission_classes = (IsAuthenticatedTest,)
    renderer_classes = (JSONRenderer,)


class DaSDRemoteTestRequestViews(DaSDRemoteTestView):

    def get(self, request, format=None):
        return Response({'data': request.GET})

    def post(self, request, *args, **kwargs):
        return Response({'data': request.data})

requests_view = DaSDRemoteTestRequestViews.as_view()


class DaSDRemoteTestCompletedTorrentsView(DaSDRemoteTestView):

    # Create new completed torrent
    # TODO: Take in a list of file sizes instead of a file count and total size
    def post(self, request, *args, **kwargs):
        # Validate input
        serializer = TestCreateTorrentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save input
        torrent = serializer.data['torrent']
        file_count = serializer.data['file_count']
        total_size = serializer.data['total_size']

        # Determine paths
        # Torrent must be created in a temp directory and moved to
        # the completed torrents directory to trigger inotify
        temp_path = os.path.join(settings.DASDREMOTE['TEMP_DIR'], torrent)
        path = os.path.join(settings.DASDREMOTE['COMPLETED_TORRENTS_DIR'], torrent)

        if file_count == 1:
            # Torrent is one file
            utils.fs.write_random_file(temp_path, total_size)
            shutil.move(temp_path, path)
            sha256 = utils.hash.compute_sha256(path)
            return Response([{'filename': torrent, 'filesize': total_size, 'sha256': sha256}])

        # Torrent is a directory of files
        utils.fs.mkdir_p(temp_path)

        file_size = total_size / file_count
        remainder = total_size % file_count
        if file_size == 0:
            return HttpResponseBadRequest('Total size is not large enough for the number of files')

        response_data = []
        i = -1
        for i in xrange(file_count):
            filename = '%s.%04d' % (torrent, i)
            file_path = os.path.join(temp_path, filename)
            utils.fs.write_random_file(file_path, file_size)
            sha256 = utils.hash.compute_sha256(file_path)
            response_data.append({'filename': filename, 'filesize': file_size, 'sha256': sha256})

        if remainder > 0:
            filename = '%s.%04d' % (torrent, i+1)
            file_path = os.path.join(temp_path, filename)
            utils.fs.write_random_file(file_path, remainder)
            sha256 = utils.hash.compute_sha256(file_path)
            response_data.append({'filename': filename, 'filesize': remainder, 'sha256': sha256})

        shutil.move(temp_path, path)

        return Response(response_data)

    # Delete existing completed torrent
    def delete(self, request, *args, **kwargs):
        # Validate input
        serializer = TestDeleteTorrentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save input
        torrent = serializer.data['torrent']
        delete_all = serializer.data['delete_all']

        # Get config
        completed_torrents_dir = settings.DASDREMOTE['COMPLETED_TORRENTS_DIR']

        # Delete directory contents
        if delete_all:
            utils.fs.rm_dir_contents(completed_torrents_dir)
            return Response('Cleared completed torrents directory')

        # Determine path
        path = os.path.join(completed_torrents_dir, torrent)

        # Delete path
        utils.fs.rm_rf(path)

        return Response('Deleted completed torrent: %s' % torrent)


completed_torrents_view = DaSDRemoteTestCompletedTorrentsView.as_view()


class DaSDRemoteTestPackagedTorrentsView(DaSDRemoteTestView):

    # Create packaged torrent
    def post(self, request, *args, **kwargs):
        # Validate input
        serializer = TestCreateTorrentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save input
        torrent = serializer.data['torrent']
        file_count = serializer.data['file_count']
        total_size = serializer.data['total_size']

        # Create package files(s)
        file_size = total_size / file_count
        remainder = total_size % file_count
        if file_size == 0:
            return HttpResponseBadRequest('Total size is not large enough for the number of files')

        response_data = []
        i = -1
        for i in xrange(file_count):
            filename = '%s.%04d' % (torrent, i)
            file_path = os.path.join(settings.DASDREMOTE['PACKAGED_TORRENTS_DIR'], filename)
            utils.fs.write_random_file(file_path, file_size)
            sha256 = utils.hash.compute_sha256(file_path)
            response_data.append({'filename': filename, 'filesize': file_size, 'sha256': sha256})

        if remainder > 0:
            filename = '%s.%04d' % (torrent, i+1)
            file_path = os.path.join(settings.DASDREMOTE['PACKAGED_TORRENTS_DIR'], filename)
            utils.fs.write_random_file(file_path, remainder)
            sha256 = utils.hash.compute_sha256(file_path)
            response_data.append({'filename': filename, 'filesize': remainder, 'sha256': sha256})

        return Response(response_data)


    # Delete existing packaged torrent(s)
    def delete(self, request, *args, **kwargs):
        # Validate input
        serializer = TestDeleteTorrentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save input
        torrent = serializer.data['torrent']
        delete_all = serializer.data['delete_all']

        # Get config
        packaged_torrents_dir = settings.DASDREMOTE['PACKAGED_TORRENTS_DIR']

        # Delete directory contents
        if delete_all:
            utils.fs.rm_dir_contents(packaged_torrents_dir)
            return Response('Cleared packaged torrents directory')

        # Determine path
        path = os.path.join(packaged_torrents_dir, torrent)

        # Delete path
        utils.fs.rm_rf(path)

        return Response('Deleted packaged torrent: %s' % torrent)


packaged_torrents_view = DaSDRemoteTestPackagedTorrentsView.as_view()
