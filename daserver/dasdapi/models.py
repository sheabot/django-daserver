from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from dasdapi.stages import TorrentStage


class Torrent(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now_add=True)
    stage = models.CharField(max_length=255)
    package_files_count = models.IntegerField(default=0)

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return 'Torrent: id: %d, created: %s, stage: %s, package_files_count: %d' % (
            self.id, self.created, self.stage, self.package_files_count
        )

    def save(self, *args, **kwargs):
        """Update last modified time"""
        self.last_modified = timezone.now()
        super(Torrent, self).save(*args, **kwargs)

    def completed(self):
        """Move torrent to completed stage and save it"""
        stage = TorrentStage(self.stage)
        assert stage.is_processing_stage
        self.stage = stage.next().name
        self.save()

    def set_error(self, error):
        """Create error if necessary, otherwise update the most recent error.
        Then, move torrent to error stage.
        """
        err, created = self.errors.get_or_create(
            type=error.id,
            defaults={
                'message': str(error),
                'stage': self.stage
                }
            )

        if not created:
            err.save()
        self.stage = 'Error'
        self.save()


class PackageFile(models.Model):
    filename = models.CharField(max_length=255)
    torrent = models.ForeignKey(Torrent, related_name='package_file_set')
    filesize = models.IntegerField(default=0)
    sha256 = models.CharField(max_length=255, blank=True)
    stage = models.CharField(max_length=255)

    def set_error(self, error):
        """Create error if necessary, otherwise update the most recent error.
        Then, move torrent to error stage.
        """
        err, created = self.errors.get_or_create(
            type=error.id,
            defaults={
                'message': str(error),
                'stage': self.stage
            }
        )

        if not created:
            err.save()
        self.stage = 'Error'
        self.save()


class TorrentError(models.Model):
    torrent = models.ForeignKey(Torrent, related_name='errors')
    type = models.BigIntegerField()
    message = models.CharField(max_length=1024)
    time = models.DateTimeField()
    stage = models.CharField(max_length=255)
    count = models.IntegerField(default=0)
    retry_delay = models.IntegerField(default=2)

    class Meta:
        ordering = ('-time',)

    def save(self, *args, **kwargs):
        """Update time, increment count, increase retry delay exponentially,
        and save to database
        """
        self.time = timezone.now()
        self.count += 1
        self.retry_delay **= 2
        super(TorrentError, self).save(*args, **kwargs)


class PackageFileError(models.Model):
    package_file = models.ForeignKey(PackageFile, related_name='errors')
    type = models.BigIntegerField()
    message = models.CharField(max_length=1024)
    time = models.DateTimeField()
    stage = models.CharField(max_length=255)
    count = models.IntegerField(default=0)
    retry_delay = models.IntegerField(default=2)

    class Meta:
        ordering = ('-time',)

    def save(self, *args, **kwargs):
        """Update time, increment count, increase retry delay exponentially,
        and save to database
        """
        self.time = timezone.now()
        self.count += 1
        self.retry_delay **= 2
        super(PackageFileError, self).save(*args, **kwargs)
