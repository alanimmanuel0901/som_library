from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
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

app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.environ.get("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")

mail = Mail(app)

# ===========================
# TWILIO CONFIGURATION
# ===========================

TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP = "whatsapp:+14155238886"  # Twilio Sandbox

client = Client(TWILIO_SID, TWILIO_TOKEN)

def send_whatsapp(to, message):
    client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP,
        to=f"whatsapp:{to}"
    )

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
    student_phone = db.Column(db.String(20))
    borrow_date = db.Column(db.String(100))
    due_date = db.Column(db.String(100))
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"))
    book = db.relationship("Book")

class Waiting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(200))
    student_phone = db.Column(db.String(20))
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"))
    book = db.relationship("Book")

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
# BOOK DETAIL
# ===========================

@app.route("/book/<int:id>")
def book_detail(id):
    book = Book.query.get_or_404(id)
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=7)

    return render_template(
        "book_detail.html",
        book=book,
        borrow_date=borrow_date.strftime("%d %b %Y %I:%M %p"),
        due_date=due_date.strftime("%d %b %Y %I:%M %p")
    )

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
# AUTHOR ROUTES
# ===========================

@app.route("/admin/authors")
def view_authors():
    if "admin" not in session:
        return redirect("/admin")
    authors = Author.query.all()
    return render_template("authors_list.html", authors=authors)

@app.route("/admin/add-author")
def add_author_page():
    if "admin" not in session:
        return redirect("/admin")
    return render_template("add_author.html")

@app.route("/admin/save-author", methods=["POST"])
def save_author():
    if "admin" not in session:
        return redirect("/admin")

    new_author = Author(
        full_name=request.form["full_name"],
        date_of_birth=request.form["date_of_birth"],
        country=request.form["country"],
        biography=request.form["biography"],
        achievements=request.form["achievements"]
    )

    db.session.add(new_author)
    db.session.commit()
    return redirect("/admin/authors")

@app.route("/admin/edit-author/<int:id>")
def edit_author(id):
    if "admin" not in session:
        return redirect("/admin")
    author = Author.query.get_or_404(id)
    return render_template("edit_author.html", author=author)

@app.route("/admin/update-author/<int:id>", methods=["POST"])
def update_author(id):
    if "admin" not in session:
        return redirect("/admin")

    author = Author.query.get_or_404(id)
    author.full_name = request.form["full_name"]
    author.date_of_birth = request.form["date_of_birth"]
    author.country = request.form["country"]
    author.biography = request.form["biography"]
    author.achievements = request.form["achievements"]

    db.session.commit()
    return redirect("/admin/authors")

# ===========================
# BOOK ROUTES
# ===========================

@app.route("/admin/books")
def view_books():
    if "admin" not in session:
        return redirect("/admin")
    books = Book.query.all()
    return render_template("book_list.html", books=books)

@app.route("/admin/add-book")
def add_book_page():
    if "admin" not in session:
        return redirect("/admin")
    authors = Author.query.all()
    return render_template("add_book.html", authors=authors)

@app.route("/admin/save-book", methods=["POST"])
def save_book():
    if "admin" not in session:
        return redirect("/admin")

    file = request.files.get("cover_image")
    filename = ""

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    new_book = Book(
        title=request.form["title"],
        description=request.form["description"],
        quantity=int(request.form["quantity"]),
        cover_image=filename,
        author_id=int(request.form["author_id"])
    )

    db.session.add(new_book)
    db.session.commit()
    return redirect("/admin/books")

@app.route("/admin/delete-book/<int:id>")
def delete_book(id):
    if "admin" not in session:
        return redirect("/admin")
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return redirect("/admin/books")

# ===========================
# HISTORY
# ===========================

@app.route("/admin/history")
def admin_history():
    if "admin" not in session:
        return redirect("/admin")
    borrows = Borrow.query.order_by(Borrow.id.desc()).all()
    return render_template("history.html", borrows=borrows)

# ===========================
# REMINDERS
# ===========================

@app.route("/admin/reminders")
def admin_reminders():
    if "admin" not in session:
        return redirect("/admin")

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d %b %Y")
    borrows = Borrow.query.all()
    due_tomorrow = [record for record in borrows if tomorrow in record.due_date]

    return render_template("reminders.html", records=due_tomorrow)

# ===========================
# BORROW + EMAIL
# ===========================

@app.route("/borrow/<int:book_id>", methods=["POST"])
def borrow(book_id):
    book = Book.query.get_or_404(book_id)

    if book.quantity > 0:

        student_name = request.form["student_name"]
        student_phone = request.form["student_phone"]

        borrow_date = datetime.now().strftime("%d %b %Y %I:%M %p")
        due_date = (datetime.now() + timedelta(days=7)).strftime("%d %b %Y %I:%M %p")

        # 🔥 Reduce quantity
        book.quantity -= 1

        new_borrow = Borrow(
            student_name=student_name,
            student_phone=student_phone,
            borrow_date=borrow_date,
            due_date=due_date,
            book_id=book.id
        )

        db.session.add(new_borrow)

        # 🔥 SAVE CHANGES
        db.session.commit()

        # Send WhatsApp
        message = f"""
📚 SCHOOL OF MINES DIGITAL LIBRARY

Hello {student_name},

📖 Book: {book.title}
📅 Due Date: {due_date}

Thank you!
"""
        send_whatsapp(student_phone, message)

    return redirect("/")

# ===========================
# WHATSAPP ROUTE
# ===========================

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    response = MessagingResponse()
    response.message("📚 SCHOOL OF MINES DIGITAL LIBRARY\n\nYour message received successfully ✅")
    return str(response)

# ===========================
# CREATE DATABASE
# ===========================

with app.app_context():
    db.create_all()

# ===========================
# RUN
# ===========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))