from flask import session, request, flash
import sqlite3
import os
from email_validator import validate_email, EmailNotValidError
from datetime import date

from main_checks import email_check, shelter_form_check
from main_helpers import dict_factory, save_image, get_geocode

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
    # Creates a geocode for the shelter
    geocode = get_geocode(shelter['loc_city'], shelter['loc_adress'], shelter['loc_postal'])
    shelter['geo_lat'] = geocode[0]
    shelter['geo_lng'] = geocode[1]
    # Connects to db and creates new entry
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO shelters (name, loc_city, loc_adress, loc_postal, con_phone, con_email, description, image, geo_lat, geo_lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(
        shelter['name'],
        shelter['loc_city'],
        shelter['loc_adress'],
        shelter['loc_postal'],
        shelter['con_phone'],
        shelter['con_email'],
        shelter['description'],
        shelter['image'],
        shelter['geo_lat'],
        shelter['geo_lng']
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
    # Creates a geocode for the shelter
    geocode = get_geocode(shelter['loc_city'], shelter['loc_adress'], shelter['loc_postal'])
    shelter['geo_lat'] = geocode[0]
    shelter['geo_lng'] = geocode[1]
    # Db entry update
    cur.execute("UPDATE shelters SET name = ?, loc_city = ?, loc_adress = ?, loc_postal = ?, con_phone = ?, con_email = ?, description = ?, image = ?, geo_lat = ?, geo_lng = ? WHERE id = ?",(
        shelter['name'],
        shelter['loc_city'],
        shelter['loc_adress'],
        shelter['loc_postal'],
        shelter['con_phone'],
        shelter['con_email'],
        shelter['description'],
        shelter['image'],
        shelter['geo_lat'],
        shelter['geo_lng'],
        shelter_id
    ))
    con.commit()
    con.close()
    return True

# Addes new demand to supplies db
def add_supply(shelter_id):
    # Checks weather form is filled correctly
    error = False
    name = request.form.get('name')
    if len(name) < 1 or len(name) > 50 or not name.replace(' ','').isalnum():
        error = True
        flash('Please provide a right supply name!')
    demand = int(request.form.get('demand'))
    if demand not in [0, 1, 2]:
        error = True
        flash('Please provide a right demand level!')
    # Checks if product is already on a demand list
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT supply FROM supplies WHERE supply = ? AND shelter_id = ?", (name, shelter_id))
    if cur.fetchone():
        error = True
        flash('Product is already in demands list!')
    # Return false if there are any problems
    if error:
        con.close()
        return False
    # If everything is alright makes a commit in database
    cur.execute("INSERT INTO supplies(shelter_id, supply, demand, date) VALUES (?, ?, ?, ?)", (
        shelter_id,
        name,
        demand,
        date.today()
    ))
    con.commit()
    con.close()
    flash('Product was succesfully added to demands list!')
    return True

# Removes suply from demands db
def delete_supply(shelter_id, supply_id):
    # Connects to db and checks if theres an entry with provided id
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT id FROM supplies WHERE shelter_id = ? AND id = ?", (shelter_id, supply_id))
    if not cur.fetchone():
        con.close()
        flash('There is no such product request in demands!')
        return False
    cur.execute("DELETE FROM supplies WHERE id = ?", (supply_id,))
    con.commit()
    con.close()
    flash('Product request was successfully removed!')
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

# Search for shelters using filters and keywords
def search_for_shelters():
    # Gets search keywords from the form and checks correctness
    keywords = request.form.get('keywords')
    if not keywords:
        return False
    if keywords.replace(' ','').isalnum() == False:
        flash('You can only use letters and numbers!')
        return False
    keywords = keywords.split()
    if len(keywords) > 5:
        flash('Please provide up to 5 words!')
        return False
    # Creates a search query based on checked parameters
    query = ''
    filters = 0
    if request.form.get('name') == 'True':
        query += ' name LIKE ?'
        filters += 1
    if request.form.get('location') == 'True':
        if filters != 0:
            query += ' OR'
        query += ' loc_city LIKE ? OR loc_adress LIKE ?'
        filters += 2
    if request.form.get('description') == 'True':
        if filters != 0:
            query += ' OR'
        query += ' description LIKE ?'
        filters += 1
    # Checks if there are any search parameters
    if query == '':
        flash('No shelters were found!')
        return False
    # Adds 1 query for each keyword
    bu_query = query
    if len(keywords) > 1:
        for i in range(len(keywords) - 1):
            query = query + ' OR' + bu_query
    # Creates tuple with search parameters
    params = ()
    for keyword in keywords:
        for i in range(filters):
            params += (f'%{keyword}%',)
    # Connects to database and prompts it for query with ?, providing the right amount of parameters
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute(f"SELECT * FROM shelters WHERE{query}", params)
    shelters = cur.fetchall()
    con.close()
    # Returns search results
    if shelters:
        return shelters
    else:
        flash('No shelters were found!')
        return False