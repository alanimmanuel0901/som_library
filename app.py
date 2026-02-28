from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ===========================
# DATABASE CONFIG
# ===========================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ===========================
# MAIL CONFIGURATION
# ===========================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")

mail = Mail(app)

# ===========================
# UPLOAD FOLDER
# ===========================

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ===========================
# MODELS
# ===========================

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200))
    date_of_birth = db.Column(db.String(100))
    country = db.Column(db.String(100))
    biography = db.Column(db.Text)
    achievements = db.Column(db.Text)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer)
    cover_image = db.Column(db.String(200))
    author_id = db.Column(db.Integer, db.ForeignKey("author.id"))
    author = db.relationship("Author")

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(200))
    student_email = db.Column(db.String(200))
    borrow_date = db.Column(db.String(100))
    due_date = db.Column(db.String(100))
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"))
    book = db.relationship("Book")

# ===========================
# ADMIN LOGIN
# ===========================

ADMIN_USERNAME = "SOM0901"
ADMIN_PASSWORD = "0901"

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            return render_template("admin_login.html", error="Invalid Credentials")
    return render_template("admin_login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")
    authors = Author.query.all()
    books = Book.query.all()
    return render_template("admin.html", authors=authors, books=books)

# ===========================
# HOME
# ===========================

@app.route("/")
def home():
    query = request.args.get("search")
    if query:
        books = Book.query.filter(Book.title.ilike(f"%{query}%")).all()
    else:
        books = Book.query.all()
    return render_template("home.html", books=books)

# ===========================
# BORROW + EMAIL (FIXED)
# ===========================

@app.route("/borrow/<int:id>", methods=["POST"])
def borrow_book(id):

    book = Book.query.get_or_404(id)

    if book.quantity <= 0:
        return redirect(f"/book/{id}")

    student_name = request.form["student_name"]
    student_email = request.form["student_email"]

    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=7)

    formatted_borrow = borrow_date.strftime("%d %b %Y %I:%M %p")
    formatted_due = due_date.strftime("%d %b %Y %I:%M %p")

    new_borrow = Borrow(
        student_name=student_name,
        student_email=student_email,
        borrow_date=formatted_borrow,
        due_date=formatted_due,
        book_id=id
    )

    book.quantity -= 1
    db.session.add(new_borrow)
    db.session.commit()

    try:
        msg = Message(
            "📚 SCHOOL OF MINES DIGITAL LIBRARY - Borrow Confirmation",
            sender=app.config['MAIL_USERNAME'],
            recipients=[student_email]
        )

        msg.html = f"""
<h2>📚 SCHOOL OF MINES DIGITAL LIBRARY</h2>
<p>Hello <b>{student_name}</b>,</p>
<ul>
    <li><b>Book:</b> {book.title}</li>
    <li><b>Borrow Date:</b> {formatted_borrow}</li>
    <li><b>Due Date:</b> {formatted_due}</li>
</ul>
<p>Please return before due date.</p>
<p>
Regards,<br>
<b>SCHOOL OF MINES DIGITAL LIBRARY</b>
</p>
"""

        mail.send(msg)

    except Exception as e:
        print("Email Error:", e)

    return redirect("/")

# ===========================
# CREATE DATABASE
# ===========================

with app.app_context():
    db.create_all()

# ===========================
# RUN
# ===========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)