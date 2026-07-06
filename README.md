# WordPress Auto Poster

Desktop app Python để đọc Excel và đăng bài lên WordPress qua REST API. App hỗ trợ ảnh local theo mã bài, preview trước khi đăng, đăng thủ công, lịch tự động và báo cáo kết quả.

## Cài đặt

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Excel đầu vào

Cột bắt buộc:

- `title`
- `content`

Cột tùy chọn:

- `ma_bai`
- `featured_image_url`
- `category`
- `tags`
- `status`
- `publish_date`

Nếu `status` trống, app dùng `draft` để tránh public ngoài ý muốn.

## Quy ước ảnh local

Đặt ảnh trong cùng một thư mục:

```text
{ma_bai}_bg.jpg
{ma_bai}_1.jpg
{ma_bai}_2.png
{ma_bai}_3.webp
```

`_bg` là ảnh đại diện. Các ảnh `_1`, `_2`, ... được upload và chèn đều vào nội dung.

## Sử dụng

1. Nhập URL WordPress, username và application password.
2. Bấm `Kiểm tra kết nối`.
3. Chọn file Excel.
4. Chọn thư mục ảnh nếu có.
5. Bấm `Preview`.
6. Bấm `Đăng ngay` và xác nhận.

Application password không được lưu vào `config/settings.json`; khi mở lại app cần nhập lại.

## Lịch tự động

Tab `Lịch tự động` cho phép chọn Excel, thư mục ảnh, tần suất hàng ngày, hàng tuần hoặc cron. Lịch chỉ chạy khi checkbox `Bật lịch tự động` được bật. Trong phiên hiện tại vẫn cần nhập application password để job có thể đăng bài.

## Tạo file mẫu

```powershell
python create_sample_excel.py
```

Lệnh này tạo `data/sample_posts.xlsx` và ảnh mẫu trong `data/sample_images/`.

## Kiểm tra core

```powershell
python -m unittest discover -s tests
```
