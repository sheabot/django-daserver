from django.views import generic

from dasdremote.models import Torrent


class IndexView(generic.ListView):
    model = Torrent
    template_name = 'dasdremote/index.html'
    context_object_name = 'torrents'


class DetailView(generic.DetailView):
    model = Torrent
    template_name = 'dasdremote/torrent.html'
    slug_field = 'name'
    slug_url_kwarg = 'name'
