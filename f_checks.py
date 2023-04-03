from flask import session
from email_validator import validate_email, EmailNotValidError
import sqlite3

# Let's for creating dictionares of database content
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}



############################################# CHECKS FUNCTIONS #############################################


# Checks if user is logged in
def login_check():
    if 'user' in session:
        return True
    else:
        return False
    
# Checks if user is a keeper
def keeper_check(shelter_id):
    if not login_check():
        return False
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username FROM keepers WHERE username = ? AND shelter_id = ?", (session['user'], shelter_id))
    if cur.fetchone():
        con.close()
        return True
    else:
        con.close()
        return False

# Checks if user is an owner
def owner_check(shelter_id):
    if not login_check():
        return False
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM keepers WHERE username = ? AND shelter_id = ? AND owner = 1", (session['user'], shelter_id))
    if cur.fetchone():
        con.close()
        return True
    else:
        con.close()
        return False

# Checks if username is ok
def username_check(username):
    errors = []

    if len(username) < 4 or len(username) > 20:
        errors.append('Username lenght must be between 4 and 20 characters!')

    if not username.isalnum():
        errors.append('Username must contain only letters and numbers!')

    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        errors.append('Username is already taken!')

    return errors

# Checks if email is ok
def email_check(table, con_email):
    errors = []

    try:
        validate = validate_email(con_email)
        con_email = validate['email']
    except EmailNotValidError:
        errors.append('Incorrect email adress!')

    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT con_email FROM "+table+" WHERE con_email = ?", (con_email,))
    if cur.fetchone():
        errors.append('Email adress is already taken!')

    return errors

# Checks if password is ok
def password_check(password, conpassword):
    errors = []

    if password != conpassword:
        errors.append('Passwords do not match!')
    
    if len(password) < 3 or len(password) > 20:
        errors.append('Password must be between 8 and 20 characters long!')

    return errors

# Checks shelte create form
def shelter_form_check(shelter):
    errors = []

    if shelter['name'].replace(' ','').isalnum() == False:
        errors.append('Shelter name can only contain letters and numbers!')
    if len(shelter['name']) < 4 or len(shelter['name']) > 20:
        errors.append('Shlelter name must be between 4 and 20 character long!')
    
    if shelter['loc_city'].isalnum() == False or len(shelter['loc_city']) > 100:
        errors.append('Please provide right city name!')

    if not shelter['loc_adress'] or len(shelter['loc_adress']) > 100:
        errors.append('Please provide right adress!')

    if not shelter['loc_postal'] or len(shelter['loc_postal']) > 100:
        errors.append('Please provide right postal code!')

    if not shelter['con_phone'] or len(shelter['con_phone']) > 100:
        errors.append('Please provide right phone number!')

    if len(shelter['description']) > 1000:
        errors.append('Description must be shorter than 1000 characters!')

    return errors