"""Images pasted into the Add / Edit Finding markdown editors (upload_finding_image)."""
import datetime
import io
from unittest import mock

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import FileResponse
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from dojo.models import Dojo_User, Engagement, FileUpload, Product, Product_Type, Test, Test_Type

from .dojo_test_case import DojoTestCase

IN_MEMORY_STORAGES = {
    **settings.STORAGES,
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
}
PASSWORD = "testTEST1234!@#$"


def _image_bytes(image_format="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color=(255, 0, 0)).save(buffer, format=image_format)
    return buffer.getvalue()


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class TestUploadFindingImage(DojoTestCase):

    @classmethod
    def setUpTestData(cls):
        product_type = Product_Type.objects.create(name="Finding Image PT")
        cls.product = Product.objects.create(name="Finding Image Product", description="Test", prod_type=product_type)
        cls.member = Dojo_User.objects.create_user(username="finding_image_member", password=PASSWORD, is_active=True)
        cls.outsider = Dojo_User.objects.create_user(username="finding_image_outsider", password=PASSWORD, is_active=True)
        cls.product.authorized_users.add(cls.member)
        engagement = Engagement.objects.create(
            name="Finding Image Engagement",
            product=cls.product,
            target_start=timezone.make_aware(datetime.datetime(2024, 1, 1)),
            target_end=timezone.make_aware(datetime.datetime(2024, 12, 31)),
        )
        test_type, _ = Test_Type.objects.get_or_create(name="Manual Code Review")
        cls.test = Test.objects.create(
            engagement=engagement,
            test_type=test_type,
            target_start=timezone.make_aware(datetime.datetime(2024, 1, 1)),
            target_end=timezone.make_aware(datetime.datetime(2024, 12, 31)),
        )

    def _client(self, user):
        client = Client()
        client.login(username=user.username, password=PASSWORD)
        return client

    def _upload(self, user, content, name="pasted.png", content_type="image/png"):
        return self._client(user).post(
            reverse("upload_finding_image", args=(self.test.id,)),
            data={"image": SimpleUploadedFile(name, content, content_type=content_type)},
        )

    def test_member_upload_returns_access_file_url_and_attaches_to_test(self):
        response = self._upload(self.member, _image_bytes())

        self.assertEqual(response.status_code, 200, response.content)
        file_upload = self.test.files.get()
        self.assertEqual(
            response.json()["url"],
            reverse("access_file_named", args=(file_upload.id, self.test.id, "Test", f"finding-image-{file_upload.id}.png")),
        )
        self.assertTrue(file_upload.file.name.endswith(".png"))

    def test_url_ends_with_image_extension(self):
        # EasyMDE embeds the upload as ![](url) only when the URL ends in an image extension;
        # otherwise it inserts a [link](url) and the finding page shows text instead of the image.
        response = self._upload(self.member, _image_bytes("JPEG"))

        self.assertTrue(response.json()["url"].endswith(".jpg"))

    def test_embedded_url_renders_as_img_on_finding_page(self):
        from dojo.templatetags.display_tags import markdown_render  # noqa: PLC0415 -- template filter under test

        url = self._upload(self.member, _image_bytes()).json()["url"]

        self.assertIn(f'<img alt="" src="{url}"', str(markdown_render(f"Step 1\n![]({url})")))

    def test_uploaded_image_is_served_to_member(self):
        url = self._upload(self.member, _image_bytes()).json()["url"]

        response = self._client(self.member).get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(b"".join(response.streaming_content).startswith(b"\x89PNG"))

    def test_uploaded_image_is_not_served_to_outsider(self):
        url = self._upload(self.member, _image_bytes()).json()["url"]

        response = self._client(self.outsider).get(url)

        # DefectDojo's 403 handler renders the "403 Forbidden" page with status 400
        self.assertIn(response.status_code, {400, 403})
        self.assertNotIsInstance(response, FileResponse)

    def test_extension_follows_detected_format_not_client_name(self):
        response = self._upload(self.member, _image_bytes("JPEG"), name="looks-like.png")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(self.test.files.get().file.name.endswith(".jpg"))

    def test_non_image_is_rejected(self):
        response = self._upload(self.member, b"<html><script>alert(1)</script></html>", name="fake.png")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(FileUpload.objects.exists())

    def test_svg_is_rejected(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        response = self._upload(self.member, svg, name="image.svg", content_type="image/svg+xml")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(FileUpload.objects.exists())

    def test_too_large_image_is_rejected(self):
        with mock.patch("dojo.test.ui.views.FINDING_IMAGE_MAX_SIZE", 10):
            response = self._upload(self.member, _image_bytes())

        self.assertEqual(response.status_code, 400)
        self.assertFalse(FileUpload.objects.exists())

    def test_missing_image_is_rejected(self):
        response = self._client(self.member).post(reverse("upload_finding_image", args=(self.test.id,)))

        self.assertEqual(response.status_code, 400)

    def test_user_without_access_to_test_is_denied(self):
        response = self._upload(self.outsider, _image_bytes())

        self.assertEqual(response.status_code, 403)
        self.assertFalse(FileUpload.objects.exists())

    def test_get_is_not_allowed(self):
        response = self._client(self.member).get(reverse("upload_finding_image", args=(self.test.id,)))

        self.assertEqual(response.status_code, 405)
