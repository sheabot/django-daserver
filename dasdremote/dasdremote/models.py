import binascii
import os

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class DaSDRemoteToken(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='dasdremote_auth_token',
        on_delete=models.CASCADE, verbose_name=_("User"), primary_key=True
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        # TODO: Can this be removed with a newer django version?
        # Work around for a bug in Django:
        # https://code.djangoproject.com/ticket/19422
        #
        # Also see corresponding ticket:
        # https://github.com/tomchristie/django-rest-framework/issues/705
        abstract = 'rest_framework.authtoken' not in settings.INSTALLED_APPS
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    def save(self, *args, **kwargs):
        self.key = self.generate_key()
        return super(DaSDRemoteToken, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key


class Torrent(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now_add=True)
    package_files_count = models.IntegerField(default=0)

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return 'id: %d, name: "%s", created: %s, package_files_count: %d' % (
            self.id, self.name, self.created, self.package_files_count
        )

    def save(self, *args, **kwargs):
        """Update last modified time"""
        self.last_modified = timezone.now()
        super(Torrent, self).save(*args, **kwargs)

    def is_packaged(self):
        return self.package_files_count > 0


class PackageFile(models.Model):
    filename = models.CharField(max_length=255)
    filesize = models.IntegerField(default=0)
    sha256 = models.CharField(max_length=255)
    torrent = models.ForeignKey(Torrent, related_name='package_file_set')

    def __unicode__(self):
        return 'id: %d, filename: "%s", filesize: %d, sha256: %s' % (
            self.id, self.filename, self.filesize, self.sha256
        )
