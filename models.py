from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 👤 AUTHOR MODEL
class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200))
    date_of_birth = db.Column(db.String(50))
    country = db.Column(db.String(100))
    biography = db.Column(db.Text)
    achievements = db.Column(db.Text)

# 📚 BOOK MODEL
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer)

    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    # 📸 Image field
    cover_image = db.Column(db.String(200))

    # Relationship
    author = db.relationship('Author')