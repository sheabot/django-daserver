import os

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseNotFound
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from dasdremote.authentication import DaSDRemoteTokenAuthentication
import dasdremote.utils as utils


class DaSDRemoteDownloadViews(APIView):
    authentication_classes = (DaSDRemoteTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, filename):
        # Verify file exists
        filepath = os.path.join(settings.DASDREMOTE['PACKAGED_TORRENTS_DIR'], filename)
        if not os.path.isfile(filepath):
            return HttpResponseNotFound()

        response = HttpResponse()
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        response['X-Accel-Redirect'] = os.path.join(settings.DASDREMOTE['PACKAGED_TORRENTS_INTERNAL_URL'], filename)
        return response

    def delete(self, request, filename):
        # Delete torrent package file
        try:
            os.remove(os.path.join(settings.DASDREMOTE['PACKAGED_TORRENTS_DIR'], filename))
            return HttpResponse()
        except:
            return HttpResponseNotFound()