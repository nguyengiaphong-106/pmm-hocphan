from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ---------- Bước 2. Cấu hình kết nối CSDL ----------
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-chi-dung-khi-phat-trien"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///qlsv.db"
db.init_app(app)


# ---------- Bước 3. Khai báo model Student ----------
class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mssv: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gpa: Mapped[float] = mapped_column(default=0.0)

    def __repr__(self):
        return f"<Student {self.mssv} {self.name}>"


# ---------- Bước 4. Tạo bảng ----------
with app.app_context():
    db.create_all()


# ---------- Trang chủ hiển thị giao diện HTML ----------
@app.get("/")
def index():
    students = db.session.scalars(db.select(Student)).all()
    return render_template("students.html", students=students)


# ---------- Bước 5. Thêm dữ liệu bằng view function ----------
@app.get("/them-mau")
def add_sample():
    total = db.session.scalar(db.select(func.count(Student.id)))
    if total > 0:
        return f"Đã có {total} sinh viên, không thêm nữa."
    an = Student(mssv="2371020001", name="Nguyễn Văn An", gpa=8.5)
    before = an.id
    db.session.add(an)
    db.session.add_all([
        Student(mssv="2371020002", name="Trần Thị Bình", gpa=6.8),
        Student(mssv="2371020003", name="Lê Hoàng Cường", gpa=9.1),
        Student(mssv="2371020004", name="Phạm Minh Dũng", gpa=4.5),
        Student(mssv="2371020005", name="Hoàng Thu Hà", gpa=7.4),
    ])
    db.session.commit()
    return (
        f"Đã thêm 5 sinh viên, id của An: "
        f"trước commit = {before}, "
        f"sau commit = {an.id}"
    )


# ---------- Bước 6. Đọc dữ liệu bằng view function ----------
TEXT = {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/thu-truy-van")
def try_queries():
    if db.session.scalar(db.select(func.count(Student.id))) == 0:
        return "Chưa có dữ liệu, hãy mở /them-mau trước."
    lines = []
    lines.append(f"1. get(3): {db.session.get(Student, 3)}")
    lines.append(f"2. get(99): {db.session.get(Student, 99)}")
    everyone = db.session.execute(db.select(Student)).scalars().all()
    lines.append(f"3. Tất cả: {len(everyone)} sinh viên")
    stmt = (
        db.select(Student)
        .where(Student.gpa >= 8)
        .order_by(Student.gpa.desc())
    )
    good = db.session.execute(stmt).scalars().all()
    lines.append(f"4. Điểm >= 8: {good}")
    binh = db.session.scalar(
        db.select(Student).filter_by(mssv="2371020002")
    )
    lines.append(f"5. MSSV 2371020002: {binh}")
    count = db.session.scalar(db.select(func.count(Student.id)))
    avg = db.session.scalar(db.select(func.avg(Student.gpa)))
    lines.append(f"6. Số SV: {count}, điểm TB: {avg:.2f}")
    return "\n".join(lines), TEXT
