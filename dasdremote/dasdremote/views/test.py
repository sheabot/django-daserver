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
    def post(self, request, *args, **kwargs):
        # Validate input
        serializer = TestCreateTorrentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save input
        torrent = serializer.data['torrent']
        file_count = serializer.data['file_count']
        total_size = serializer.data['total_size']

        # Determine path
        path = os.path.join(settings.DASDREMOTE['COMPLETED_TORRENTS_DIR'], torrent)

        if file_count == 1:
            # Torrent is one file
            utils.write_random_file(path, total_size)
            md5 = utils.compute_md5(path)
            return Response([{'filename': torrent, 'md5': md5}])

        # Torrent is a directory of files
        utils.mkdir_p(path)

        file_size = total_size / file_count
        if file_size == 0:
            return HttpResponseBadRequest('Total size is not large enough for the number of files')

        response_data = []
        for i in xrange(file_count):
            filename = '%s.%04d' % (torrent, i)
            file_path = os.path.join(path, filename)
            utils.write_random_file(file_path, file_size)
            md5 = utils.compute_md5(file_path)
            response_data.append({'filename': filename, 'md5': md5})

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
            utils.rm_dir_contents(completed_torrents_dir)
            return Response('Cleared completed torrents directory')

        # Determine path
        path = os.path.join(completed_torrents_dir, torrent)

        # Delete path
        utils.rm_rf(path)

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
        if file_size == 0:
            return HttpResponseBadRequest('Total size is not large enough for the number of files')

        response_data = []
        for i in xrange(file_count):
            filename = '%s.%04d' % (torrent, i)
            file_path = os.path.join(settings.DASDREMOTE['PACKAGED_TORRENTS_DIR'], filename)
            utils.write_random_file(file_path, file_size)
            md5 = utils.compute_md5(file_path)
            response_data.append({'filename': filename, 'md5': md5})

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
            utils.rm_dir_contents(packaged_torrents_dir)
            return Response('Cleared packaged torrents directory')

        # Determine path
        path = os.path.join(packaged_torrents_dir, torrent)

        # Delete path
        utils.rm_rf(path)

        return Response('Deleted packaged torrent: %s' % torrent)


packaged_torrents_view = DaSDRemoteTestPackagedTorrentsView.as_view()
