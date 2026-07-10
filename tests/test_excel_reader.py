from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from wp_auto_poster_gui.core.excel_reader import (
    ExcelValidationError,
    read_post_updates_from_excel,
    read_posts_from_excel,
)


class ExcelReaderTest(unittest.TestCase):
    def test_reads_vietnamese_seo_html_sheet(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas is not installed")

        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "seo.xlsx"
            with pd.ExcelWriter(workbook) as writer:
                pd.DataFrame({"Ghi chú": ["không phải dữ liệu bài"]}).to_excel(
                    writer,
                    sheet_name="Tổng quan",
                    index=False,
                )
                pd.DataFrame(
                    [
                        {
                            "STT": 1,
                            "Từ khóa chính": "thang máy gia đình",
                            "Từ khóa phụ đã phủ thêm": "thang máy kính, thang máy mini",
                            "Tiêu đề SEO": "Thang Máy Gia Đình",
                            "Nội dung HTML thuần": "<h2>Thang Máy Gia Đình</h2><h3>Mục 1</h3><p>Nội dung</p>",
                            "Slug": "thang-may-gia-dinh",
                            "Mô tả Meta SEO": "Mô tả ngắn",
                            "Danh mục": "Tin Tức",
                        }
                    ]
                ).to_excel(writer, sheet_name="Bài SEO HTML", index=False)

            posts = read_posts_from_excel(workbook)

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, "Thang Máy Gia Đình")
        self.assertIn("<h3>Mục 1</h3>", posts[0].content)
        self.assertEqual(posts[0].slug, "thang-may-gia-dinh")
        self.assertEqual(posts[0].seo_title, "Thang Máy Gia Đình")
        self.assertEqual(posts[0].meta_description, "Mô tả ngắn")
        self.assertEqual(posts[0].category, "Tin Tức")
        self.assertEqual(posts[0].tags, [])
        self.assertEqual(posts[0].focus_keywords, ["thang máy gia đình", "thang máy kính", "thang máy mini"])

    def test_uses_slug_as_image_code_when_ma_bai_is_missing(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas is not installed")

        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "seo.xlsx"
            pd.DataFrame(
                [
                    {
                        "Tiêu đề SEO": "Xịt Côn Trùng",
                        "Nội dung HTML": "<p>Nội dung</p>",
                        "Slug": "/xit-con-trung/",
                        "Mô tả": "Mô tả SEO",
                    }
                ]
            ).to_excel(workbook, sheet_name="30 Bài SEO HTML", index=False)

            posts = read_posts_from_excel(workbook)

        self.assertEqual(posts[0].slug, "/xit-con-trung/")
        self.assertEqual(posts[0].ma_bai, "xit-con-trung")
        self.assertEqual(posts[0].meta_description, "Mô tả SEO")

    def test_reads_secondary_keywords_with_common_separators(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas is not installed")

        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "keywords.xlsx"
            pd.DataFrame(
                [
                    {
                        "Tiêu đề SEO": "Bài SEO",
                        "Nội dung HTML": "<p>Nội dung</p>",
                        "Từ khóa chính": "từ khóa chính",
                        "Từ khóa phụ": "từ phụ 1; từ phụ 2\ntừ phụ 3 | từ phụ 1",
                    }
                ]
            ).to_excel(workbook, sheet_name="Bài SEO HTML", index=False)

            posts = read_posts_from_excel(workbook)

        self.assertEqual(posts[0].primary_keyword, "từ khóa chính")
        self.assertEqual(posts[0].secondary_keywords, ["từ phụ 1", "từ phụ 2", "từ phụ 3"])
        self.assertEqual(
            posts[0].focus_keywords,
            ["từ khóa chính", "từ phụ 1", "từ phụ 2", "từ phụ 3"],
        )

    def test_allows_multiple_keywords_in_primary_column_for_legacy_files(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas is not installed")

        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "legacy-keywords.xlsx"
            pd.DataFrame(
                [
                    {
                        "Tiêu đề SEO": "Bài SEO",
                        "Nội dung HTML": "<p>Nội dung</p>",
                        "Từ khóa chính": "từ khóa chính, từ phụ 1, từ phụ 2",
                    }
                ]
            ).to_excel(workbook, sheet_name="Bài SEO HTML", index=False)

            posts = read_posts_from_excel(workbook)

        self.assertEqual(posts[0].primary_keyword, "từ khóa chính")
        self.assertEqual(posts[0].secondary_keywords, ["từ phụ 1", "từ phụ 2"])

    def test_reads_partial_updates_with_identifier_columns(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas is not installed")

        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "updates.xlsx"
            pd.DataFrame(
                [
                    {
                        "ID": 101,
                        "Mô tả Meta SEO": "Mô tả mới",
                        "Từ khóa chính": "kw một, kw hai",
                    },
                    {
                        "Link bài viết": "https://example.com/bai-hai/",
                        "Danh mục": "Tin Tức",
                    },
                ]
            ).to_excel(workbook, sheet_name="Cập nhật", index=False)

            updates = read_post_updates_from_excel(workbook)

        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[0].post_id, 101)
        self.assertEqual(updates[0].meta_description, "Mô tả mới")
        self.assertEqual(updates[0].focus_keywords, ["kw một", "kw hai"])
        self.assertIsNone(updates[0].title)
        self.assertIsNone(updates[0].content)
        self.assertIsNone(updates[0].link)
        self.assertIsNone(updates[1].post_id)
        self.assertEqual(updates[1].link, "https://example.com/bai-hai/")
        self.assertEqual(updates[1].category, "Tin Tức")
        self.assertIsNone(updates[1].meta_description)

    def test_update_rows_require_an_identifier(self) -> None:
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas is not installed")

        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "updates.xlsx"
            pd.DataFrame(
                [{"ID": None, "Mô tả Meta SEO": "Thiếu định danh"}]
            ).to_excel(workbook, index=False)

            with self.assertRaises(ExcelValidationError):
                read_post_updates_from_excel(workbook)


if __name__ == "__main__":
    unittest.main()
