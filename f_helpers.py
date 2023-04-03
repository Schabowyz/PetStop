from flask import redirect, session, request, flash
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from f_checks import username_check, email_check, password_check

UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png']
ANIMAL_IMAGES_PATH = 'static/animal_images/'
SHELTER_IMAGES_PATH = 'static/shelter_images/'



############################################# DECORATORS #############################################


# Login requirement decorator for routs in app
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') is None:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# Logout requirement decorator for routs in app
def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') is not None:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function



############################################# HELPER FUNCTIONS #############################################


# Let's for creating dictionares of database content
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


# Checks status of application user; logged/keeper/owner
def get_user_status(shelter_id):
    user_status = {}
    # Checks if user is logged in
    if 'user' in session:
        user_status['login'] = True
    else:
        user_status['login'] = False
        user_status['keeper'] = False
        user_status['owner'] = False
        return user_status
    # Checks if shelter page is opened
    if shelter_id == None:
        user_status['keeper'] = False
        user_status['owner'] = False
        return user_status        
    # If shelter page is opened checks if user is in keepers for the shelter and if user in owner of the shelter
    else:
        con = sqlite3.connect('database.db')
        con.row_factory = dict_factory
        cur = con.cursor()
        cur.execute("SELECT username, owner FROM keepers WHERE username = ? AND shelter_id = ?", (session['user'], shelter_id))
        check = cur.fetchone()
        if not check:
            user_status['keeper'] = False
            user_status['owner'] = False
            con.close()
            return user_status
        else:
            user_status['keeper'] = True
            user_status['owner'] = check['owner']
            con.close()
            return user_status
        
# Logs user in
def login_user():
    # Gets username and pw from forms and checks them with database records
    username = request.form.get('username')
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username, password FROM users WHERE username = ?", (username,))
    check = cur.fetchone()
    # If theres no such user or pw is wrong returns false, else returns true
    if not check:
        flash('Wrong username or password!')
        return False
    else:
        if not check_password_hash(check['password'], request.form.get('password')):
            flash('Wrong username or password!')
            return False
        else:
            session['user'] = username
            flash('You were successfully logged in!')
            return True
        
# Regiseters a new user
def register_user():
    # Gets info from forms and passes them to separate check functions
    username = request.form.get('username')
    con_email = request.form.get('con_email')
    password = request.form.get('password')
    conpassword = request.form.get('conpassword')

    errors = []
    errors += username_check(username)
    errors += email_check(con_email)
    errors += password_check(password, conpassword)

    # If there's no error commits changes to database and returns true
    if errors:
        for error in errors:
            flash(error)
        return False
    else:
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute("INSERT INTO users (username, con_email, password) VALUES (?, ?, ?)", (username, con_email, generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)))
        con.commit()
        con.close()

        session['user'] = username
        flash('You were successfully registered!')
        return True

# Checks if logged user is keeper in a shelter and if so returns it's id
def check_user_shelter():
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute('SELECT shelter_id FROM keepers WHERE username = ?', (session['user'],))
    shelter_id = cur.fetchone()
    con.close()
    if not shelter_id:
        return False
    else:
        return shelter_id