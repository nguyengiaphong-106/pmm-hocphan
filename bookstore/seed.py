"""Dữ liệu mẫu + ảnh bìa vẽ bằng Pillow. Chạy: flask --app app seed"""
import os
import secrets
import textwrap
from datetime import datetime, timedelta

from flask import current_app
from PIL import Image, ImageDraw, ImageFont

from extensions import db
from models import (CANCELLED, COMPLETED, PENDING, SHIPPING, Book, Category,
                    Order, OrderItem, StatusHistory, shipping_fee)

FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "C:/Windows/Fonts/arialbd.ttf", "/Library/Fonts/Arial Bold.ttf"]


def _font(size):
    for p in FONTS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def make_cover(title, color):
    img = Image.new("RGB", (300, 420), color)
    d = ImageDraw.Draw(img)
    d.rectangle([14, 14, 285, 405], outline=(255, 255, 255), width=2)
    y = 120
    for line in textwrap.wrap(title, 13):
        w = d.textlength(line, font=_font(30))
        d.text(((300 - w) / 2, y), line, font=_font(30), fill=(255, 255, 255))
        y += 42
    name = f"{secrets.token_hex(8)}.png"
    img.save(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
    return name


def seed():
    if db.session.query(Category).count():
        print("CSDL đã có dữ liệu, bỏ qua.")
        return
    cats = {n: Category(name=n) for n in
            ["Lập trình", "Cơ sở dữ liệu", "Công cụ", "Mạng",
             "Kỹ năng lập trình", "Thiết kế"]}
    db.session.add_all(cats.values())

    data = [  # tên, tác giả, NXB, năm, danh mục, giá, tồn, màu
        ("Lập trình Python cơ bản", "Nguyễn Văn A", "NXB Đại học Huế", 2024, "Lập trình", 95000, 30, (31, 78, 74)),
        ("Giáo trình Flask", "Miguel Grinberg", "O'Reilly", 2018, "Lập trình", 120000, 20, (52, 96, 140)),
        ("Cơ sở dữ liệu", "Trần Văn B", "NXB Giáo dục", 2020, "Cơ sở dữ liệu", 85000, 0, (120, 72, 60)),
        ("Pro Git", "Scott Chacon", "Apress", 2014, "Công cụ", 150000, 15, (60, 60, 70)),
        ("Mạng máy tính", "Lê Văn C", "NXB Khoa học", 2019, "Mạng", 110000, 12, (140, 90, 40)),
        ("Clean Code", "Robert C. Martin", "Prentice Hall", 2008, "Kỹ năng lập trình", 180000, 5, (90, 50, 110)),
    ]
    books = []
    for i, (t, a, p, y, c, price, stock, color) in enumerate(data):
        b = Book(title=t, author=a, publisher=p, year=y, category=cats[c],
                 price=price, stock=stock, cover=make_cover(t, color),
                 description=f"{t} – tài liệu dành cho sinh viên Công nghệ Thông tin.",
                 created_at=datetime.now() - timedelta(days=30 - i))
        books.append(b)
    db.session.add_all(books)
    db.session.flush()

    now = datetime.now()
    demo = [  # khách, sđt, [(chỉ số sách, sl)], trạng thái, số ngày trước
        ("Phạm Minh Dũng", "0933333333", [(0, 1)], CANCELLED, 12),
        ("Lê Hoàng Cường", "0922222222", [(5, 1)], COMPLETED, 6),
        ("Trần Thị Bình", "0911111111", [(1, 1), (4, 1)], SHIPPING, 3),
        ("Võ Quốc Khánh", "0901234567", [(3, 1), (4, 1)], PENDING, 2),
        ("Nguyễn Văn An", "0912345678", [(0, 2), (1, 1), (3, 1)], PENDING, 1),
    ]
    for name, phone, items, status, ago in demo:
        placed = now - timedelta(days=ago)
        subtotal = sum(books[i].price * q for i, q in items)
        fee = shipping_fee(subtotal)
        o = Order(customer_name=name, phone=phone, address="12 Lê Lợi, phường Thuận Hoá, Huế",
                  payment="cod", shipping_fee=fee, total=subtotal + fee, status=status,
                  created_at=placed,
                  items=[OrderItem(book_id=books[i].id, unit_price=books[i].price, quantity=q)
                         for i, q in items],
                  history=[StatusHistory(status=PENDING, changed_at=placed)])
        if status != PENDING:
            o.history.append(StatusHistory(status=SHIPPING if status != CANCELLED else CANCELLED,
                                           changed_at=placed + timedelta(hours=3)))
        if status == COMPLETED:
            o.history.append(StatusHistory(status=COMPLETED, changed_at=placed + timedelta(days=1)))
        db.session.add(o)
    db.session.commit()
    print("Đã tạo dữ liệu mẫu.")
