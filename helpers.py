from email_validator import validate_email, EmailNotValidError
from flask import redirect, session
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


# Function to convert tuple to string, if tuple is empty, it returns None
def conv_tup_to_str(tup):
    if tup != None:
        string = ''.join(tup)
        return string
    else:
        return None


# Login requirement decorator for routs in app
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Keeper requirment decorator for routs in app
def keeper_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if shelter_check() == False:
            return redirect("/yourshelter")
        return f(*args, **kwargs)
    return decorated_function


# Checks if user is logged in 
def login_check():
    if "user" in session:
        return True
    else:
        return False
    

# Check registriation parameters with other functions
def registration_check(username, email, password, conpass):
    errors = []
    for error in username_check(username):
        errors.append(error)
    for error in email_check(email):
        errors.append(error)
    for error in password_check(password, conpass):
        errors.append(error)
    return errors

# Username check
def username_check(username): 
    errors = []

    if len(username) < 4 or len(username) > 20:
        errors.append("Username lenght must be between 4 and 20 characters!")

    if not username.isalnum():
        errors.append("Username must contain only letters and numbers!")

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    if username == conv_tup_to_str(cur.fetchone()):
        errors.append("Username is already taken!")

    return errors

# Email check
def email_check(email):
    errors = []

    try:
        validate = validate_email(email)
        email = validate["email"]
    except EmailNotValidError:
        errors.append("Incorrect email adress!")

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT email FROM users WHERE email = ?", (email,))
    if email == conv_tup_to_str(cur.fetchone()):
        errors.append("Email adress already taken!")

    return errors

#Password check
def password_check(password, conpass):
    errors = []

    if password != conpass:
        errors.append("Passwords don't match!")
    
    if len(password) < 3 or len(password) > 20:
        errors.append("Password must be between 8 and 20 characters long!")

    return errors


# Register new user
def register_user(username, email, password):
    
    # Create hash password form password
    password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
    con.commit()
    con.close()

    session["user"] = username

    return


# Check login parameters
def login_user(username, password):
    # Connects to database, requesting for dictionaries instead of tuples
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    # Checks if username is in database
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    try:
        username = cur.fetchone()["username"]
    except TypeError:
        con.close()
        return "Wrong username or password!"
    
    # Checks if usrname fits password
    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    correct_password = cur.fetchone()["password"]
    if not check_password_hash(correct_password, password):
        con.close()
        return "Wrong username or password!"
    
    con.close()
    return


# Check if logged person is a keeper
def shelter_check():
    # Connects to database, requesting for dictionaries instead of tuples
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    # Try to get shelters id, if not possible return False
    try:
        cur.execute("SELECT * FROM keepers WHERE username = ?", (session['user'],))
        shelter_id = cur.fetchone()['shelter_id']
        con.close()
        return shelter_id
    except TypeError:
        con.close()
        return False
    except KeyError:
        con.close()
        return False
    

# Gets all shelter information in form of dictionary, using shelter id
def get_shelter_info(shelter_id):
    # Connects to database
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Gets information and returns them
    cur.execute("SELECT * FROM shelters WHERE id = ?", (shelter_id,))
    shelter_info = cur.fetchone()
    con.close()

    return shelter_info


# Gets all shelter keepers using shelter id
def get_shelter_keepers(shelter_id):
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    cur.execute("SELECT username FROM keepers WHERE shelter_id = ?", (shelter_id,))
    shelter_keepers = cur.fetchall()
    con.close()

    return shelter_keepers


# Gets information about profile using username
def get_profile_info(username):
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    cur.execute("SELECT username, email, name, surname, phone FROM users WHERE username = ?", (username,))
    profile_info = cur.fetchone()
    con.close()

    return profile_info


# Creates a list of shelter keepers, together with all their info
def get_keepers_info(shelter_id):
    shelter_keepers = get_shelter_keepers(shelter_id)
    for keeper in shelter_keepers:
        keeper.update(get_profile_info(keeper['username']))
    return shelter_keepers