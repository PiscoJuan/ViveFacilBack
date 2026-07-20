from django.conf import settings
from django.db.models import FileField, ImageField
from django.db.models.fields.files import FieldFile, ImageFieldFile


class URLCompletaFieldFile(FieldFile):
    @property
    def url(self):
        return settings.URL_BACKEND_HOST.rstrip('/') + super().url


class URLCompletaImageFieldFile(ImageFieldFile):
    @property
    def url(self):
        return settings.URL_BACKEND_HOST.rstrip('/') + super().url


class URLCompletaFileField(FileField):
    attr_class = URLCompletaFieldFile

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'django.db.models.FileField', args, kwargs


class URLCompletaImageField(ImageField):
    attr_class = URLCompletaImageFieldFile

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'django.db.models.ImageField', args, kwargs
