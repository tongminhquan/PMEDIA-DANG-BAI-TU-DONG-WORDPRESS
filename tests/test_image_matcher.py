from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from wp_auto_poster_gui.core.image_matcher import match_images_for_posts


class ImageMatcherTest(unittest.TestCase):
    def test_matches_background_content_and_orphans(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ["bai01_bg.JPG", "bai01_2.png", "bai01_1.webp", "bai02_1.jpg", "other.jpg"]:
                (folder / name).write_bytes(b"x")

            matches, orphans = match_images_for_posts(folder, ["bai01", "bai02"], max_images_per_post=1)

            self.assertEqual(matches["bai01"].background.name, "bai01_bg.JPG")
            self.assertEqual([path.name for path in matches["bai01"].content_images], ["bai01_1.webp"])
            self.assertEqual([path.name for path in matches["bai02"].content_images], ["bai02_1.jpg"])
            self.assertEqual([path.name for path in orphans], ["other.jpg"])


if __name__ == "__main__":
    unittest.main()
