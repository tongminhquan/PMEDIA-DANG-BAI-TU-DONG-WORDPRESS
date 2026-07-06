from __future__ import annotations

import unittest

from wp_auto_poster_gui.core.models import Post, WordPressConfig
from wp_auto_poster_gui.core.wp_client import WordPressClient


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200
        self.text = ""

    def json(self):
        return self._payload


class PayloadClient(WordPressClient):
    def __init__(self):
        try:
            super().__init__(WordPressConfig("https://example.com", "user", "pass"))
        except RuntimeError:
            raise unittest.SkipTest("requests is not installed")
        self.last_payload = None

    def _request(self, method: str, path: str, **kwargs):
        self.last_payload = kwargs.get("json")
        return _FakeResponse({"link": "https://example.com/post"})


class WordPressClientTest(unittest.TestCase):
    def test_create_post_includes_slug_and_excerpt(self) -> None:
        client = PayloadClient()
        post = Post(
            row_number=2,
            title="Title",
            content="<p>Body</p>",
            slug="custom-slug",
            meta_description="Meta description",
        )

        client.create_post(post, post.content)

        self.assertEqual(client.last_payload["slug"], "custom-slug")
        self.assertEqual(client.last_payload["excerpt"], "Meta description")


if __name__ == "__main__":
    unittest.main()
