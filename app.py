import os
from datetime import datetime

import click
from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy import func, select

from cart import cart_count
from config import Config
from extensions import csrf, db, migrate
import models
from models import PAYMENT_LABELS, PENDING, STATUS_LABELS, Order


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    import admin
    import shop
    app.register_blueprint(shop.bp)
    app.register_blueprint(admin.bp)

    # ---- bộ lọc & biến dùng chung trong template ----
    @app.template_filter("money")
    def money(v):
        return f"{int(v or 0):,}".replace(",", ".") + " đ"

    @app.template_filter("dt")
    def dt(v, fmt="%d/%m/%Y %H:%M"):
        return v.strftime(fmt) if v else ""

    app.jinja_env.globals.update(STATUS_LABELS=STATUS_LABELS,
                                 PAYMENT_LABELS=PAYMENT_LABELS)

    @app.template_global()
    def page_url(n):
        """URL của trang n, giữ nguyên bộ lọc/từ khoá hiện tại."""
        args = {**request.view_args, **request.args.to_dict(), "page": n}
        return url_for(request.endpoint, **args)

    @app.context_processor
    def inject():
        data = {"cart_count": cart_count(), "current_year": datetime.now().year}
        if request.blueprint == "admin":
            data["pending_count"] = db.session.scalar(
                select(func.count(Order.id)).where(Order.status == PENDING))
        return data

    @app.errorhandler(404)
    def not_found(_):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(_):
        flash("Tệp tải lên quá lớn (ảnh bìa tối đa 2 MB).", "danger")
        return redirect(request.referrer or url_for("admin.books"))

    # ---- lệnh CLI ----
    @app.cli.command("init-db")
    def init_db():
        """Tạo bảng nhanh (không dùng migration)."""
        db.create_all()
        click.echo("Đã tạo bảng.")

    @app.cli.command("seed")
    def seed_cmd():
        """Nạp dữ liệu mẫu."""
        from seed import seed
        seed()

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
