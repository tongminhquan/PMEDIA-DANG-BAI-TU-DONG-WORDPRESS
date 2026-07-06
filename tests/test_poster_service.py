from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from wp_auto_poster_gui.core.models import Post, PosterOptions, UploadedMedia, WordPressConfig
from wp_auto_poster_gui.core.poster_service import publish_posts
from wp_auto_poster_gui.core.poster_service import publish_from_excel


class FakeClient:
    def __init__(self):
        self.created = []
        self.updated = []

    def find_post_by_title(self, title: str):
        if title == "Duplicate":
            return {"id": 99, "link": "https://example.com/duplicate"}
        return None

    def upload_media_from_path(self, path: Path) -> UploadedMedia:
        return UploadedMedia(100 + len(str(path)), f"https://cdn.example.com/{path.name}", path.name)

    def upload_media_from_url(self, url: str) -> UploadedMedia:
        return UploadedMedia(55, url, "remote.jpg")

    def create_post(self, post: Post, content: str, featured_media_id: int | None = None):
        self.created.append((post, content, featured_media_id))
        return {"link": f"https://example.com/{post.row_number}"}

    def update_post(self, post_id: int, post: Post, content: str, featured_media_id: int | None = None):
        self.updated.append((post_id, post, content, featured_media_id))
        return {"link": f"https://example.com/existing/{post_id}"}


class PosterServiceTest(unittest.TestCase):
    def test_publishes_with_local_images_and_updates_duplicate_seo(self) -> None:
        fake = FakeClient()
        posts = [
            Post(2, "First", "<p>A</p><p>B</p>", ma_bai="bai01"),
            Post(3, "Duplicate", "C", ma_bai="bai02", slug="duplicate", focus_keywords=["keyword"]),
        ]
        config = WordPressConfig("https://example.com", "u", "p")

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "bai01_bg.jpg").write_bytes(b"x")
            (folder / "bai01_1.jpg").write_bytes(b"x")
            (folder / "bai02_bg.jpg").write_bytes(b"x")
            (folder / "bai02_1.jpg").write_bytes(b"x")
            results, orphans = publish_posts(
                posts,
                config,
                PosterOptions(),
                image_folder=folder,
                client_factory=lambda _: fake,
            )

        self.assertEqual([result.status for result in results], ["success", "success"])
        self.assertEqual(orphans, [])
        self.assertEqual(len(fake.created), 1)
        self.assertEqual(len(fake.updated), 1)
        self.assertEqual(fake.updated[0][0], 99)
        self.assertIn("<img", fake.updated[0][2])
        self.assertIsNotNone(fake.updated[0][3])
        self.assertIn("<img", fake.created[0][1])
        self.assertIsNotNone(fake.created[0][2])

    def test_publish_from_excel_auto_detects_adjacent_image_zip(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas is not installed")

        fake = FakeClient()
        config = WordPressConfig("https://example.com", "u", "p")

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            excel_path = folder / "posts.xlsx"
            pd.DataFrame(
                [
                    {
                        "ma_bai": "bai01",
                        "Tiêu đề SEO": "First",
                        "Nội dung HTML thuần": "<p>A</p><p>B</p>",
                        "Slug": "first",
                        "Mô tả Meta SEO": "Meta",
                        "Từ khóa chính": "keyword",
                    }
                ]
            ).to_excel(excel_path, sheet_name="Bài SEO HTML", index=False)

            zip_path = folder / "anh_SEO_test.zip"
            with ZipFile(zip_path, "w") as archive:
                archive.writestr("bai01_bg.jpg", b"x")
                archive.writestr("bai01_1.jpg", b"x")

            results, orphans = publish_from_excel(
                excel_path,
                None,
                config,
                PosterOptions(),
                client_factory=lambda _: fake,
            )

        self.assertEqual([result.status for result in results], ["success"])
        self.assertEqual(orphans, [])
        self.assertEqual(len(fake.created), 1)
        self.assertIn("<img", fake.created[0][1])
        self.assertIsNotNone(fake.created[0][2])


if __name__ == "__main__":
    unittest.main()
