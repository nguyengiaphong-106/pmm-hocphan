from flask import Flask, url_for, request, redirect, abort, make_response
from markupsafe import escape
import csv
import io

app = Flask(__name__)
app.json.ensure_ascii = False


STUDENTS = {
    "23T1020001": {
        "ho_ten": "Nguyễn Văn An",
        "lop": "K47A",
        "scores": {
            "PMMNM": 8.5,
            "CSDL": 7.0,
            "MMT": 9.0
        }
    },
    "23T1020002": {
        "ho_ten": "Trần Thị Bình",
        "lop": "K47A",
        "scores": {
            "PMMNM": 6.0,
            "CSDL": 5.5,
            "MMT": 7.0
        }
    },
    "23T1020003": {
        "ho_ten": "Lê Hoàng Cường",
        "lop": "K47B",
        "scores": {
            "PMMNM": 9.5,
            "CSDL": 9.0
        }
    },
    "23T1020004": {
        "ho_ten": "Phạm Minh Dũng",
        "lop": "K47B",
        "scores": {
            "PMMNM": 4.0,
            "CSDL": 3.5,
            "MMT": 5.0
        }
    },
    "23T1020005": {
        "ho_ten": "Hoàng Thu Hà",
        "lop": "K47A",
        "scores": {}
    },
    "23T1020006": {
        "ho_ten": "Võ Quốc Khánh",
        "lop": "K47C",
        "scores": {
            "PMMNM": 7.5,
            "MMT": 8.0
        }
    }
}


def average(scores):
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def rank(avg):
    if avg is None:
        return "Chưa có điểm"
    if avg >= 8.5:
        return "Giỏi"
    if avg >= 7:
        return "Khá"
    if avg >= 5:
        return "Trung bình"
    return "Yếu"


def student_summary(mssv):
    sv = STUDENTS[mssv]
    avg = average(sv["scores"])

    return {
        "mssv": mssv,
        "ho_ten": sv["ho_ten"],
        "lop": sv["lop"],
        "scores": sv["scores"],
        "average": avg,
        "rank": rank(avg)
    }


def layout(title, body):
    title = escape(title)

    return f"""
    <!doctype html>
    <html lang="vi">
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
    </head>
    <body>
        <nav>
            <a href="{url_for('index')}">Trang chủ</a> |
            <a href="{url_for('students')}">Sinh viên</a> |
            <a href="{url_for('search')}">Tìm kiếm</a>
        </nav>

        <h1>{title}</h1>

        {body}
    </body>
    </html>
    """


# =========================
# CÂU 1
# =========================

@app.route("/")
def index():
    total = len(STUDENTS)
    classes = len(set(sv["lop"] for sv in STUDENTS.values()))

    body = f"""
    <p>Tổng số sinh viên: {total}</p>
    <p>Số lớp khác nhau: {classes}</p>

    <p>
        <a href="{url_for('students')}">
            Danh sách sinh viên
        </a>
    </p>

    <p>
        <a href="{url_for('api_students')}">
            API sinh viên
        </a>
    </p>
    """

    return layout("Sổ điểm lớp học", body)


# =========================
# CÂU 2
# =========================

@app.route("/students")
def students():
    lop = request.args.get("lop")

    data = STUDENTS

    if lop:
        data = {
            mssv: sv
            for mssv, sv in STUDENTS.items()
            if sv["lop"] == lop
        }

    classes = sorted(set(sv["lop"] for sv in STUDENTS.values()))

    body = """
    <form method="get">
        <label>Lọc theo lớp:</label>
        <select name="lop">
            <option value="">Tất cả</option>
    """

    for cls in classes:
        selected = "selected" if cls == lop else ""
        body += f"""
            <option value="{escape(cls)}" {selected}>
                {escape(cls)}
            </option>
        """

    body += """
        </select>
        <button type="submit">Lọc</button>
    </form>

    <table border="1">
        <tr>
            <th>MSSV</th>
            <th>Họ tên</th>
            <th>Lớp</th>
            <th>Điểm TB</th>
            <th>Xếp loại</th>
        </tr>
    """

    for mssv, sv in data.items():
        avg = average(sv["scores"])

        avg_text = "Chưa có" if avg is None else avg

        body += f"""
        <tr>
            <td>
                <a href="{url_for('student_detail', mssv=mssv)}">
                    {escape(mssv)}
                </a>
            </td>
            <td>{escape(sv["ho_ten"])}</td>
            <td>{escape(sv["lop"])}</td>
            <td>{avg_text}</td>
            <td>{escape(rank(avg))}</td>
        </tr>
        """

    body += "</table>"

    return layout("Danh sách sinh viên", body)


# =========================
# CÂU 3
# =========================

@app.route("/students/<mssv>")
def student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404)

    sv = student_summary(mssv)

    body = f"""
    <p>MSSV: {escape(sv["mssv"])}</p>
    <p>Họ tên: {escape(sv["ho_ten"])}</p>
    <p>Lớp: {escape(sv["lop"])}</p>

    <h2>Điểm</h2>
    <ul>
    """

    for course, score in sv["scores"].items():
        body += f"""
        <li>{escape(course)}: {score}</li>
        """

    body += f"""
    </ul>

    <p>Điểm trung bình: {
        "Chưa có" if sv["average"] is None else sv["average"]
    }</p>

    <p>Xếp loại: {escape(sv["rank"])}</p>
    """

    return layout("Chi tiết sinh viên", body)


# =========================
# CÂU 4
# =========================

@app.route("/sv/<mssv>")
def old_student_url(mssv):
    return redirect(
        url_for("student_detail", mssv=mssv),
        code=301
    )


# =========================
# CÂU 5
# =========================

@app.route("/students/<mssv>/export")
def export_student(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    sv = STUDENTS[mssv]

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["MSSV", "Họ tên", "Lớp", "Môn học", "Điểm"])

    for course, score in sv["scores"].items():
        writer.writerow([
            mssv,
            sv["ho_ten"],
            sv["lop"],
            course,
            score
        ])

    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=diem_{mssv}.csv"
    )

    return response

# =========================
# CÂU 6
# =========================

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()

    results = []

    if q:
        q_lower = q.lower()

        for mssv, sv in STUDENTS.items():
            if (
                q_lower in mssv.lower()
                or q_lower in sv["ho_ten"].lower()
                or q_lower in sv["lop"].lower()
            ):
                results.append((mssv, sv))

    body = f"""
    <form method="get">
        <input
            type="text"
            name="q"
            value="{escape(q)}"
            placeholder="Nhập MSSV, họ tên hoặc lớp"
        >
        <button type="submit">Tìm</button>
    </form>
    """

    if q:
        body += f"<p>Kết quả tìm kiếm cho: {escape(q)}</p>"

        if not results:
            body += "<p>Không tìm thấy sinh viên.</p>"
        else:
            body += "<ul>"

            for mssv, sv in results:
                body += f"""
                <li>
                    <a href="{url_for('student_detail', mssv=mssv)}">
                        {escape(sv["ho_ten"])}
                    </a>
                    - {escape(mssv)}
                    - {escape(sv["lop"])}
                </li>
                """

            body += "</ul>"

    return layout("Tìm kiếm sinh viên", body)


# =========================
# CÂU 7
# =========================

@app.route("/api/students")
def api_students():
    lop = request.args.get("lop")
    min_avg_text = request.args.get("min_avg")

    if min_avg_text is not None:
        try:
            min_avg = float(min_avg_text)
        except ValueError:
            return {
                "error": "bad_request",
                "detail": "min_avg phải là số"
            }, 400
    else:
        min_avg = None

    result = []

    for mssv, sv in STUDENTS.items():

        if lop and sv["lop"] != lop:
            continue

        avg = average(sv["scores"])

        if min_avg is not None:
            if avg is None or avg < min_avg:
                continue

        result.append(student_summary(mssv))

    return result
@app.route("/api/students/<mssv>")
def api_student_detail(mssv):
    if mssv not in STUDENTS:
        return {
            "error": "not_found",
            "detail": f"Không có sinh viên với MSSV = {mssv}."
        }, 404

    return student_summary(mssv)

# =========================
# CÂU 8
# =========================

@app.route(
    "/api/students/<mssv>/scores/<course>",
    methods=["GET", "PUT", "DELETE"]
)
def score_api(mssv, course):

    if mssv not in STUDENTS:
        abort(404)

    course = course.upper()
    scores = STUDENTS[mssv]["scores"]

    if request.method == "GET":

        if course not in scores:
            abort(404)

        return {
            "mssv": mssv,
            "course": course,
            "score": scores[course]
        }

    if request.method == "PUT":

        data = request.get_json(silent=True)

        if not data or "score" not in data:
            return {
                "error": "bad_request",
                "detail": "Thiếu score"
            }, 400

        try:
            score = float(data["score"])
        except (ValueError, TypeError):
            return {
                "error": "bad_request",
                "detail": "score phải là số"
            }, 400

        if score < 0 or score > 10:
            return {
                "error": "bad_request",
                "detail": "score phải nằm trong khoảng 0 đến 10"
            }, 400

        is_new = course not in scores

        scores[course] = score

        avg = average(scores)

        result = {
            "mssv": mssv,
            "course": course,
            "score": score,
            "average": avg
        }

        if is_new:
            response = make_response(result, 201)
            response.headers["Location"] = url_for(
                "score_api",
                mssv=mssv,
                course=course
            )
            return response

        return result, 200

    if request.method == "DELETE":

        if course not in scores:
            abort(404)

        del scores[course]

        return "", 204


# =========================
# CÂU 9
# =========================

@app.errorhandler(404)
def not_found(error):

    if request.path.startswith("/api/"):
        return {
            "error": "not_found",
            "detail": "Không tìm thấy tài nguyên"
        }, 404

    return layout(
        "404 - Không tìm thấy",
        "<p>Không tìm thấy trang yêu cầu.</p>"
    ), 404


@app.errorhandler(400)
def bad_request(error):

    if request.path.startswith("/api/"):
        return {
            "error": "bad_request",
            "detail": "Yêu cầu không hợp lệ"
        }, 400

    return layout(
        "400 - Yêu cầu không hợp lệ",
        "<p>Yêu cầu không hợp lệ.</p>"
    ), 400


@app.errorhandler(405)
def method_not_allowed(error):

    if request.path.startswith("/api/"):
        return {
            "error": "method_not_allowed",
            "detail": "Phương thức HTTP không được phép"
        }, 405

    return layout(
        "405 - Method Not Allowed",
        "<p>Phương thức HTTP không được phép.</p>"
    ), 405