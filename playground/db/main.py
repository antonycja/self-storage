import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app = Flask(__name__)  # Creating the app

# Configuring the sqlite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"

db.init_app(app)  # Initialize app with extension


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement="auto")
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    surname: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)


# Create the table and add data to the table
# with app.app_context():
#     db.create_all()
#     user = User(name="Antony", surname="Maposa", email="ant@gmail.com",
#                 password="$2b$12$t7J9gwz50A80C27WCZzKce7SiEjUb1/z3KBTxLetRIxirBJg1y8Q.")
#     db.session.add(user)
#     db.session.commit()


# Read all users from the table
# with app.app_context():
#     users = db.session.execute(db.select(User).order_by(User.name))
#     all_users = users.scalars()
    
    
# Read a specific record
# with app.app_context():
#     user = db.session.execute(db.select(User).where(User.name == "Antony")).scalar()
#     print(user.name)


# Update a particular record
# with app.app_context():
#     user_to_update = db.session.execute(db.select(User).where(User.email == "ant@gmail.com")).scalar()
#     user_to_update.email = "antony@gmail.com"
#     db.session.commit()


# Delete a specific record
# book_id = 1
# with app.app_context():
#     user_to_delete = db.session.execute(db.select(User).where(User.id == book_id)).scalar()
#     db.session.delete(user_to_delete)
#     db.session.commit()

# db = sqlite3.connect("test.db")
# cursor = db.cursor()

# cursor.execute("CREATE TABLE users (" +
#                "id INTEGER PRIMARY KEY," +
#                "name varchar(250) NOT NULL," +
#                "surname varchar(250) NOT NULL," +
#                "email varchar(250) NOT NULL UNIQUE," +
#                "password TEXT NOT NULL)"
#                )

# cursor.execute("INSERT INTO users VALUES(" +
#                "1," +
#                "'Antony'," +
#                "'Maposa', " +
#                "'ant@gmail.com'," +
#                "'$2b$12$t7J9gwz50A80C27WCZzKce7SiEjUb1/z3KBTxLetRIxirBJg1y8Q.')"
#                )
# db.commit()


print("Done")
