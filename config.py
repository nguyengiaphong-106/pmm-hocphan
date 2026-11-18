import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "doi-khoa-nay-khi-trien-khai")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///bookstore.db")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024      # chặn request quá lớn (413)
    MAX_COVER_BYTES = 2 * 1024 * 1024         # ảnh bìa tối đa 2 MB
