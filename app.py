from flask import Flask, render_template, request, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

from helpers import check_email, conv_tup_to_str, login_required

# Configure application
app = Flask(__name__)

app.secret_key = 'dupa'

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template("add.html")

    else:
        # Open database and creates a cursor
        con = sqlite3.connect("database.db")
        cur = con.cursor()

        # Put new animal into database
        cur.execute("INSERT INTO animals (shelter_id, name, species, description, image, urgency) VALUES (?, ?, ?, ?, ?, ?)", (
            1, # TO BE CHANGED IN THE FUTURE
            request.form.get("name"),
            request.form.get("species"),
            request.form.get("description"),
            request.form.get("image"),
            request.form.get("urgency")
        ))

        # Commit the changes and close database
        con.commit()
        con.close()


        return redirect("/")
    

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")



@app.route("/login", methods = ["GET", "POST"])
def login():

    session.clear()
    error = None

    if request.method == "POST":

        # Opens a database and creates a cursor
        con = sqlite3.connect("database.db")
        cur = con.cursor()

        # Check if user is in database
        username = request.form.get("username")
        cur.execute("SELECT username FROM users WHERE username = ?", (username, ))
        username_check = conv_tup_to_str(cur.fetchone())
        print(username_check)
        if username != username_check:
            error = "Wrong username!"
            return render_template("login.html", error = error)

        # Check password
        password = request.form.get("password")
        cur.execute("SELECT password FROM users WHERE username = ?", (username, ))
        password_check = conv_tup_to_str(cur.fetchone())
        print(password_check)
        if not check_password_hash(password_check, password):
            error = "Wrong password!"
            return render_template("login.html", error = error)
        
        # After passing checks, creates a session and redirects user to index page
        cur.execute("SELECT id FROM users WHERE username = ?", (username, ))
        user_id = cur.fetchone()[0]
        session["user_id"] = user_id
        return redirect("/")


    return render_template("login.html", error = error)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods = ["GET", "POST"])
def register():
    
    error = None

    # Opens database and creates a cursor
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    
    if request.method == "POST":

        # Gets informations from form and checks if them for faults

        # Checks username
        username = request.form.get("username")
        
        if len(username) < 4 or len(username) > 16:
            error = "Username must be between 4 and 16 characters long!"

        if not username.isalnum():
            error = "Username must contain only letters and numbers!"

        cur.execute("SELECT username FROM users WHERE username = ?", (username, ))
        if username == conv_tup_to_str(cur.fetchone()):
            error = "Username already taken!"
  
        # Checks email
        email = request.form.get("email")

        if check_email(email) == False:
            error = "Incorrect email adress!"

        cur.execute("SELECT email FROM users WHERE email = ?", (email, ))
        if email == conv_tup_to_str(cur.fetchone()):
            error = "Email adress already taken!"

        # Checks password
        password = request.form.get("password")
        conpassword = request.form.get("conpassword")

        if password != conpassword:
            error = "Passwords don't match!"

        if len(password) < 8 or len(password) > 20:
            error = "Password must be between 8 and 20 characters long"

        

        # Creates a new user in database and returns to homepage if theres no error
        if error == None:

            # Sets password to hash password
            password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

            cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
            cur.execute("SELECT id FROM users WHERE username = ?", (username, ))
            user_id = cur.fetchone()[0]
            session["user_id"] = user_id
            con.commit()
            con.close()
            
            return render_template("index.html")
        
    con.close()    
    return render_template("register.html", error=error)


@app.route("/registershelter", methods = ["GET", "POST"])
def registershelter():
    if request.method == "GET":
        return render_template("registershelter.html")

    else:
        # Opens database and creates a cursor
        con = sqlite3.connect("database.db")
        cur = con.cursor()

        # Gets informations from form and checks it for faults

        # Check name
        name = request.form.get("name")

        if name.isalnum() == False:
            print("Unallowed characters in name")
            return redirect("/")
        
        if len(name) > 30:
            print("Name must contain less than 30 characters")
            return redirect("/") 
        
        cur.execute("SELECT name FROM shelters")
        names = cur.fetchall()
        names = [item for t in names for item in t]
        if name in names:
            print("Username not available")
            return redirect("/")
        

        # Check email
        email = request.form.get("email")

        if check_email(email) == False:
            print("Invalid email")
            return redirect("/")
        
        cur.execute("SELECT con_email FROM shelters")
        emails = cur.fetchall()
        emails = [item for t in emails for item in t]
        if email in emails:
            print("Email already taken")
            return redirect("/")
        

        # Check password
        password = request.form.get("password")
        conpas = request.form.get("conpas")

        if password != conpas:
            print("Passwords don't match")
            return redirect("/")
        
        if len(password) < 8 or len(password) > 30:
            print("Password must contain between 8 and 30 characters")
            return redirect("/")
        

        # Check city
        city = request.form.get("city")

        if city.isalpha() == False or not city:
            print("Please provide right city name")
            return redirect("/")
        

        # Check adress
        adress = request.form.get("adress")

        if not adress:
            print("Please provide the right adress")
            return redirect("/")
        

        # Check postal code
        postal = request.form.get("postal")

        if not postal:
            print("Please provide the right postal code")
            return redirect("/")
        

        # Check number
        phone = request.form.get("phone")

        if not phone:
            print("Please provide the right phone number")
            return redirect("/")


    print("Alls good")
    return render_template("register.html")