from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from datetime import timedelta
import sqlite3

from helpers import login_required, login_check, registration_check, register_user, login_user

# Configure application
app = Flask(__name__)

# Configure app backed server session
app.config['SESSION_PERMAMENT'] = True
app.config['PERMAMENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SECRET_KEY'] = 'key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


@app.route("/")
def index():
    return render_template("index.html", login = login_check())


@app.route("/login", methods = ["GET", "POST"])
def login():

    # Clears all information that could be stored in session and set errors value to correct
    session.clear()
    errors = None

    # Route for form
    if request.method == "POST":

        # Checks users login and password and if theres no error, creates a session and redirects user to homepage
        username = request.form.get("username")
        errors = login_user(username, request.form.get("password"))
        if errors == None:
            session["user"] = username
            return redirect("/")

    return render_template("login.html", login = login_check(), errors = errors)


@app.route("/logout")
@login_required
def logout():
    
    # Clears session and redirects user to homepage
    session.clear()
    return redirect("/")


@app.route("/register", methods = ["GET", "POST"])
def register():

    # Sets errors to empty list
    errors = []

    # Route for form
    if request.method == "POST":

        # Gets information form form and checks if it's correct, if not creates errors list
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        errors = registration_check(username, email, password, request.form.get("conpassword"))

        # Creates a new user in database and returns to homepage if theres no error in errors list
        if not errors:
            register_user(username, email, password)
            return redirect("/")
        
    return render_template("register.html", login = login_check(), errors=errors)


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", login = login_check())


@app.route("/yourshelter")
def yourshelter():

    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    try:
        cur.execute("SELECT * FROM keepers WHERE username = ?", (session['user'],))
        shelter_id = cur.fetchone()['shelter_id']
        con.close()
        return redirect("/shelter{}".format(shelter_id))
    except TypeError:
        con.close()
        return render_template("yourshelter.html", login = login_check())
    except KeyError:
        con.close()
        return render_template("yourshelter.html", login = login_check())
        


@app.route("/shelter<shelter_id>")
def shelter(shelter_id):
    
    error = None
    
    # Get shelter info
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    try:
        cur.execute("SELECT * FROM shelters WHERE id = ?", (shelter_id,))
        shelter_info = cur.fetchone()
    except TypeError:
        error = 404

    # Check if logged person is shelters keeper
    try:
        cur.execute("SELECT * FROM keepers WHERE shelter_id = ? AND username = ?", (shelter_id, session['user']))
        keeper = cur.fetchone()['username']
    except TypeError:
        keeper = None
    except KeyError:
        keeper = None
    

        
    return render_template("shelter.html", login = login_check(), error=error, keeper = keeper, shelter_info = shelter_info)



# @app.route("/registershelter", methods = ["GET", "POST"])
# def registershelter():
#     if request.method == "GET":
#         return render_template("registershelter.html")

#     else:
#         # Opens database and creates a cursor
#         con = sqlite3.connect("database.db")
#         cur = con.cursor()

#         # Gets informations from form and checks it for faults

#         # Check name
#         name = request.form.get("name")

#         if name.isalnum() == False:
#             print("Unallowed characters in name")
#             return redirect("/")
        
#         if len(name) > 30:
#             print("Name must contain less than 30 characters")
#             return redirect("/") 
        
#         cur.execute("SELECT name FROM shelters")
#         names = cur.fetchall()
#         names = [item for t in names for item in t]
#         if name in names:
#             print("Username not available")
#             return redirect("/")
        

#         # Check email
#         email = request.form.get("email")

#         if check_email(email) == False:
#             print("Invalid email")
#             return redirect("/")
        
#         cur.execute("SELECT con_email FROM shelters")
#         emails = cur.fetchall()
#         emails = [item for t in emails for item in t]
#         if email in emails:
#             print("Email already taken")
#             return redirect("/")
        

#         # Check password
#         password = request.form.get("password")
#         conpas = request.form.get("conpas")

#         if password != conpas:
#             print("Passwords don't match")
#             return redirect("/")
        
#         if len(password) < 8 or len(password) > 30:
#             print("Password must contain between 8 and 30 characters")
#             return redirect("/")
        

#         # Check city
#         city = request.form.get("city")

#         if city.isalpha() == False or not city:
#             print("Please provide right city name")
#             return redirect("/")
        

#         # Check adress
#         adress = request.form.get("adress")

#         if not adress:
#             print("Please provide the right adress")
#             return redirect("/")
        

#         # Check postal code
#         postal = request.form.get("postal")

#         if not postal:
#             print("Please provide the right postal code")
#             return redirect("/")
        

#         # Check number
#         phone = request.form.get("phone")

#         if not phone:
#             print("Please provide the right phone number")
#             return redirect("/")


#     print("Alls good")
#     return render_template("register.html")



# @app.route("/add", methods=["GET", "POST"])
# def add():
#     if request.method == "GET":
#         return render_template("add.html")

#     else:
#         # Open database and creates a cursor
#         con = sqlite3.connect("database.db")
#         cur = con.cursor()

#         # Put new animal into database
#         cur.execute("INSERT INTO animals (shelter_id, name, species, description, image, urgency) VALUES (?, ?, ?, ?, ?, ?)", (
#             1, # TO BE CHANGED IN THE FUTURE
#             request.form.get("name"),
#             request.form.get("species"),
#             request.form.get("description"),
#             request.form.get("image"),
#             request.form.get("urgency")
#         ))

#         # Commit the changes and close database
#         con.commit()
#         con.close()


#         return redirect("/")