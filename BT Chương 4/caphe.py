
import math
from flask import Flask, render_template, request, abort

app = Flask(__name__)

# Bộ lọc định dạng tiền Việt Nam
@app.template_filter("vnd")
def format_vnd(value):
    return f"{int(value):,}".replace(",", ".") + " đ"


# Thông tin cửa hàng
SHOP = {
    "name": "Cà phê Sông Hương",
    "address": "12 Lê Lợi, Huế",
    "phone": "0234 3888 999"
}


# Danh sách thực đơn
MENU = [
    {"id": 1, "name": "Cà phê đen", "price": 20000},
    {"id": 2, "name": "Cà phê sữa", "price": 25000},
    {"id": 3, "name": "Bạc xỉu", "price": 30000},
    {"id": 4, "name": "Trà đào", "price": 35000},
    {"id": 5, "name": "Trà sữa", "price": 40000},
    {"id": 6, "name": "Nước cam", "price": 30000},
    {"id": 7, "name": "Sinh tố bơ", "price": 45000}
]

PER_PAGE = 3


# Trang chủ
@app.get("/")
def index():
    return render_template("index.html", shop=SHOP)


# Trang thực đơn có phân trang
@app.get("/menu")
def show_menu():
    page_param = request.args.get("page", "1")

    try:
        page = int(page_param)
    except (ValueError, TypeError):
        page = 1

    total_pages = math.ceil(len(MENU) / PER_PAGE)

    if page < 1 or page > total_pages:
        abort(404)

    start_idx = (page - 1) * PER_PAGE
    items = MENU[start_idx:start_idx + PER_PAGE]

    return render_template(
        "menu.html",
        shop=SHOP,
        items=items,
        page=page,
        pages=total_pages
    )


# Trang liên hệ
@app.get("/contact")
def contact():
    return render_template("contact.html", shop=SHOP)


# Trang lỗi 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", shop=SHOP), 404


if __name__ == "__main__":
    app.run(debug=True)
