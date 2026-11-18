from datetime import datetime

from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from PIL import Image
from sqlalchemy import select
from wtforms import IntegerField, RadioField, SelectField, StringField, TextAreaField
from wtforms.validators import (DataRequired, Email, InputRequired, Length,
                                NumberRange, Optional, Regexp, ValidationError)

from extensions import db
from models import PAYMENT_LABELS, Book, Category


def strip(value):
    return value.strip() if isinstance(value, str) else value


class IntField(IntegerField):
    """IntegerField với thông báo lỗi tiếng Việt."""

    def process_formdata(self, valuelist):
        if not valuelist or valuelist[0] == "":
            return
        try:
            self.data = int(valuelist[0])
        except ValueError:
            self.data = None
            raise ValueError("Vui lòng nhập một số nguyên.")


class CheckoutForm(FlaskForm):
    customer_name = StringField("Họ tên", filters=[strip], validators=[
        DataRequired("Vui lòng nhập họ tên."), Length(max=100)])
    phone = StringField("Số điện thoại", filters=[strip], validators=[
        DataRequired("Vui lòng nhập số điện thoại."),
        Regexp(r"^0\d{9}$", message="Số điện thoại gồm 10 chữ số, bắt đầu bằng 0.")])
    address = TextAreaField("Địa chỉ giao hàng", filters=[strip], validators=[
        DataRequired("Vui lòng nhập địa chỉ giao hàng."), Length(max=255)])
    email = StringField("Email", filters=[strip], validators=[
        Optional(), Email("Email không đúng định dạng."), Length(max=120)])
    note = TextAreaField("Ghi chú", filters=[strip], validators=[
        Optional(), Length(max=500)])
    payment = RadioField("Thanh toán", choices=list(PAYMENT_LABELS.items()),
                         default="cod", validators=[DataRequired("Chọn hình thức thanh toán.")])


class BookForm(FlaskForm):
    title = StringField("Tên sách", filters=[strip], validators=[
        DataRequired("Vui lòng nhập tên sách."), Length(max=200)])
    author = StringField("Tác giả", filters=[strip], validators=[
        DataRequired("Vui lòng nhập tác giả."), Length(max=120)])
    publisher = StringField("Nhà xuất bản", filters=[strip], validators=[
        Optional(), Length(max=120)])
    year = IntField("Năm xuất bản", validators=[Optional()])
    category_id = SelectField("Danh mục", coerce=int, validators=[
        InputRequired("Chọn danh mục.")])
    price = IntField("Giá (đồng)", validators=[
        InputRequired("Vui lòng nhập giá."),
        NumberRange(min=1000, message="Giá tối thiểu 1.000 đồng.")])
    stock = IntField("Tồn kho", validators=[
        InputRequired("Vui lòng nhập tồn kho."),
        NumberRange(min=0, message="Tồn kho không âm.")])
    description = TextAreaField("Mô tả", filters=[strip], validators=[Optional()])
    cover_file = FileField("Ảnh bìa", validators=[
        FileAllowed(["jpg", "jpeg", "png", "webp"], "Chỉ nhận ảnh JPG, PNG, WEBP.")])

    def __init__(self, *args, book_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.book_id = book_id
        cats = db.session.scalars(select(Category).order_by(Category.name)).all()
        self.category_id.choices = [(c.id, c.name) for c in cats]

    def validate_title(self, field):
        wanted = field.data.casefold()
        for bid, title in db.session.execute(select(Book.id, Book.title)):
            if bid != self.book_id and title.casefold() == wanted:
                raise ValidationError("Tên sách đã tồn tại.")

    def validate_year(self, field):
        if field.data is None:
            return
        now = datetime.now().year
        if not 1900 <= field.data <= now:
            raise ValidationError(f"Năm xuất bản từ 1900 đến {now}.")

    def validate_cover_file(self, field):
        f = field.data
        if not f or not getattr(f, "filename", ""):
            return
        f.stream.seek(0, 2)
        size = f.stream.tell()
        f.stream.seek(0)
        if size > current_app.config["MAX_COVER_BYTES"]:
            raise ValidationError("Ảnh bìa tối đa 2 MB.")
        try:                                   # chắc chắn đây là ảnh thật
            Image.open(f.stream).verify()
        except Exception:
            raise ValidationError("Tệp không phải ảnh hợp lệ.")
        finally:
            f.stream.seek(0)


class CategoryForm(FlaskForm):
    name = StringField("Tên", filters=[strip], validators=[
        DataRequired("Vui lòng nhập tên danh mục."), Length(max=100)])
    description = TextAreaField("Mô tả", filters=[strip], validators=[Optional()])

    def __init__(self, *args, category_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_id = category_id

    def validate_name(self, field):
        wanted = field.data.casefold()
        for cid, name in db.session.execute(select(Category.id, Category.name)):
            if cid != self.category_id and name.casefold() == wanted:
                raise ValidationError("Danh mục đã tồn tại.")
