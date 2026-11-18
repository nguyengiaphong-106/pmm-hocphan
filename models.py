from datetime import datetime

from flask import url_for

from extensions import db

# ---- Hằng số nghiệp vụ -------------------------------------------------
PENDING, SHIPPING, COMPLETED, CANCELLED = "pending", "shipping", "completed", "cancelled"
STATUS_LABELS = {
    PENDING: "Chờ xác nhận",
    SHIPPING: "Đang giao",
    COMPLETED: "Hoàn tất",
    CANCELLED: "Đã huỷ",
}
STATUS_ORDER = [PENDING, SHIPPING, COMPLETED, CANCELLED]
# Chuyển trạng thái hợp lệ
TRANSITIONS = {
    PENDING: [SHIPPING, CANCELLED],
    SHIPPING: [COMPLETED, CANCELLED],
    COMPLETED: [],
    CANCELLED: [],
}
PAYMENT_LABELS = {"cod": "Tiền mặt khi nhận hàng", "bank": "Chuyển khoản"}
SHIPPING_FEE = 20_000
FREE_SHIP_FROM = 200_000
LOW_STOCK = 5


def shipping_fee(subtotal: int) -> int:
    return 0 if subtotal >= FREE_SHIP_FROM else SHIPPING_FEE


# ---- Mô hình -------------------------------------------------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)

    books = db.relationship("Book", back_populates="category")


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    publisher = db.Column(db.String(120))
    year = db.Column(db.Integer)
    price = db.Column(db.Integer, nullable=False)          # đồng, số nguyên
    stock = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text)
    cover = db.Column(db.String(100))                      # tên file ngẫu nhiên
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    category = db.relationship("Category", back_populates="books")

    @property
    def cover_url(self):
        if self.cover:
            return url_for("static", filename=f"uploads/{self.cover}")
        return url_for("static", filename="img/no-cover.svg")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    note = db.Column(db.String(500))
    payment = db.Column(db.String(10), nullable=False, default="cod")
    shipping_fee = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False)           # đã gồm phí giao
    status = db.Column(db.String(12), nullable=False, default=PENDING, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)

    items = db.relationship("OrderItem", back_populates="order",
                            cascade="all, delete-orphan")
    history = db.relationship("StatusHistory", back_populates="order",
                              cascade="all, delete-orphan",
                              order_by="StatusHistory.id")

    @property
    def subtotal(self):
        return sum(i.line_total for i in self.items)

    @property
    def allowed_next(self):
        return TRANSITIONS[self.status]


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)      # giá tại thời điểm đặt
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", back_populates="items")
    book = db.relationship("Book")

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class StatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    status = db.Column(db.String(12), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    order = db.relationship("Order", back_populates="history")
