"""Quản lý sách - Flask + SQLite
Chạy:  pip install flask   rồi   python app.py   -> mở http://127.0.0.1:5000
CSDL instance/library.db được tạo tự động (kèm dữ liệu mẫu) nếu chưa có.
"""
import os
import sqlite3

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, "library.db")

app = Flask(__name__)
app.secret_key = "doi-khoa-bi-mat-nay"


# ---------------------------------------------------------------- Database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS books (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            author      TEXT DEFAULT '',
            year        INTEGER,
            price       INTEGER NOT NULL DEFAULT 0,
            quantity    INTEGER NOT NULL DEFAULT 0,
            category_id INTEGER NOT NULL,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
        );
        """
    )
    if db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO categories(name, description) VALUES (?, ?)",
            [
                ("Công nghệ thông tin", "Lập trình, CSDL, mạng máy tính"),
                ("Văn học", "Tiểu thuyết, truyện ngắn, thơ"),
                ("Kinh tế", "Quản trị, tài chính, khởi nghiệp"),
            ],
        )
        db.executemany(
            "INSERT INTO books(title, author, year, price, quantity, category_id) VALUES (?,?,?,?,?,?)",
            [
                ("Python cơ bản", "Nguyễn Văn A", 2022, 120000, 15, 1),
                ("Cơ sở dữ liệu SQLite", "Trần Thị B", 2021, 95000, 8, 1),
                ("Truyện Kiều", "Nguyễn Du", 2019, 70000, 20, 2),
                ("Dế Mèn phiêu lưu ký", "Tô Hoài", 2020, 60000, 12, 2),
                ("Khởi nghiệp tinh gọn", "Eric Ries", 2018, 150000, 5, 3),
            ],
        )
    db.commit()
    db.close()


# ---------------------------------------------------------------- Dashboard
@app.route("/")
def dashboard():
    db = get_db()
    totals = db.execute(
        """SELECT
             (SELECT COUNT(*) FROM categories)            AS n_categories,
             (SELECT COUNT(*) FROM books)                 AS n_titles,
             (SELECT COALESCE(SUM(quantity),0) FROM books) AS n_copies,
             (SELECT COALESCE(SUM(price*quantity),0) FROM books) AS stock_value"""
    ).fetchone()
    per_category = db.execute(
        """SELECT c.id, c.name, COUNT(b.id) AS n_titles,
                  COALESCE(SUM(b.quantity),0) AS n_copies
           FROM categories c LEFT JOIN books b ON b.category_id = c.id
           GROUP BY c.id ORDER BY n_titles DESC, c.name"""
    ).fetchall()
    latest = db.execute(
        """SELECT b.*, c.name AS category_name FROM books b
           JOIN categories c ON c.id = b.category_id
           ORDER BY b.id DESC LIMIT 5"""
    ).fetchall()
    max_titles = max([r["n_titles"] for r in per_category], default=0) or 1
    return render_template(
        "dashboard.html",
        totals=totals, per_category=per_category, latest=latest, max_titles=max_titles,
    )


# ---------------------------------------------------------------- Categories
@app.route("/categories")
def categories():
    rows = get_db().execute(
        """SELECT c.*, COUNT(b.id) AS n_titles FROM categories c
           LEFT JOIN books b ON b.category_id = c.id
           GROUP BY c.id ORDER BY c.name"""
    ).fetchall()
    return render_template("categories.html", rows=rows)


def _save_category(cid=None):
    name = request.form.get("name", "").strip()
    desc = request.form.get("description", "").strip()
    if not name:
        flash("Hãy nhập tên danh mục.", "error")
        return False
    db = get_db()
    try:
        if cid is None:
            db.execute("INSERT INTO categories(name, description) VALUES (?,?)", (name, desc))
        else:
            db.execute("UPDATE categories SET name=?, description=? WHERE id=?", (name, desc, cid))
        db.commit()
    except sqlite3.IntegrityError:
        flash(f"Danh mục “{name}” đã tồn tại. Hãy dùng tên khác.", "error")
        return False
    return True


@app.route("/categories/new", methods=["GET", "POST"])
def category_new():
    if request.method == "POST":
        if _save_category():
            flash("Đã thêm danh mục.", "ok")
            return redirect(url_for("categories"))
    return render_template("category_form.html", cat=request.form, editing=False)


@app.route("/categories/<int:cid>/edit", methods=["GET", "POST"])
def category_edit(cid):
    db = get_db()
    cat = db.execute("SELECT * FROM categories WHERE id=?", (cid,)).fetchone()
    if cat is None:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("categories"))
    if request.method == "POST":
        if _save_category(cid):
            flash("Đã lưu danh mục.", "ok")
            return redirect(url_for("categories"))
        cat = request.form
    return render_template("category_form.html", cat=cat, editing=True)


@app.route("/categories/<int:cid>/delete", methods=["POST"])
def category_delete(cid):
    db = get_db()
    n = db.execute("SELECT COUNT(*) FROM books WHERE category_id=?", (cid,)).fetchone()[0]
    if n:
        flash(f"Danh mục còn {n} sách. Hãy xoá hoặc chuyển các sách sang danh mục khác trước.", "error")
        return redirect(url_for("categories"))
    db.execute("DELETE FROM categories WHERE id=?", (cid,))
    db.commit()
    flash("Đã xoá danh mục.", "ok")
    return redirect(url_for("categories"))


# ---------------------------------------------------------------- Books
@app.route("/books")
def books():
    db = get_db()
    cat_id = request.args.get("category", type=int)
    q = request.args.get("q", "").strip()
    sql = """SELECT b.*, c.name AS category_name FROM books b
             JOIN categories c ON c.id = b.category_id WHERE 1=1"""
    args = []
    if cat_id:
        sql += " AND b.category_id = ?"
        args.append(cat_id)
    if q:
        sql += " AND (b.title LIKE ? OR b.author LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY c.name, b.title"
    rows = db.execute(sql, args).fetchall()
    cats = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return render_template("books.html", rows=rows, cats=cats, cat_id=cat_id, q=q)


def _save_book(bid=None):
    f = request.form
    title = f.get("title", "").strip()
    author = f.get("author", "").strip()
    cat_id = f.get("category_id", type=int)
    year = f.get("year", type=int)
    price = f.get("price", type=int)
    quantity = f.get("quantity", type=int)
    if not title:
        flash("Hãy nhập tên sách.", "error")
        return False
    if not cat_id:
        flash("Hãy chọn danh mục.", "error")
        return False
    if price is None or price < 0 or quantity is None or quantity < 0:
        flash("Giá và số lượng phải là số nguyên từ 0 trở lên.", "error")
        return False
    db = get_db()
    if bid is None:
        db.execute(
            "INSERT INTO books(title, author, year, price, quantity, category_id) VALUES (?,?,?,?,?,?)",
            (title, author, year, price, quantity, cat_id),
        )
    else:
        db.execute(
            "UPDATE books SET title=?, author=?, year=?, price=?, quantity=?, category_id=? WHERE id=?",
            (title, author, year, price, quantity, cat_id, bid),
        )
    db.commit()
    return True


@app.route("/books/new", methods=["GET", "POST"])
def book_new():
    db = get_db()
    cats = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    if not cats:
        flash("Cần có ít nhất một danh mục trước khi thêm sách.", "error")
        return redirect(url_for("category_new"))
    if request.method == "POST":
        if _save_book():
            flash("Đã thêm sách.", "ok")
            return redirect(url_for("books", category=request.form.get("category_id")))
        book = request.form
    else:
        book = {"category_id": request.args.get("category", type=int), "price": 0, "quantity": 1}
    return render_template("book_form.html", book=book, cats=cats, editing=False)


@app.route("/books/<int:bid>/edit", methods=["GET", "POST"])
def book_edit(bid):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (bid,)).fetchone()
    if book is None:
        flash("Không tìm thấy sách.", "error")
        return redirect(url_for("books"))
    cats = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    if request.method == "POST":
        if _save_book(bid):
            flash("Đã lưu sách.", "ok")
            return redirect(url_for("books", category=request.form.get("category_id")))
        book = request.form
    return render_template("book_form.html", book=book, cats=cats, editing=True)


@app.route("/books/<int:bid>/delete", methods=["POST"])
def book_delete(bid):
    db = get_db()
    row = db.execute("SELECT category_id FROM books WHERE id=?", (bid,)).fetchone()
    db.execute("DELETE FROM books WHERE id=?", (bid,))
    db.commit()
    flash("Đã xoá sách.", "ok")
    return redirect(url_for("books", category=row["category_id"] if row else None))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
