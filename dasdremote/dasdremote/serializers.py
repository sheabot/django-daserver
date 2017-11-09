from rest_framework import serializers


class TorrentPackageSerializer(serializers.Serializer):

    torrent = serializers.RegexField(r'[^/]+')


#
# Test Serializers
#

class TestCreateTorrentSerializer(serializers.Serializer):

    torrent = serializers.RegexField(r'[^/]+')
    file_count = serializers.IntegerField(min_value=1)
    total_size = serializers.IntegerField(min_value=1)


class TestDeleteTorrentSerializer(serializers.Serializer):

    torrent = serializers.RegexField(r'[^/]+')
    delete_all = serializers.BooleanField(default=False)
