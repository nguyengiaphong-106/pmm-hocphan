"""Phần A – Trang bán hàng ①–⑤."""
from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from sqlalchemy import or_, select, update

from cart import (cart_lines, cart_quantity, cart_totals, clear_cart, get_cart,
                  save_cart)
from extensions import db
from forms import CheckoutForm
from models import (PENDING, Book, Category, Order, OrderItem, StatusHistory,
                    shipping_fee)

bp = Blueprint("shop", __name__)


def safe_next(default):
    """Chỉ chấp nhận đường dẫn nội bộ để tránh open redirect."""
    nxt = request.form.get("next", "")
    if nxt.startswith("/") and not nxt.startswith("//") and "\\" not in nxt:
        return nxt
    return default


@bp.route("/")
def home():
    return redirect(url_for("shop.books"))


# ① Danh sách sách ------------------------------------------------------
@bp.route("/books")
def books():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", type=int)
    stmt = select(Book).order_by(Book.id.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Book.title.ilike(like), Book.author.ilike(like)))
    if cat:
        stmt = stmt.where(Book.category_id == cat)
    items = db.session.scalars(stmt).all()
    categories = db.session.scalars(select(Category).order_by(Category.name)).all()
    return render_template("books.html", books=items, categories=categories,
                           q=q, cat=cat)


# ② Chọn sách -----------------------------------------------------------
@bp.route("/books/<int:book_id>")
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)
    in_cart = cart_quantity(book.id)
    return render_template("book_detail.html", book=book, in_cart=in_cart,
                           max_qty=max(book.stock - in_cart, 0))


@bp.post("/cart/add/<int:book_id>")
def cart_add(book_id):
    book = db.get_or_404(Book, book_id)
    back = safe_next(url_for("shop.book_detail", book_id=book.id))
    try:
        qty = int(request.form.get("quantity", "1"))
    except ValueError:
        qty = 0
    in_cart = cart_quantity(book.id)
    room = book.stock - in_cart
    if book.stock <= 0:
        flash(f"“{book.title}” đã hết hàng.", "danger")
    elif room <= 0:
        flash(f"Bạn đã có đủ {in_cart} cuốn “{book.title}” (bằng tồn kho) trong giỏ.", "danger")
    elif not 1 <= qty <= room:
        flash(f"Số lượng không hợp lệ: chỉ được chọn từ 1 đến {room}.", "danger")
    else:
        cart = get_cart()
        cart[str(book.id)] = in_cart + qty
        save_cart(cart)
        flash(f"Đã thêm {qty} × {book.title} vào giỏ hàng.", "success")
    return redirect(back)


# ③ Giỏ hàng ------------------------------------------------------------
@bp.route("/cart")
def cart():
    lines, subtotal = cart_lines()
    return render_template("cart.html", lines=lines, subtotal=subtotal)


@bp.post("/cart/update/<int:book_id>")
def cart_update(book_id):
    cart = get_cart()
    key = str(book_id)
    book = db.session.get(Book, book_id)
    if key in cart and book:
        action = request.form.get("action")
        if action == "inc":
            if cart[key] + 1 > book.stock:
                flash(f"“{book.title}” chỉ còn {book.stock} cuốn.", "danger")
            else:
                cart[key] += 1
        elif action == "dec":
            cart[key] -= 1
            if cart[key] <= 0:
                del cart[key]
        save_cart(cart)
    return redirect(url_for("shop.cart"))


@bp.post("/cart/remove/<int:book_id>")
def cart_remove(book_id):
    cart = get_cart()
    if cart.pop(str(book_id), None) is not None:
        save_cart(cart)
        flash("Đã bỏ sách khỏi giỏ hàng.", "success")
    return redirect(url_for("shop.cart"))


@bp.post("/cart/clear")
def cart_clear():
    clear_cart()
    flash("Đã xoá toàn bộ giỏ hàng.", "success")
    return redirect(url_for("shop.cart"))


# ④ Thông tin khách hàng ------------------------------------------------
@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    lines, subtotal = cart_lines()
    if not lines:
        flash("Giỏ hàng đang trống, hãy chọn sách trước khi đặt hàng.", "warning")
        return redirect(url_for("shop.cart"))
    form = CheckoutForm()
    fee, total = cart_totals(subtotal)

    if form.validate_on_submit():
        # Trừ tồn kho nguyên tử: chỉ thành công khi stock >= số lượng đặt
        short = []
        for ln in lines:
            res = db.session.execute(
                update(Book)
                .where(Book.id == ln["book"].id, Book.stock >= ln["quantity"])
                .values(stock=Book.stock - ln["quantity"]))
            if res.rowcount == 0:
                short.append(f"“{ln['book'].title}” (còn {ln['book'].stock}, bạn chọn {ln['quantity']})")
        if short:
            db.session.rollback()
            flash("Không đủ hàng, đơn chưa được tạo: " + "; ".join(short) + ".", "danger")
            return redirect(url_for("shop.cart"))

        order = Order(
            customer_name=form.customer_name.data, phone=form.phone.data,
            address=form.address.data, email=form.email.data or None,
            note=form.note.data or None, payment=form.payment.data,
            shipping_fee=shipping_fee(subtotal), total=subtotal + shipping_fee(subtotal),
            status=PENDING,
            items=[OrderItem(book_id=ln["book"].id, unit_price=ln["book"].price,
                             quantity=ln["quantity"]) for ln in lines],
            history=[StatusHistory(status=PENDING)])
        db.session.add(order)
        db.session.commit()
        clear_cart()
        mine = session.get("my_orders", [])
        session["my_orders"] = mine + [order.id]
        flash("Đặt hàng thành công!", "success")
        return redirect(url_for("shop.order_done", order_id=order.id))

    return render_template("checkout.html", form=form, lines=lines,
                           subtotal=subtotal, fee=fee, total=total)


# ⑤ Đặt thành công ------------------------------------------------------
@bp.route("/orders/<int:order_id>")
def order_done(order_id):
    # chỉ chủ phiên đã đặt đơn này mới xem được (tránh dò mã đơn)
    if order_id not in session.get("my_orders", []):
        abort(404)
    order = db.get_or_404(Order, order_id)
    return render_template("order_done.html", order=order)
