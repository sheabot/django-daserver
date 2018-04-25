from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
#from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    url(r'^auth/api-token-auth/$', views.obtain_auth_token),
    url(r'^download/(?P<filename>[^/]+)/$', views.DaSDRemoteDownloadViews.as_view()),
    url(r'^torrents/$', views.DaSDRemoteTorrentViews.as_view()),
    url(r'^admin/', admin.site.urls),

    #url(r'^auth/login/$', auth_views.login),    # Don't think this is being used
]

if settings.DEBUG:
    urlpatterns += [
        url(r'^test/requests/$', views.test.requests_view),
        url(r'^test/completed-torrents/$', views.test.completed_torrents_view),
        url(r'^test/packaged-torrents/$', views.test.packaged_torrents_view),

        url(r'^index/', views.index.index_view),

        url(r'^debug/$', views.debug.IndexView.as_view()),
        url(r'^debug/(?P<name>[^/]+)/$', views.debug.DetailView.as_view(), name='torrent')
    ]
