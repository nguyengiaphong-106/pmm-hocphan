"""Giỏ hàng lưu trong session: {"<book_id>": số lượng}. Không lưu giá."""
from flask import session
from sqlalchemy import select

from extensions import db
from models import Book, shipping_fee


def get_cart() -> dict:
    return dict(session.get("cart", {}))


def save_cart(cart: dict):
    session["cart"] = cart
    session.modified = True


def cart_quantity(book_id: int) -> int:
    return get_cart().get(str(book_id), 0)


def cart_count() -> int:
    return sum(get_cart().values())


def clear_cart():
    session.pop("cart", None)


def cart_lines():
    """Trả về (danh sách dòng, tạm tính). Giá luôn lấy mới từ CSDL."""
    cart = get_cart()
    if not cart:
        return [], 0
    ids = [int(i) for i in cart]
    books = db.session.scalars(select(Book).where(Book.id.in_(ids))).all()
    lines, subtotal = [], 0
    for book in sorted(books, key=lambda b: ids.index(b.id)):
        qty = cart[str(book.id)]
        line_total = book.price * qty
        subtotal += line_total
        lines.append({"book": book, "quantity": qty, "line_total": line_total,
                      "over": qty > book.stock})
    # sách đã bị xoá khỏi CSDL thì bỏ khỏi giỏ
    alive = {str(b.id) for b in books}
    if alive != set(cart):
        save_cart({k: v for k, v in cart.items() if k in alive})
    return lines, subtotal


def cart_totals(subtotal: int):
    fee = shipping_fee(subtotal) if subtotal else 0
    return fee, subtotal + fee
