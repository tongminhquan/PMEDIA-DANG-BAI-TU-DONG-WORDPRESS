from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from wp_auto_poster_gui.core.models import Post, PosterOptions, UploadedMedia, WordPressConfig
from wp_auto_poster_gui.core.poster_service import publish_posts


class FakeClient:
    def __init__(self):
        self.created = []

    def check_duplicate_by_title(self, title: str) -> bool:
        return title == "Duplicate"

    def upload_media_from_path(self, path: Path) -> UploadedMedia:
        return UploadedMedia(100 + len(str(path)), f"https://cdn.example.com/{path.name}", path.name)

    def upload_media_from_url(self, url: str) -> UploadedMedia:
        return UploadedMedia(55, url, "remote.jpg")

    def create_post(self, post: Post, content: str, featured_media_id: int | None = None):
        self.created.append((post, content, featured_media_id))
        return {"link": f"https://example.com/{post.row_number}"}


class PosterServiceTest(unittest.TestCase):
    def test_publishes_with_local_images_and_skips_duplicates(self) -> None:
        fake = FakeClient()
        posts = [
            Post(2, "First", "<p>A</p><p>B</p>", ma_bai="bai01"),
            Post(3, "Duplicate", "C", ma_bai="bai02"),
        ]
        config = WordPressConfig("https://example.com", "u", "p")

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "bai01_bg.jpg").write_bytes(b"x")
            (folder / "bai01_1.jpg").write_bytes(b"x")
            results, orphans = publish_posts(
                posts,
                config,
                PosterOptions(),
                image_folder=folder,
                client_factory=lambda _: fake,
            )

        self.assertEqual([result.status for result in results], ["success", "skipped"])
        self.assertEqual(orphans, [])
        self.assertEqual(len(fake.created), 1)
        self.assertIn("<img", fake.created[0][1])
        self.assertIsNotNone(fake.created[0][2])


if __name__ == "__main__":
    unittest.main()
