# Cloud Edition — trạng thái MVP

## Đã có trong nhánh cloud-edition
- Ứng dụng Streamlit riêng cho Cloud, không phụ thuộc OBS/Roblox Studio/FFmpeg ở server.
- Password gate qua Streamlit Secrets.
- OpenAI API integration cho sinh JSON content.
- Supabase persistence adapter; session-only fallback có cảnh báo.
- Story, Character, World, Director, Sound, Thumbnail, SEO, Production Job, QC và Batch queue.
- JSON export cho nội dung và Production Job.
- Cloud-specific requirements, Streamlit config, .gitignore và SQL schema.

## Chưa có — không được hiểu là đã hoàn tất
- Windows Production Agent chạy nền và API xác thực/polling/callback.
- Upload artifact lớn từ Windows Agent lên cloud storage.
- Supabase Storage bucket provisioning và quản lý quyền truy cập file.
- Web OAuth YouTube và upload/scheduling.
- Multi-user auth, RBAC, per-user data isolation.
- Image generation trực tiếp; Thumbnail Studio chỉ đặt chữ lên ảnh nền tải lên.
- Tự tạo Roblox .rbxl hoặc thực thi script trong Roblox Studio từ Cloud.
- Automated end-to-end test trên Streamlit Community Cloud.
