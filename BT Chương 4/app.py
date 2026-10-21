
from datetime import datetime

from flask import Flask, render_template, request, redirect

app = Flask(__name__)

BOOKS = [
    {
        "title": "Python cơ bản",
        "author": "Nguyễn Văn A",
        "year": 2022
    },
    {
        "title": "Lập trình Flask",
        "author": "Trần Thị B",
        "year": 2023
    },
    {
        "title": "Cơ sở dữ liệu",
        "author": "Lê Văn C",
        "year": 2021
    },
    {
        "title": "HTML và CSS",
        "author": "Phạm Văn D",
        "year": 2020
    }
]


@app.route("/")
def index():
    q = request.args.get("q", "").strip()

    books = BOOKS

    if q:
        books = [
            book for book in BOOKS
            if q.lower() in book["title"].lower()
        ]

    return render_template(
        "index.html",
        books=books,
        q=q,
        now=datetime.now()
    )


if __name__ == "__main__":
    app.run(debug=True)
