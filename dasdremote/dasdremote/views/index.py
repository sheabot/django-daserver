from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView


class IndexViews(APIView):

    def get(self, request):
        return Response({'data': settings.DASDREMOTE})

index_view = IndexViews.as_view()
