from email_validator import validate_email, EmailNotValidError
import sqlite3



############################################# CHECKS FUNCTIONS #############################################


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
def email_check(con_email):
    errors = []

    try:
        validate = validate_email(con_email)
        con_email = validate['email']
    except EmailNotValidError:
        errors.append('Incorrect email adress!')

    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT con_email FROM users WHERE con_email = ?", (con_email,))
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