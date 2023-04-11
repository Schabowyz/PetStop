from flask import session, request, flash
import sqlite3
import os
from email_validator import validate_email, EmailNotValidError

from main_checks import email_check, shelter_form_check
from main_helpers import dict_factory, save_image

SHELTER_IMAGES_PATH = 'static/shelter_images/'


####################################################################################################  FUNCTIONS ASSIGNED TO SHELTER PROFILE  ####################################################################################################
# This file contains all the functions beeing a core funcionality of the app, that are assigned to shelter profile; creation, editing info, etc.


##################################################    SHELTER    ##################################################

# Creates new shelter in database
def add_shelter():
    # Gathers all the information from the form
    shelter = {}
    shelter['name'] = request.form.get('name')
    shelter['con_email'] = request.form.get('con_email')
    shelter['loc_city'] = request.form.get('loc_city')
    shelter['loc_adress'] = request.form.get('loc_adress')
    shelter['loc_postal'] = request.form.get('loc_postal')
    shelter['con_phone'] = request.form.get('con_phone')
    shelter['description'] = request.form.get('description')
    # Checks for errors and if there are any returns fals
    errors = shelter_form_check(shelter)
    errors += email_check('shelters', shelter['con_email'])
    if errors:
        for error in errors:
            flash(error)
        return False
    # Saves image if theres one
    image = save_image(SHELTER_IMAGES_PATH)
    if image != False:
        shelter['image'] = image
    else:
        shelter['image'] = 0
    # Connects to db and creates new entry
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO shelters (name, loc_city, loc_adress, loc_postal, con_phone, con_email, description, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(
        shelter['name'],
        shelter['loc_city'],
        shelter['loc_adress'],
        shelter['loc_postal'],
        shelter['con_phone'],
        shelter['con_email'],
        shelter['description'],
        shelter['image']
    ))
    con.commit()
    shelter_id = cur.lastrowid
    con.close()
    flash('Shelter was successfully created!')
    # Adds logged user as shelter keeper and shelter owner
    add_keeper(session['user'], shelter_id)
    add_owner(session['user'], shelter_id)
    return shelter_id

# Edits shelter information
def edit_shelter_info(shelter_id):
    # Gathers all the information from the form
    shelter = {}
    shelter['name'] = request.form.get('name')
    shelter['con_email'] = request.form.get('con_email')
    shelter['loc_city'] = request.form.get('loc_city')
    shelter['loc_adress'] = request.form.get('loc_adress')
    shelter['loc_postal'] = request.form.get('loc_postal')
    shelter['con_phone'] = request.form.get('con_phone')
    shelter['description'] = request.form.get('description')
    # Checks for errors and if there are any returns fals
    errors = shelter_form_check(shelter)
    try:
        validate = validate_email(shelter['con_email'])
        shelter['con_email'] = validate['email']
    except EmailNotValidError:
        errors.append('Incorrect email adress!')
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT con_email FROM shelters WHERE con_email = ? AND id != ?", (shelter['con_email'], shelter_id))
    if cur.fetchone():
        errors.append('Email adress is already taken!')
    # If there are any errors returns false
    if errors:
        for error in errors:
            flash(error)
        return False
    # Connects to db and gets current image from it
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute('SELECT image FROM shelters WHERE id = ?', (shelter_id,))
    curr_image = cur.fetchone()
    # If theres new image uploaded, old one is switched, else its left alone
    image = save_image(SHELTER_IMAGES_PATH)
    if image != False:
        shelter['image'] = image
        if curr_image['image']:
            os.remove(curr_image['image'])
    else:
        shelter['image'] = curr_image['image']
    # Db entry update
    cur.execute("UPDATE shelters SET name = ?, loc_city = ?, loc_adress = ?, loc_postal = ?, con_phone = ?, con_email = ?, description = ?, image = ? WHERE id = ?",(
        shelter['name'],
        shelter['loc_city'],
        shelter['loc_adress'],
        shelter['loc_postal'],
        shelter['con_phone'],
        shelter['con_email'],
        shelter['description'],
        shelter['image'],
        shelter_id
    ))
    con.commit()
    con.close()
    return True


##################################################    SHELTER STAFF    ##################################################

# Adds new keeper to shelter
def add_keeper(username, shelter_id):
    # Checks if passed vriables have have value
    if not username:
        return False
    if not shelter_id:
        return False
    # Connects to database
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if there's user 'username'
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    check = cur.fetchone()
    if not check:
        flash('There is no user named {}!'.format(username))
        return False
    # Checks if user is already keeper in the shelter
    cur.execute("SELECT username FROM keepers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    check = cur.fetchone()
    if check:
        flash('{} is already a keeper in this shelter!'.format(username))
        return False
    # After passing all tests, puts new user as keeper
    cur.execute("INSERT INTO keepers VALUES (?, ?, 0)", (username, shelter_id))
    con.commit()
    con.close()
    return True

# Update keeper to an owener of shelter
def add_owner(username, shelter_id):
    # Checks if passed vriables have have value
    if not username:
        return False
    if not shelter_id:
        return False 
    # Connects to database
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if there's user 'username' in shelter keepers
    cur.execute("SELECT username FROM keepers WHERE shelter_id = ?", (shelter_id,))
    check = cur.fetchone()
    print(check)
    if not check:
        flash('{} is not a keeper in this shelter and can not be made an owner!'.format(username))
        return False
    # Removes old owner and add a new one
    cur.execute("UPDATE keepers SET owner = 0 WHERE shelter_id = ? AND owner = 1", (shelter_id,))
    cur.execute("UPDATE keepers SET owner = 1 WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    con.commit()
    con.close()
    flash('{} was successfully made an owner of this shelter!'.format(username))
    return True

# Deletes keeper form a shelter
def delete_keeper(shelter_id, username):
    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Check if deleted person isn't owner
    cur.execute("SELECT owner FROM keepers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    owner = cur.fetchone()
    if owner:
        if owner['owner'] == 1:
            con.close()
            flash('You can not remove owner, you have to set different owner first!')
            return False
    # Deletes a keeper
    cur.execute("DELETE FROM keepers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    con.commit()
    con.close()
    flash('You have succesfully removed {} from shelter keepers.'.format(username))
    return True


##################################################    SHELTER VOLUNTEERS    ##################################################

# Add new volunteer to the shelter
def add_volunteer(username, shelter_id):
    # Checks if passed vriables have have value
    if not username:
        return False
    if not shelter_id:
        return False
    # Connects to database
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if there's user 'username'
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    check = cur.fetchone()
    if not check:
        flash('There is no user named {}!'.format(username))
        return False
    # Checks if person is already a keeper in sheter
    cur.execute("SELECT username FROM keepers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    check = cur.fetchone()
    if check:
        flash('{} is already a keeper in this shelter!'.format(username))
        return False
    # Checks if user is already volunteer in the shelter
    cur.execute("SELECT username FROM volunteers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    check = cur.fetchone()
    if check:
        flash('{} is already a volunteer in this shelter!'.format(username))
        return False
    # After passing all tests, puts new user as keeper
    cur.execute("INSERT INTO volunteers VALUES (?, ?)", (username, shelter_id))
    con.commit()
    con.close()
    flash('{} was successfully added as shelter volunteer!'.format(username))
    return True

# Deletes volunteer from shelter
def delete_volunteer(shelter_id, username):
    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if user is a volunteer in the shelter
    cur.execute("SELECT * FROM volunteers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    if not cur.fetchone():
        con.close()
        flash('{} is not a volunteer in this shelter!'.format(username))
        return False
    # Deletes user form volunteers
    cur.execute("DELETE FROM volunteers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    con.commit()
    con.close()
    flash('You have succesfully removed {} from shelter volunteers.'.format(username))
    return True


##################################################    SHELTER SEARCH    ##################################################

# Search filters for shelters
# By name
# By location
# By description
def search_shelters():

    # Gets search keywords from the form
    keywords = request.form.get('keywords')

    # Splits keywords to list of words and adds %% OR to each of them for sql purposes
    keywords = keywords.split()
    for i in range(len(keywords)):
        keywords[i] = " '%{}%' OR".format(keywords[i])

    # Gets search parameters from the form    
    parameters = []
    if request.form.get('name') == 'True':
        parameters.append(' name ')
    if request.form.get('location') == 'True':
        parameters.append(' loc_city ')
        parameters.append(' loc_adress ')
    if request.form.get('description') == 'True':
        parameters.append(' description ')

    # Creates variable query that will store sql query for search    
    query = ''

    # For each parameter that was selected expands query with: parameter LIKE %search_keyword% OR
    for parameter in parameters:
        for keyword in keywords:
            query += '{}LIKE{}'.format(parameter, keyword)

    # Deletes ' OR' at the end of query
    query = query[:-3]

    # Connects to database and fetches all the results for the query
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM shelters WHERE{}".format(query))
    shelters = cur.fetchall()
    con.close()
    
    # If there are no results returns false, otherwise returns the results
    if not shelters:
        return False
    else:
        return shelters
