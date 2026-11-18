# Quản Lý Sinh Viên (QLSV) - Flask & SQLAlchemy

Dự án Quản Lý Sinh Viên được thực hiện theo Slide Bài giảng Chương 6.

## Hướng dẫn cài đặt và chạy ứng dụng

1. Di chuyển vào thư mục dự án:
   cd qlsv

2. Tạo môi trường ảo:
   py -m venv .venv

3. Kích hoạt môi trường ảo (Windows PowerShell):
   .venv\Scripts\Activate.ps1

4. Cài đặt các thư viện cần thiết:
   pip install -r requirements.txt

5. Khởi chạy server ứng dụng:
   py -m flask --app app run --debug

6. Truy cập ứng dụng trên trình duyệt:
   - Trang chủ: http://127.0.0.1:5000/
   - Nạp dữ liệu mẫu: http://127.0.0.1:5000/them-mau
   - Thử nghiệm truy vấn: http://127.0.0.1:5000/thu-truy-van
