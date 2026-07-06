from __future__ import annotations

import unittest

from wp_auto_poster_gui.core.content_composer import compose_content_with_images
from wp_auto_poster_gui.core.models import UploadedMedia


class ContentComposerTest(unittest.TestCase):
    def test_inserts_images_evenly_into_html_paragraphs(self) -> None:
        content = "<p>A</p><p>B</p><p>C</p>"
        images = [
            UploadedMedia(11, "https://example.com/1.jpg"),
            UploadedMedia(12, "https://example.com/2.jpg"),
        ]

        output = compose_content_with_images(content, "Demo", images)

        self.assertIn('class="wp-image-11 aligncenter"', output)
        self.assertIn('class="wp-image-12 aligncenter"', output)
        self.assertLess(output.index("wp-image-11"), output.index("wp-image-12"))
        self.assertEqual(output.count("<img"), 2)

    def test_returns_original_without_images(self) -> None:
        self.assertEqual(compose_content_with_images("A", "Demo", []), "A")


if __name__ == "__main__":
    unittest.main()
