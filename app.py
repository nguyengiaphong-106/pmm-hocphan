from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ---------------------------------------------------------
# BƯỚC 2: CẤU HÌNH KẾT NỐI CSDL SQLITE
# ---------------------------------------------------------
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-chia-dung-khi-phat-trien"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///qlev.db"

db.init_app(app)

# Header cấu hình trả về text thuần cho route thử nghiệm
TEXT = {"Content-Type": "text/plain; charset=utf-8"}

# ---------------------------------------------------------
# BƯỚC 3: KHAI BÁO MODEL STUDENT (Bảng 'student')
# ---------------------------------------------------------
class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mssv: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gpa: Mapped[float] = mapped_column(default=0.0)

    def __repr__(self):
        return f"<Student {self.mssv} {self.name}>"

# ---------------------------------------------------------
# BƯỚC 4: TẠO BẢNG CSDL TỰ ĐỘNG
# ---------------------------------------------------------
with app.app_context():
    db.create_all()

# ---------------------------------------------------------
# BƯỚC 5: ROUTE NẠP DỮ LIỆU MẪU
# ---------------------------------------------------------
@app.get("/them-mau")
def add_sample():
    total = db.session.scalar(db.select(func.count(Student.id)))
    if total > 0:
        return f"Đã có {total} sinh viên, không thêm nữa."

    an = Student(mssv="23T1020001", name="Nguyễn Văn An", gpa=3.5)
    before = an.id

    db.session.add(an)
    db.session.add_all([
        Student(mssv="23T1020002", name="Trần Thị Bình", gpa=3.8),
        Student(mssv="23T1020003", name="Lê Hoàng Cường", gpa=3.3),
        Student(mssv="23T1020004", name="Phạm Minh Dũng", gpa=3.57),
        Student(mssv="23T1020005", name="Hoàng Thu Hà", gpa=3.4),
    ])

    db.session.commit()

    return (f"Đã thêm 5 sinh viên. id của An: "
            f"<br>trước commit = {before}, "
            f"<br>sau commit = {an.id}")

# ---------------------------------------------------------
# BƯỚC 6: ĐỌC DỮ LIỆU BẰNG VIEW FUNCTION (KĨ THUẬT TRUY VẤN)
# ---------------------------------------------------------
@app.get("/thu-truy-van")
def try_queries():
    if db.session.scalar(db.select(func.count(Student.id))) == 0:
        return "Chưa có dữ liệu, hãy mở /them-mau trước."

    lines = []

    # 1 & 2. Lấy đối tượng theo ID (Primary Key)
    lines.append(f"1. get(3): {db.session.get(Student, 3)}")
    lines.append(f"2. get(99): {db.session.get(Student, 99)}")

    # 3. Lấy tất cả bản ghi sinh viên
    everyone = db.session.execute(db.select(Student)).scalars().all()
    lines.append(f"3. Tất cả: {len(everyone)} sinh viên")

    # 4. Lọc theo điều kiện gpa >= 3.5 và sắp xếp giảm dần
    stmt = (
        db.select(Student)
        .where(Student.gpa >= 3.5)
        .order_by(Student.gpa.desc())
    )
    gpas = db.session.execute(stmt).scalars().all()
    lines.append(f"4. Điểm >= 3.5: {gpas}")

    # 5. Tìm kiếm chính xác theo thuộc tính
    binh = db.session.scalar(db.select(Student).filter_by(mssv="23T1020002"))
    lines.append(f"5. MSSV 23T1020002: {binh}")

    # 6. Thống kê số lượng và tính GPA trung bình
    count = db.session.scalar(db.select(func.count(Student.id)))
    avg = db.session.scalar(db.select(func.avg(Student.gpa)))
    lines.append(f"6. Số SV: {count}, điểm TB: {avg:.2f}")

    return "\n".join(lines), TEXT

# ---------------------------------------------------------
# TRANG CHỦ: HIỂN THỊ DANH SÁCH RA GIAO DIỆN WEB HTML
# ---------------------------------------------------------
@app.get("/")
def index():
    students = db.session.scalars(select(Student)).all()
    return render_template("students.html", students=students)

if __name__ == '__main__':
    app.run(debug=True) 