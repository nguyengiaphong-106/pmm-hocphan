# Quản lý sách - Flask + SQLite

Bài kiểm tra môn TIN4063.002 - Phần mềm mã nguồn mở (Nhóm 2).

## Chức năng
- CRUD danh mục sách
- CRUD sách theo danh mục (lọc theo danh mục, tìm theo tên hoặc tác giả)
- Dashboard thống kê số danh mục, số sách và biểu đồ số đầu sách theo danh mục
- Cơ sở dữ liệu SQLite (`instance/library.db`)

## Cách chạy
```
pip install -r requirements.txt
python app.py
```
Trên Windows nếu không có lệnh `python` thì dùng `py -m pip install -r requirements.txt` và `py app.py`.

Mở http://127.0.0.1:5000 trên trình duyệt.

Nếu xoá `instance/library.db`, chương trình sẽ tự tạo lại CSDL kèm dữ liệu mẫu khi chạy.
