from flask import session
from email_validator import validate_email, EmailNotValidError
import sqlite3
import datetime

# Let's for creating dictionares of database content
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


####################################################################################################  CHECK FUNCTIONS  ####################################################################################################
# This file contains all the functions that helps the main app to work. It includes functions which purpose is to check provided information


##################################################    USER STATUS CHECKS    ##################################################

# Checks if user is logged in
def login_check():
    if 'user' in session:
        return True
    else:
        return False
    
# Checks if user is volunteer
def volunteer_check(shelter_id):
    # Checks if user is logged in
    if not login_check():
        return False
    # Connects to database and checks if user is volunteer in the shelter, then returns either true or false
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT username FROM volunteers WHERE username = ? AND shelter_id = ?", (session['user'], shelter_id))
    if cur.fetchone():
        con.close()
        return True
    else:
        con.close()
        return False
    
# Checks if user is a keeper
def keeper_check(shelter_id):
    # Checks if user is logged in
    if not login_check():
        return False
    # Connects to database and checks if user is keeper in the shelter, then returns either true or false
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
    # Checks if user is logged in
    if not login_check():
        return False
    # Connects to database and checks if user is owner in the shelter, then returns either true or false
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
    
# Checks if user status allows for taking animal for a walk
def walk_check(animal_id):
    # Connects to database and based on animal gets shelters id
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT shelter_id FROM animals WHERE id = ?", (animal_id,))
    shelter_id = cur.fetchone()
    con.close()
    # If theres no such shelter returns false
    if not shelter_id:
        return False
    # Otherwise checks if user has the right status to schedule a walk with the animal
    shelter_id = shelter_id['shelter_id']
    if not volunteer_check(shelter_id) and not keeper_check(shelter_id):
        return False
    return True


##################################################    FORM CHECKS    ##################################################
    

# Checks if username is ok
def username_check(username):
    errors = []
    # Checks for length
    if len(username) < 4 or len(username) > 20:
        errors.append('Username lenght must be between 4 and 20 characters!')
    # Checks for special characters
    if not username.isalnum():
        errors.append('Username must contain only letters and numbers!')
    # Checks if username is already taken
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        errors.append('Username is already taken!')
    # Returns either errors or empty list
    return errors

# Checks if email is ok
def email_check(table, con_email):
    errors = []
    # Validates email structure
    try:
        validate = validate_email(con_email)
        con_email = validate['email']
    except EmailNotValidError:
        errors.append('Incorrect email adress!')
    # Checks if email is already taken
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT con_email FROM "+table+" WHERE con_email = ?", (con_email,))
    if cur.fetchone():
        errors.append('Email adress is already taken!')
    # Returns either erorrs or empty list
    return errors

# AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA                   PO TESTOWANIU DOROBIĆ WIĘCEJ CHECKÓW ASDASDASDASDSAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
# Checks if password is ok
def password_check(password, conpassword):
    errors = []
    # Checks password for match with repeated one
    if password != conpassword:
        errors.append('Passwords do not match!')
    # Checks for length
    if len(password) < 3 or len(password) > 20:
        errors.append('Password must be between 8 and 20 characters long!')
    # Returns either errors or empty list
    return errors

# Checks shelte create form
def shelter_form_check(shelter):
    errors = []
    # Checks name for special characters and length
    if shelter['name'].replace(' ','').isalnum() == False:
        errors.append('Shelter name can only contain letters and numbers!')
    if len(shelter['name']) < 4 or len(shelter['name']) > 20:
        errors.append('Shlelter name must be between 4 and 20 character long!')
    # Checks city name for special characters
    if not shelter['loc_city'] or shelter['loc_city'].isalnum() == False or len(shelter['loc_city']) > 100:
        errors.append('Please provide right city name!')
    # Checks adress for length
    if not shelter['loc_adress'] or len(shelter['loc_adress']) > 100:
        errors.append('Please provide right adress!')
    # Checks postal for length
    if not shelter['loc_postal'] or len(shelter['loc_postal']) > 100:
        errors.append('Please provide right postal code!')
    # Checks phone for length
    if not shelter['con_phone'] or len(shelter['con_phone']) > 100:
        errors.append('Please provide right phone number!')
    # Checks description for length
    if len(shelter['description']) > 1000:
        errors.append('Description must be shorter than 1000 characters!')
    # Retutns either errors or emoty list
    return errors

# Checks if date is correct
def date_check(date):
    try:
        datetime.date.fromisoformat(date)
        return True
    except ValueError:
        return False