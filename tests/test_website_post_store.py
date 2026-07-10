from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from wp_auto_poster_gui.core.website_post_store import WebsitePostStore


class WebsitePostStoreTest(unittest.TestCase):
    def test_saves_all_posts_for_connected_website(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = WebsitePostStore(Path(directory) / "website_posts.json")
            payloads = [
                {
                    "id": index,
                    "status": "publish" if index % 2 else "draft",
                    "title": {"rendered": f"Bài {index}"},
                    "slug": f"bai-{index}",
                    "date": "2026-07-10T09:00:00",
                    "modified": "2026-07-10T10:00:00",
                    "link": f"https://example.com/bai-{index}",
                }
                for index in range(1, 251)
            ]

            saved = store.save_snapshot("https://example.com/", payloads, synced_at="2026-07-10T10:30:00")
            loaded = WebsitePostStore(Path(directory) / "website_posts.json").get_snapshot("https://example.com")

        self.assertEqual(saved.total, 250)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.total, 250)
        self.assertEqual(len(loaded.posts), 250)
        self.assertEqual(loaded.posts[0].post_id, 1)
        self.assertEqual(loaded.posts[-1].post_id, 250)

    def test_keeps_snapshots_separate_for_multiple_websites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "website_posts.json"
            store = WebsitePostStore(path)
            store.save_snapshot("https://first.example", [{"id": 1, "title": {"rendered": "First"}}])
            store.save_snapshot("https://second.example/", [{"id": 2, "title": {"rendered": "Second"}}])

            first = store.get_snapshot("https://first.example/")
            second = store.get_snapshot("https://second.example")

        self.assertEqual(first.posts[0].title, "First")
        self.assertEqual(second.posts[0].title, "Second")

    def test_load_accepts_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "website_posts.json"
            path.write_text(
                '[{"site_url":"https://example.com","synced_at":"2026-07-10T10:30:00","total":0,"posts":[]}]',
                encoding="utf-8-sig",
            )

            snapshots = WebsitePostStore(path).load_snapshots()

        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].site_url, "https://example.com")


if __name__ == "__main__":
    unittest.main()
