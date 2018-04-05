import os

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse
)
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from dasdremote.authentication import DaSDRemoteTokenAuthentication
from dasdremote.logger import log
from dasdremote.models import PackageFile, Torrent
from dasdremote.serializers import TorrentPackageSerializer
from dasdremote.torrent_package import TorrentDoesNotExistException, TorrentPackage


class DaSDRemoteTorrentViews(APIView):
    authentication_classes = (DaSDRemoteTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        # Validate input
        serializer = TorrentPackageSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            # Return list of packaged torrents
            packaged_torrents = Torrent.objects.filter(package_files_count__gt=0)
            return JsonResponse([torrent.name for torrent in packaged_torrents], safe=False)

        # Save input
        torrent_name = serializer.data['torrent']
        log.debug('Get package files for torrent: %s' % torrent_name)

        # Lookup torrent
        try:
            torrent = Torrent.objects.get(name=torrent_name)
            if not torrent.is_packaged():
                # Torrent has not been packaged yet
                log.error('Torrent not packaged yet: %s' % torrent.name)
                return HttpResponseNotFound()

            # Return list of package files
            return JsonResponse(self._get_package_files(torrent), safe=False)
        except Torrent.DoesNotExist:
            log.error('Torrent does not exist: %s' % torrent_name)
            return HttpResponseNotFound()
        except:
            log.exception("Error")
            return HttpResponseServerError()

    def _get_package_files(self, torrent):
        package_files = []
        for package_file in torrent.package_file_set.all().order_by('filename'):
            package_files.append({
                'filename': package_file.filename,
                'filesize': package_file.filesize,
                'sha256': package_file.sha256
            })
        return package_files
