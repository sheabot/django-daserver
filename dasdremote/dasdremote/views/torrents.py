import os

from django.conf import settings
from django.http import (
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse
)
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from dasdremote.authentication import DaSDRemoteTokenAuthentication
from dasdremote.logger import log
from dasdremote.serializers import TorrentPackageSerializer
from dasdremote.torrent_package import TorrentDoesNotExistException, TorrentPackage


class DaSDRemoteTorrentViews(APIView):
    authentication_classes = (DaSDRemoteTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        # Return directory listing
        dir = settings.DASDREMOTE['COMPLETED_TORRENTS_DIR']
        listing = os.listdir(dir)
        return JsonResponse(listing, safe=False)

    def post(self, request, *args, **kwargs):
        # Validate input
        serializer = TorrentPackageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save input
        torrent = serializer.data['torrent']
        log.debug('torrent: %s' % torrent)

        # Get config
        completed_torrents_dir = settings.DASDREMOTE['COMPLETED_TORRENTS_DIR']
        packaged_torrents_dir = settings.DASDREMOTE['PACKAGED_TORRENTS_DIR']

        # Get full path to torrent
        torrent_path = os.path.join(completed_torrents_dir, torrent)

        try:
            # Create torrent package instance
            split_bytes = settings.DASDREMOTE['TORRENT_PACKAGE_SPLIT_BYTES']
            tp = TorrentPackage(torrent_path, packaged_torrents_dir, split_bytes)

            # Package torrent
            tp.create_package()

            # Return list of package files as json
            return JsonResponse(tp.get_split_files(), safe=False)
        except TorrentDoesNotExistException:
            # Could not find torrent
            return HttpResponseNotFound()
        except:
            # Failed to package torrent
            return HttpResponseServerError()
