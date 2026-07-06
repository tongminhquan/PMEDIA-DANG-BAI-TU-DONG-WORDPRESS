from __future__ import annotations

from pathlib import Path


OUTPUT_XLSX = Path("docs/Mau_Excel_Dang_Bai_SEO_HTML_WordPress.xlsx")
OUTPUT_IMAGES = Path("docs/mau_ten_hinh_anh")


def main() -> int:
    try:
        import pandas as pd
        from PIL import Image, ImageDraw
    except ImportError as exc:
        print(f"Missing dependency: {exc}")
        return 1

    OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_IMAGES.mkdir(parents=True, exist_ok=True)

    posts = [
        {
            "STT": 1,
            "ma_bai": "thang-may-gia-dinh",
            "Từ khóa chính": "thang máy gia đình",
            "Từ khóa phụ đã phủ thêm": "kích thước thang máy gia đình, báo giá thang máy gia đình, thang máy mini",
            "Tiêu đề SEO": "Thang Máy Gia Đình: Báo Giá, Kích Thước Và Kinh Nghiệm Lựa Chọn",
            "Nội dung HTML thuần": (
                "<h2>Thang Máy Gia Đình: Báo Giá, Kích Thước Và Kinh Nghiệm Lựa Chọn</h2>\n"
                "<p><strong>thang máy gia đình</strong> là giải pháp giúp nhà ở tiện nghi hơn.</p>\n"
                "<h3>Khi nào nên lắp thang máy gia đình?</h3>\n"
                "<p>Nên cân nhắc khi nhà có người lớn tuổi, trẻ nhỏ hoặc nhiều tầng.</p>\n"
                "<h3>Cần chuẩn bị gì trước khi lắp?</h3>\n"
                "<p>Chuẩn bị kích thước hố thang, tải trọng, ngân sách và đơn vị khảo sát.</p>"
            ),
            "Slug": "thang-may-gia-dinh",
            "Mô tả Meta SEO": "Tư vấn thang máy gia đình an toàn, phù hợp công trình tại Biên Hòa, Đồng Nai.",
            "Danh mục": "Tin Tức",
            "status": "draft",
        },
        {
            "STT": 2,
            "ma_bai": "thang-may-kinh",
            "Từ khóa chính": "thang máy kính",
            "Từ khóa phụ đã phủ thêm": "thang máy kính Biên Hòa, thang máy gia đình, thang máy biệt thự",
            "Tiêu đề SEO": "Thang Máy Kính Là Gì? Ưu Điểm, Nhược Điểm Và Báo Giá Mới Nhất",
            "Nội dung HTML thuần": (
                "<h2>Thang Máy Kính Là Gì? Ưu Điểm, Nhược Điểm Và Báo Giá Mới Nhất</h2>\n"
                "<p><strong>thang máy kính</strong> phù hợp các công trình cần không gian mở và thẩm mỹ cao.</p>\n"
                "<h3>Ưu điểm của thang máy kính</h3>\n"
                "<p>Thiết kế sáng, sang trọng và giúp không gian có cảm giác rộng hơn.</p>\n"
                "<h3>Lưu ý khi chọn thang máy kính</h3>\n"
                "<p>Cần kiểm tra vị trí lắp đặt, độ riêng tư, vật liệu kính và bảo trì.</p>"
            ),
            "Slug": "thang-may-kinh",
            "Mô tả Meta SEO": "Tổng quan thang máy kính, ưu nhược điểm và lưu ý chọn đơn vị lắp đặt tại Biên Hòa.",
            "Danh mục": "Tin Tức",
            "status": "draft",
        },
        {
            "STT": 3,
            "ma_bai": "thang-may-tai-hang",
            "Từ khóa chính": "thang máy tải hàng",
            "Từ khóa phụ đã phủ thêm": "thang máy tải hàng Biên Hòa, thang máy tải hàng Đồng Nai, thang máy kho hàng",
            "Tiêu đề SEO": "Thang Máy Tải Hàng: Cấu Tạo, Tải Trọng Và Chi Phí Lắp Đặt",
            "Nội dung HTML thuần": (
                "<h2>Thang Máy Tải Hàng: Cấu Tạo, Tải Trọng Và Chi Phí Lắp Đặt</h2>\n"
                "<p><strong>thang máy tải hàng</strong> giúp vận chuyển hàng hóa ổn định và an toàn hơn.</p>\n"
                "<h3>Cấu tạo cơ bản</h3>\n"
                "<p>Gồm cabin, ray dẫn hướng, máy kéo hoặc hệ thủy lực và hệ điều khiển.</p>\n"
                "<h3>Cách chọn tải trọng</h3>\n"
                "<p>Chọn theo loại hàng, kích thước hàng, tần suất vận hành và mặt bằng.</p>"
            ),
            "Slug": "thang-may-tai-hang",
            "Mô tả Meta SEO": "Tư vấn cấu tạo, tải trọng và chi phí lắp đặt thang máy tải hàng cho nhà xưởng, kho hàng.",
            "Danh mục": "Tin Tức",
            "status": "draft",
        },
    ]

    naming_rows = [
        {
            "Mẫu tên file": "{ma_bai}_bg.jpg",
            "Ý nghĩa": "Ảnh đại diện / featured image của bài",
            "Ví dụ": "thang-may-gia-dinh_bg.jpg",
        },
        {
            "Mẫu tên file": "{ma_bai}_1.jpg",
            "Ý nghĩa": "Ảnh nội dung thứ 1, chèn vào bài",
            "Ví dụ": "thang-may-gia-dinh_1.jpg",
        },
        {
            "Mẫu tên file": "{ma_bai}_2.png",
            "Ý nghĩa": "Ảnh nội dung thứ 2, chèn sau ảnh 1",
            "Ví dụ": "thang-may-gia-dinh_2.png",
        },
        {
            "Mẫu tên file": "{ma_bai}_3.webp",
            "Ý nghĩa": "Ảnh nội dung thứ 3 hoặc các ảnh tiếp theo",
            "Ví dụ": "thang-may-gia-dinh_3.webp",
        },
        {
            "Mẫu tên file": "ten-sai.jpg",
            "Ý nghĩa": "Không khớp ma_bai nào, app sẽ báo ảnh không khớp",
            "Ví dụ": "anh-khong-khop.jpg",
        },
    ]

    checklist_rows = [
        {"Mục kiểm tra": "Sheet tên Bài SEO HTML", "Đạt khi": "Có đủ cột Tiêu đề SEO và Nội dung HTML thuần"},
        {"Mục kiểm tra": "ma_bai", "Đạt khi": "Mỗi bài có một mã ngắn, không dấu, không khoảng trắng"},
        {"Mục kiểm tra": "Tên ảnh", "Đạt khi": "Tên ảnh bắt đầu bằng đúng ma_bai + dấu gạch dưới"},
        {"Mục kiểm tra": "Ảnh đại diện", "Đạt khi": "Có file {ma_bai}_bg nếu muốn set featured image"},
        {"Mục kiểm tra": "Ảnh nội dung", "Đạt khi": "Đánh số tăng dần: _1, _2, _3"},
        {"Mục kiểm tra": "Trạng thái", "Đạt khi": "status là draft nếu chưa muốn public ngay"},
    ]

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        pd.DataFrame(posts).to_excel(writer, sheet_name="Bài SEO HTML", index=False)
        pd.DataFrame(naming_rows).to_excel(writer, sheet_name="Quy ước đặt tên ảnh", index=False)
        pd.DataFrame(checklist_rows).to_excel(writer, sheet_name="Checklist trước khi đăng", index=False)

        workbook = writer.book
        for sheet in workbook.worksheets:
            sheet.freeze_panes = "A2"
            for cell in sheet[1]:
                cell.style = "Headline 3"
            for column_cells in sheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 14), 46)

    sample_images = [
        ("thang-may-gia-dinh_bg.jpg", "#2E74B5"),
        ("thang-may-gia-dinh_1.jpg", "#8EC5FC"),
        ("thang-may-gia-dinh_2.jpg", "#F4A261"),
        ("thang-may-kinh_bg.jpg", "#1F4D78"),
        ("thang-may-kinh_1.jpg", "#94D2BD"),
        ("thang-may-tai-hang_bg.jpg", "#7A5A00"),
        ("thang-may-tai-hang_1.jpg", "#E9C46A"),
        ("anh-khong-khop.jpg", "#777777"),
    ]
    for filename, color in sample_images:
        image = Image.new("RGB", (1200, 800), color)
        draw = ImageDraw.Draw(image)
        draw.rectangle((40, 40, 1160, 760), outline="white", width=6)
        draw.text((80, 90), filename, fill="white")
        draw.text((80, 150), "Ten file mau de app nhan dien anh thuoc bai nao", fill="white")
        image.save(OUTPUT_IMAGES / filename, quality=88)

    print(OUTPUT_XLSX)
    print(OUTPUT_IMAGES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
