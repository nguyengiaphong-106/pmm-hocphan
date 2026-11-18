# Nhà sách Sông Hương (Flask)

Bài tập tổng hợp Chương 5–6: giỏ hàng (session), Flask-WTF, SQLAlchemy + migration, Jinja2/Bootstrap.

## Chạy

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

flask --app app db init          # chỉ lần đầu
flask --app app db migrate -m "khoi tao"
flask --app app db upgrade
flask --app app seed             # dữ liệu mẫu + ảnh bìa (Pillow)

flask --app app run --debug
```

Không dùng migration: `flask --app app init-db` rồi `flask --app app seed`.

- Trang bán hàng: http://127.0.0.1:5000/books
- Trang quản trị: http://127.0.0.1:5000/admin

## Cấu trúc

| File | Vai trò |
|---|---|
| `app.py` | App factory, filter `money`/`dt`, lệnh `seed`, `init-db` |
| `models.py` | Category, Book, Order, OrderItem, StatusHistory + hằng số trạng thái |
| `cart.py` | Giỏ hàng trong session `{book_id: số lượng}`, giá luôn lấy từ CSDL |
| `shop.py` | Màn ①–⑤ (danh sách, chi tiết, giỏ, thanh toán, thành công) |
| `admin.py` | Màn ⑥–⑪ (tổng quan, sách, danh mục, đơn hàng) |
| `forms.py` | CheckoutForm, BookForm, CategoryForm (Flask-WTF) |
| `seed.py` | Dữ liệu mẫu |

## Điểm cần lưu ý

- **CSRF**: bật toàn cục bằng `CSRFProtect`; mọi nút đều là form POST kèm `csrf_token`, xử lý xong chuyển hướng (PRG).
- **Đặt hàng**: trừ tồn kho bằng `UPDATE ... WHERE stock >= sl` (nguyên tử), thiếu hàng thì rollback, không tạo đơn.
- **Huỷ đơn**: hoàn lại tồn kho; chuyển trạng thái chỉ theo `TRANSITIONS` trong `models.py`.
- **Đơn giá** lưu ở `OrderItem.unit_price`; `Order.total` lưu cả phí giao để thống kê nhanh.
- **Xem đơn ⑤**: chỉ phiên đã đặt đơn đó mới xem được (`session["my_orders"]`).
- Tìm kiếm `ilike` của SQLite chỉ phân biệt hoa/thường với ký tự ASCII; kiểm tra trùng tên đã dùng `casefold()` nên đúng với tiếng Việt.
- Trang `/admin` **chưa có đăng nhập** (đề không yêu cầu). Muốn triển khai thật cần thêm Flask-Login.
