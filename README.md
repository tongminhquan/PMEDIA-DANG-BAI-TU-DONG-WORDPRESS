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

1. Nhập URL WordPress, username và application password, hoặc chọn nhanh một website trong danh sách `Website đã lưu`.
2. Bấm `Kiểm tra kết nối`. Khi kết nối thành công, app tự lưu lại website này để lần sau chọn nhanh.
3. Chọn file Excel.
4. Chọn thư mục ảnh nếu có.
5. Bấm `Preview`.
6. Bấm `Đăng ngay` và xác nhận.

## Lưu nhiều website

App lưu URL, username và application password của từng website vào `config/settings.json` để lần sau không phải nhập lại.

- Bấm `💾 Lưu` hoặc `Kiểm tra kết nối` thành công để lưu website đang nhập.
- Chọn một mục trong `Website đã lưu` để điền lại thông tin kết nối.
- Bấm `Xóa website đã lưu` để gỡ website khỏi máy này.

Application password được mã hóa bằng Windows DPAPI theo tài khoản Windows hiện tại nên không lưu ở dạng chữ thường trong file cấu hình. Nếu chép `config/settings.json` sang máy khác hoặc tài khoản Windows khác, app không giải mã được password đã lưu và sẽ yêu cầu nhập lại.

## Lịch tự động

Tab `Lịch tự động` cho phép chọn Excel, thư mục ảnh, tần suất hàng ngày, hàng tuần hoặc cron. Lịch chỉ chạy khi checkbox `Bật lịch tự động` được bật. Job dùng application password đang có ở tab kết nối; nếu đã lưu website và DPAPI giải mã được, app tự điền sẵn password khi mở nên job chạy được ngay. Nếu ô password đang trống thì cần nhập lại để job có thể đăng bài.

## Tạo file mẫu

```powershell
python create_sample_excel.py
```

Lệnh này tạo `data/sample_posts.xlsx` và ảnh mẫu trong `data/sample_images/`.

## Kiểm tra core

```powershell
python -m unittest discover -s tests
```

## Từ khóa phụ Rank Math

App đưa từ khóa chính và toàn bộ từ khóa phụ vào cùng trường `rank_math_focus_keyword` của Rank Math. File Excel có thể dùng cột `Từ khóa phụ`, `Từ khóa phụ đã phủ thêm` hoặc `Secondary keywords`.

Các từ khóa có thể ngăn cách bằng dấu phẩy, dấu chấm phẩy, xuống dòng hoặc dấu `|`. Với file cũ không có cột từ khóa phụ, có thể ghi nhiều từ khóa ngay trong cột `Từ khóa chính`; app dùng giá trị đầu tiên làm từ khóa chính và các giá trị còn lại làm từ khóa phụ.

Bảng Preview hiển thị cột `Từ khóa Rank Math` và cảnh báo rõ bài nào chưa có từ khóa phụ. Plugin metadata bản 1.2.0 bổ sung endpoint đồng bộ riêng để ghi toàn bộ danh sách từ khóa; cần cập nhật lại file `wordpress/wordpress-auto-poster-rank-math-rest-meta.zip` trên WordPress.

## Lịch sử bài viết trên website

Tab `Lịch sử` có thêm mục `Toàn bộ bài trên website`. Khi kết nối thành công hoặc bấm `Đồng bộ toàn bộ bài`, app tải đủ các trang dữ liệu WordPress cho các trạng thái publish, draft, pending, future và private.

Snapshot được lưu riêng theo từng website tại `config/website_posts.json`, gồm ID, trạng thái, ngày đăng, ngày cập nhật, tiêu đề, slug và link. Dữ liệu gần nhất vẫn hiển thị sau khi đóng và mở lại app; không lưu mật khẩu trong file này.

## Cập nhật bài trên website từ file Excel

Tab `Bài trên website` có mục `3. Cập nhật nội dung từ file Excel` để sửa hàng loạt bài đang có trên website bằng dữ liệu trong Excel.

App nhận diện từng dòng Excel với bài trên website theo thứ tự ưu tiên: cột `ID` (ID bài WordPress) → `Link bài viết` hoặc `Slug` → `Tiêu đề SEO`. File "Excel gốc + link" mà app xuất ra sau khi đăng bài dùng được ngay cho luồng này.

Hai chế độ cập nhật:

- `Chỉ bổ sung trường còn thiếu` (mặc định): mỗi ô có dữ liệu trong Excel chỉ được ghi vào website khi bài đang thiếu trường đó (mô tả meta, từ khóa SEO, tiêu đề SEO, chuyên mục, tags, ảnh đại diện, nội dung trống...). Dữ liệu đã có trên web không bị ghi đè, kể cả từ khóa Rank Math.
- Bỏ tick để chuyển sang chế độ ghi đè: mọi ô có dữ liệu trong Excel sẽ thay thế giá trị hiện có (bao gồm nội dung, trạng thái, ngày đăng, slug).

Các ô để trống trong Excel luôn được bỏ qua, không bao giờ xóa dữ liệu trên website. Kết quả từng bài hiển thị ở bảng `4. Kết quả` kèm ghi chú trường nào đã được bổ sung, và được lưu vào tab `Lịch sử` với chế độ `Cập nhật bài từ Excel`.
