from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import TestCase, override_settings
from category.models import HeroPoster


class CatalogueMediaTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_context = override_settings(DEBUG=False, MEDIA_ROOT=self.directory.name)
        self.settings_context.enable()
        self.addCleanup(self.settings_context.disable)
        Path(self.directory.name, 'poster.jpg').write_bytes(b'example-image')
        HeroPoster.objects.create(image='poster.jpg', alt_text='Our original poster')

    def test_known_uploaded_photo_served_without_debug(self):
        response = self.client.get('/media/poster.jpg')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(b''.join(response.streaming_content), b'example-image')
        response.close()

    def test_unreferenced_file_is_private(self):
        Path(self.directory.name, 'private.jpg').write_bytes(b'private')
        self.assertEqual(self.client.get('/media/private.jpg').status_code, 404)

    def test_referenced_missing_file_returns_404(self):
        HeroPoster.objects.create(image='missing.jpg', alt_text='Unavailable')
        self.assertEqual(self.client.get('/media/missing.jpg').status_code, 404)

    def test_non_image_and_traversal_are_rejected(self):
        HeroPoster.objects.create(image='private.json', alt_text='Invalid file')
        Path(self.directory.name, 'private.json').write_text('{}')
        self.assertEqual(self.client.get('/media/private.json').status_code, 404)
        self.assertEqual(self.client.get('/media/%2E%2E/private.json').status_code, 404)
