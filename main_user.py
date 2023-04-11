from flask import session, request, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from main_checks import username_check, email_check, password_check

from main_helpers import dict_factory


####################################################################################################  FUNCTIONS ASSIGNED TO USER PROFILE  ####################################################################################################
# This file contains all the functions beeing a core funcionality of the app, that are assigned to users profile; creation, loggin, editing info, etc.


##################################################    USER    ##################################################

# Logs user in
def login_user():
    # Gets username and pw from forms and checks them with database records
    username = request.form.get('username')
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username, password FROM users WHERE username = ?", (username,))
    check = cur.fetchone()
    # If theres no such user or pw is wrong returns false
    if not check:
        flash('Wrong username or password!')
        return False
    else:
        if not check_password_hash(check['password'], request.form.get('password')):
            flash('Wrong username or password!')
            return False
        else:
            # If everything is ok, creates a new session for user
            session['user'] = username
            flash('You were successfully logged in!')
            return True
        
# Regiseters a new user
def register_user():
    # Gets info from the form
    username = request.form.get('username')
    con_email = request.form.get('con_email')
    password = request.form.get('password')
    conpassword = request.form.get('conpassword')
    # Checks the informaion
    errors = []
    errors += username_check(username)
    errors += email_check('users', con_email)
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
        # Logs user in immidiately afer registering
        session['user'] = username
        flash('You were successfully registered!')
        return True

# Deletes users account
def delete_user():
    # Checks if username provided in the delete form is correct
    if request.form.get('username') != session['user']:
        flash('Wrong username provided!')
        return False
    # Connects to database
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    # Checks if user deleting the account is owner in any shelter
    cur.execute("SELECT username FROM keepers WHERE username = ? AND owner = 1", (session['user'],))
    if cur.fetchone():
        con.close()
        flash('You can not delete your account as long as you are a shelter owner!')
        return False
    # Deletes all the information about user from database
    cur.execute("DELETE FROM saved WHERE username = ?", (session['user'],))
    cur.execute("DELETE FROM schedule WHERE username = ?", (session['user'],))
    cur.execute("DELETE FROM volunteers WHERE username = ?", (session['user'],))
    cur.execute("DELETE FROM keepers WHERE username = ?", (session['user'],))
    con.commit()
    con.close()
    # Clears the session
    session.clear()
    flash('Your account was successfully deleted!')
    return True

# Edits information about user
def user_edit_info():
    # Gathers all the information from the form
    con_email = request.form.get('con_email')
    name = request.form.get('name')
    surname = request.form.get('surname')
    phone = request.form.get('phone')
    # Checks if user used new email adress, if not checks if its correct
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT con_email FROM users WHERE username = ?", (session['user'],))
    if cur.fetchone()['con_email'] != con_email:
        errors = email_check('users', con_email)
        if errors:
            for error in errors:
                flash(error)
            con.close()
            return False
    # Updates info on the user
    cur.execute("UPDATE users SET con_email = ?, name = ?, surname = ?, phone = ? WHERE username = ?", (
        con_email,
        name,
        surname,
        phone,
        session['user']
    ))
    con.commit()
    con.close()
    flash('Your profile was successfully updated!')
    return True

# Changes users password
def user_edit_pass():
    # Gathers all the information from the form
    password = request.form.get('password')
    conpassword = request.form.get('conpassword')
    # Connects to database
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if old password is correct
    cur.execute("SELECT password FROM users WHERE username = ?", (session['user'],))
    if not check_password_hash(cur.fetchone()['password'], request.form.get('old_password')):
        con.close()
        flash('Old password is incorrect!')
        return False
    # Checks if new password is correct
    errors = password_check(password, conpassword)
    if errors:
        con.close()
        for error in errors:
            flash(error)
        return False
    # Updates database
    cur.execute("UPDATE users SET password = ? WHERE username = ?", (generate_password_hash(password), session['user']))
    con.commit()
    con.close()
    flash('Your password was successfully changed!')
    return True       


##################################################    USER'S SAVED    ##################################################

# Save animal in users saved
def save_user_animal(animal_id):
    # Connects to database
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if animal exists in database
    cur.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
    if not cur.fetchone():
        flash('Animal does not exist!')
        con.close()
        return False
    # Checks if animal is already in users saved list
    cur.execute("SELECT animal_id FROM saved WHERE username = ? AND animal_id = ?", (session['user'], animal_id))
    if cur.fetchone():
        flash('Animal already in saved list!')
        con.close()
        return False
    # Saves the animal in users saved list
    cur.execute('INSERT INTO saved VALUES (?, ?)', (session['user'], animal_id))
    con.commit()
    con.close()
    flash('Animal was saved!')
    return True

# Delete animal in users saved
def delete_user_animal(animal_id):
    # Connects to database
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    # Checks if animal is in users saved list
    cur.execute("SELECT * FROM saved WHERE username = ? AND animal_id = ?", (session['user'], animal_id))
    if not cur.fetchone():
        flash('Animal is not saved!')
        con.close()
        return False
    # Deletes animal from saved list
    cur.execute("DELETE FROM saved WHERE username = ? AND animal_id = ?", (session['user'], animal_id))
    con.commit()
    con.close()
    flash('Animal was succesfully deleted from saved!')
    return True