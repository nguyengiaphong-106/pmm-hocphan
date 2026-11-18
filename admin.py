"""Phần B – Trang quản trị ⑥–⑪ (prefix /admin)."""
import os
import secrets
from datetime import datetime, timedelta

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, url_for)
from sqlalchemy import func, or_, select, update

from extensions import db
from forms import BookForm, CategoryForm
from models import (CANCELLED, COMPLETED, LOW_STOCK, PENDING, STATUS_LABELS,
                    STATUS_ORDER, TRANSITIONS, Book, Category, Order,
                    OrderItem, StatusHistory)

bp = Blueprint("admin", __name__, url_prefix="/admin")

BOOKS_PER_PAGE = 5
ORDERS_PER_PAGE = 10


# ---- Ảnh bìa ----------------------------------------------------------
def save_cover(file_storage):
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    name = f"{secrets.token_hex(8)}.{ext}"          # tên ngẫu nhiên
    file_storage.save(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
    return name


def remove_cover(name):
    if name:
        try:
            os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
        except OSError:
            pass


# ⑥ Tổng quan ------------------------------------------------------------
@bp.route("/")
def dashboard():
    s = db.session
    book_count = s.scalar(select(func.count(Book.id)))
    pending = s.scalar(select(func.count(Order.id)).where(Order.status == PENDING))
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    done_in_month = select(StatusHistory.order_id).where(
        StatusHistory.status == COMPLETED, StatusHistory.changed_at >= month_start)
    revenue = s.scalar(select(func.coalesce(func.sum(Order.total), 0)).where(
        Order.status == COMPLETED, Order.id.in_(done_in_month)))

    low_books = s.scalars(select(Book).where(Book.stock <= LOW_STOCK)
                          .order_by(Book.stock, Book.title)).all()
    latest = s.scalars(select(Order).order_by(Order.id.desc()).limit(5)).all()

    # Biểu đồ doanh thu 7 ngày (đơn hoàn tất theo ngày hoàn tất)
    today = now.date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    day_expr = func.date(StatusHistory.changed_at)
    rows = s.execute(
        select(day_expr, func.sum(Order.total))
        .join(Order, Order.id == StatusHistory.order_id)
        .where(StatusHistory.status == COMPLETED, Order.status == COMPLETED,
               StatusHistory.changed_at >= datetime.combine(days[0], datetime.min.time()))
        .group_by(day_expr)).all()
    by_day = {str(d): int(v) for d, v in rows}
    chart = [(d, by_day.get(d.isoformat(), 0)) for d in days]
    chart_max = max([v for _, v in chart] + [1])

    return render_template("admin/dashboard.html", book_count=book_count,
                           pending=pending, revenue=revenue, month=now.month,
                           low_books=low_books, latest=latest, chart=chart,
                           chart_max=chart_max)


# ⑦ Quản lý sách ---------------------------------------------------------
@bp.route("/books")
def books():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", type=int)
    stock = request.args.get("stock", "")
    page = request.args.get("page", 1, type=int)

    stmt = select(Book).order_by(Book.created_at.desc(), Book.id.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Book.title.ilike(like), Book.author.ilike(like)))
    if cat:
        stmt = stmt.where(Book.category_id == cat)
    if stock == "in":
        stmt = stmt.where(Book.stock > 0)
    elif stock == "low":
        stmt = stmt.where(Book.stock <= LOW_STOCK)
    elif stock == "out":
        stmt = stmt.where(Book.stock == 0)

    pagination = db.paginate(stmt, page=page, per_page=BOOKS_PER_PAGE, error_out=False)
    ids = [b.id for b in pagination.items]
    ordered = set(db.session.scalars(
        select(OrderItem.book_id).where(OrderItem.book_id.in_(ids)))) if ids else set()
    categories = db.session.scalars(select(Category).order_by(Category.name)).all()
    return render_template("admin/books.html", pagination=pagination, ordered=ordered,
                           categories=categories, q=q, cat=cat, stock=stock)


# ⑧ Thêm / sửa sách (dùng chung một form, một template) -------------------
FIELDS = ["title", "author", "publisher", "year", "category_id",
          "price", "stock", "description"]


@bp.route("/books/new", methods=["GET", "POST"])
@bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def book_form(book_id=None):
    book = db.get_or_404(Book, book_id) if book_id else None
    form = BookForm(obj=book, book_id=book_id)
    if not db.session.scalar(select(func.count(Category.id))):
        flash("Hãy tạo ít nhất một danh mục trước khi thêm sách.", "warning")
        return redirect(url_for("admin.categories"))

    if form.validate_on_submit():
        if book is None:
            book = Book()
            db.session.add(book)
        for name in FIELDS:
            setattr(book, name, getattr(form, name).data)
        f = form.cover_file.data
        if f and getattr(f, "filename", ""):
            remove_cover(book.cover)             # chọn ảnh mới thì xoá ảnh cũ
            book.cover = save_cover(f)
        db.session.commit()
        flash("Đã lưu sách.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", form=form, book=book)


@bp.post("/books/<int:book_id>/delete")
def book_delete(book_id):
    book = db.get_or_404(Book, book_id)
    if db.session.scalar(select(func.count(OrderItem.id)).where(OrderItem.book_id == book.id)):
        flash(f"Không thể xoá “{book.title}”: sách đã có trong đơn hàng.", "danger")
    else:
        remove_cover(book.cover)
        db.session.delete(book)
        db.session.commit()
        flash(f"Đã xoá “{book.title}”.", "success")
    return redirect(url_for("admin.books"))


# ⑨ Danh mục -------------------------------------------------------------
@bp.route("/categories", methods=["GET", "POST"])
@bp.route("/categories/<int:cat_id>/edit", methods=["GET", "POST"])
def categories(cat_id=None):
    editing = db.get_or_404(Category, cat_id) if cat_id else None
    form = CategoryForm(obj=editing, category_id=cat_id)
    if form.validate_on_submit():
        if editing is None:
            editing = Category()
            db.session.add(editing)
        editing.name = form.name.data
        editing.description = form.description.data or None
        db.session.commit()
        flash("Đã lưu danh mục.", "success")
        return redirect(url_for("admin.categories"))
    rows = db.session.execute(
        select(Category, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id).order_by(Category.id)).all()
    return render_template("admin/categories.html", rows=rows, form=form, editing=editing)


@bp.post("/categories/<int:cat_id>/delete")
def category_delete(cat_id):
    cat = db.get_or_404(Category, cat_id)
    n = db.session.scalar(select(func.count(Book.id)).where(Book.category_id == cat.id))
    if n:
        flash(f"Không thể xoá “{cat.name}”: còn {n} sách.", "danger")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash(f"Đã xoá danh mục “{cat.name}”.", "success")
    return redirect(url_for("admin.categories"))


# ⑩ Danh sách đơn hàng ----------------------------------------------------
@bp.route("/orders")
def orders():
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    if status not in STATUS_LABELS:
        status = ""

    conds = []
    if status:
        conds.append(Order.status == status)
    if q:
        like = f"%{q}%"
        parts = [Order.customer_name.ilike(like), Order.phone.like(like)]
        code = q.lstrip("#")
        if code.isdigit():
            parts.append(Order.id == int(code))
        conds.append(or_(*parts))

    pagination = db.paginate(select(Order).where(*conds).order_by(Order.id.desc()),
                             page=page, per_page=ORDERS_PER_PAGE, error_out=False)
    count, total = db.session.execute(
        select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0))
        .where(*conds)).one()
    per_status = dict(db.session.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)).all())
    tabs = [("", "Tất cả", sum(per_status.values()))] + [
        (k, STATUS_LABELS[k], per_status.get(k, 0)) for k in STATUS_ORDER]
    return render_template("admin/orders.html", pagination=pagination, tabs=tabs,
                           status=status, q=q, count=count, total=total)


# ⑪ Chi tiết đơn ---------------------------------------------------------
def change_status(order, new):
    """Đổi trạng thái hợp lệ; huỷ đơn thì hoàn lại tồn kho."""
    if new not in TRANSITIONS[order.status]:
        return False
    if new == CANCELLED:
        for it in order.items:
            db.session.execute(update(Book).where(Book.id == it.book_id)
                               .values(stock=Book.stock + it.quantity))
    order.status = new
    order.history.append(StatusHistory(status=new))
    db.session.commit()
    return True


@bp.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template("admin/order_detail.html", order=order)


@bp.post("/orders/<int:order_id>/status")
def order_status(order_id):
    order = db.get_or_404(Order, order_id)
    new = request.form.get("status", "")
    if change_status(order, new):
        msg = "Đã huỷ đơn, tồn kho đã được hoàn lại." if new == CANCELLED \
            else f"Đã chuyển đơn #{order.id} sang “{STATUS_LABELS[new]}”."
        flash(msg, "success")
    else:
        flash("Không thể chuyển trạng thái này.", "danger")
    return redirect(url_for("admin.order_detail", order_id=order.id))
