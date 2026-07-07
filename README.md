# PMEDIA - ĐĂNG BÀI TỰ ĐỘNG WORDPRESS

Desktop app Python để đọc Excel và đăng bài lên WordPress qua REST API. App hỗ trợ ảnh local theo mã bài, preview trước khi đăng, đăng thủ công, lịch tự động, xuất Excel kèm link bài viết và lưu lịch sử chạy.

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
- `slug`
- `meta_description`

Nếu `status` trống, app dùng `draft` để tránh public ngoài ý muốn.

App cũng tự nhận sheet `Bài SEO HTML` với cột tiếng Việt:

- `Nội dung HTML thuần` -> nội dung WordPress, giữ nguyên H2/H3/P
- `Slug` -> slug bài viết
- `Tiêu đề SEO` -> title WordPress và Rank Math SEO title
- `Mô tả Meta SEO` -> excerpt WordPress và Rank Math description
- `Danh mục` -> category
- `Từ khóa chính` và `Từ khóa phụ đã phủ thêm` -> Rank Math focus keyword
- `tags`, `tag`, `Thẻ WordPress` -> WordPress tags nếu muốn gắn thẻ thủ công

Nếu HTML trong cột `Nội dung HTML thuần` đã có ảnh dạng `<img src="ma-bai_1.jpg">`,
app sẽ upload ảnh local lên WordPress rồi thay `src` local bằng URL ảnh trong Media Library.
Nếu chưa chọn thư mục ảnh, app sẽ tự dò thư mục hoặc file `.zip` ảnh nằm cùng thư mục với file Excel.

## Rank Math SEO fields

App gửi các field SEO sau vào WordPress REST API:

- `meta.rank_math_title`
- `meta.rank_math_description`
- `meta.rank_math_focus_keyword`

WordPress/Rank Math thường không cho ghi các post meta này qua REST API nếu site chưa đăng ký `show_in_rest`.
Nếu ô Tiêu đề SEO, Thẻ mô tả hoặc Từ khóa chính trong Rank Math vẫn trống sau khi đăng, cài plugin hỗ trợ trong:

`wordpress/wordpress-auto-poster-rank-math-rest-meta.zip`

Cách dùng nhanh:

1. Vào WordPress Admin -> Plugins -> Add New -> Upload Plugin.
2. Upload file `wordpress-auto-poster-rank-math-rest-meta.zip`.
3. Cài và kích hoạt plugin.
4. Chạy lại app. Nếu bài đã tồn tại, app sẽ cập nhật SEO meta cho bài trùng thay vì bỏ qua hoàn toàn.

## Quy ước ảnh local

Đặt ảnh trong cùng một thư mục:

```text
{ma_bai}_bg.jpg
{ma_bai}_thumb.jpg
{ma_bai}_1.jpg
{ma_bai}_2.png
{ma_bai}_3.webp
```

`_bg`, `_thumb`, `_thumbnail` hoặc `_featured` là ảnh đại diện/thumb. Ảnh này được upload làm ảnh đại diện WordPress và cũng được chèn làm hình đầu tiên trong nội dung bài. Các ảnh `_1`, `_2`, ... được upload và chèn tiếp theo trong nội dung; mặc định app dùng 2 ảnh nội dung sau ảnh thumb.

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
