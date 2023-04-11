from flask import redirect, session, request, flash
from functools import wraps
import sqlite3
import os
import uuid
from main_checks import login_check, keeper_check, owner_check, volunteer_check

UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png']


####################################################################################################  HELPER FUNCTIONS  ####################################################################################################
# This file contains all the functions that helps the main app to work. It includes decoratiors, information recievers, image saving, etc.


##################################################    DECORATORS    ##################################################

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


##################################################    OTHER    ##################################################

# Let's for creating dictionares of database content
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

# Saves image from form, if theres no image or extension is wrong returns False, else returns it's path
def save_image(save_path):
    image = request.files['image']
    if image.filename != '':
        ext = os.path.splitext(image.filename)[1].lower()
        if ext in UPLOAD_EXTENSIONS:
            image_id = str(uuid.uuid4())
            image_path = save_path + image_id + ext
            image.save(image_path)
            return image_path
    return False


##################################################    INFORMATION RECIEVERS    ##################################################


##############################    USER INFORMATION    ##############################

# Checks status of application user; logged/keeper/owner
def get_user_status(shelter_id):
    user_status = {}
    user_status['login'] = login_check()
    user_status['volunteer'] = volunteer_check(shelter_id)
    user_status['keeper'] = keeper_check(shelter_id)
    user_status['owner'] = owner_check(shelter_id)
    return user_status

# Get users saved animals information
def get_user_saved(username):
     # Connects to database and gets all the information about animals that are in users saved list
     con = sqlite3.connect('database.db')
     con.row_factory = dict_factory
     cur = con.cursor()
     cur.execute("SELECT * FROM animals WHERE id IN (SELECT animal_id FROM saved WHERE username = ?)", (username,))
     animals = cur.fetchall()
     con.close()
     # If theres none, returns falsem otherwise returns the information
     if not animals:
         return False
     return animals

# Gets animals form users schedule
def get_user_schedule():
    # Connects to database and gets all the information from users schedule
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM schedule WHERE username = ?", (session['user'],))
    schedule = cur.fetchall()
    # If theres nothing in users schedule, returns false
    if not schedule:
        con.close()
        return False
    # For each event in schedule gathers few information about animal and it's shelter, then returns it all in list of dicts
    for event in schedule:
        cur.execute("SELECT name, shelter_id FROM animals WHERE id = ?", (event['animal_id'],))
        animal = cur.fetchone()
        event['animal_name'] = animal['name']
        cur.execute("SELECT name, id FROM shelters WHERE id = ?", (animal['shelter_id'],))
        shelter = cur.fetchone()
        event['shelter_name'] = shelter['name']
        event['shelter_id'] = shelter['id']
    con.close()
    return schedule

# Get user info
def get_user_info(username):
    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Selects info about user based on provided username
    cur.execute("SELECT username, con_email, name, surname, phone FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    con.close()
    # If theres no info fetched, returns false, otherwise returns the information
    if not user:
        return False
    else:
        return user
    

##############################    USER INFORMATION - SHELTER RELATION    ##############################
    
# Gets users shelters where user is an owner
def get_user_owners():
    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Selects all the information about shelters where user is an owner
    cur.execute("SELECT * FROM shelters WHERE id IN (SELECT shelter_id FROM keepers WHERE username = ? AND owner = 1)", (session['user'],))
    owner_shelters = cur.fetchall()
    con.close()
    # If theres none, returns empty list, otherwise returns a list with information where user is the owner
    if not owner_shelters:
        return []
    else:
        for shelter in owner_shelters:
            shelter['role'] = 'Owner'
        return owner_shelters
    
# Gets users shelters where user is a keeper
def get_user_keepers():
    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Selects all the information about shelters where user is a keeper
    cur.execute("SELECT * FROM shelters WHERE id IN (SELECT shelter_id FROM keepers WHERE username = ? AND owner = 0)", (session['user'],))
    keeper_shelters = cur.fetchall()
    con.close()
    # If theres none, returns empty list, otherwise returns a list with information where user is the keeper
    if not keeper_shelters:
        return []
    else:
        for shelter in keeper_shelters:
            shelter['role'] = 'Keeper'
        return keeper_shelters
    
# Gets users shelters where user is a volunteer
def get_user_volunteers():
    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Selects all the information about shelters where user is a keeper
    cur.execute("SELECT * FROM shelters WHERE id IN (SELECT shelter_id FROM volunteers WHERE username = ?)", (session['user'],))
    volunteer_shelters = cur.fetchall()
    con.close()
    # If theres none, returns empty list, otherwise returns a list with information where user is the volunteer
    if not volunteer_shelters:
        return []
    else:
        for shelter in volunteer_shelters:
            shelter['role'] = 'Volunteer'
        return volunteer_shelters
    
# Gets users shelters where user is owner, keeper or volunteer in this order
def get_user_shelters():
    # Using other functions gathers all the information and creates one list, if its empty returns false, otherwise returns the list
    shelters = []
    shelters += get_user_owners()
    shelters += get_user_keepers()
    shelters += get_user_volunteers()
    if not shelters:
        return False
    else:
        return shelters


##############################    SHELTER INFORMATION    ##############################

# Gets info about shelter based on provided id
def get_shelter_info(shelter_id):
    # Connects to database
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    # If theres id provided, gathers info about one shelter
    if shelter_id != None:
        cur.execute("SELECT * FROM shelters WHERE id = ?", (shelter_id,))
        shelter = cur.fetchone()
    # If theres None value provided, gather info about all the shelters
    else:
        cur.execute("SELECT * FROM shelters")
        shelter = cur.fetchall()
    con.close()
    # If no info was gathered above, it returns false, otherwise returns all the information
    if not shelter:
        flash('Shelter does not exist')
        return False
    else:
        return shelter
    
# Gets information about keepers of shelter
def get_keepers(shelter_id):
    # Checks if shelter exists
    if not get_shelter_info(shelter_id):
        return False
    # Connects to database and gets all the keepers assigned to shelter, then puts them in a list and returns the list
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username FROM keepers WHERE shelter_id = ?", (shelter_id,))
    keepers = cur.fetchall()
    for keeper in keepers:
        cur.execute("SELECT con_email, name, surname, phone FROM users WHERE username = ?", (keeper['username'],))
        keeper.update(cur.fetchone())
    con.close()
    return keepers

# Gets shelter volunteers
def get_shelter_volunteers(shelter_id):
    # Checks if theres shelter id provided
    if not shelter_id:
        return False
    # Connects to database and gets inforation about users who are volunteers in the shelter
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username IN (SELECT username FROM volunteers WHERE shelter_id = ?)", (shelter_id,))
    volunteers = cur.fetchall()
    con.close()
    # If theres nobody returns false, else returns the list of information
    if not volunteers:
        return False
    return volunteers


##############################    ANIMAL INFORMATION    ##############################

# Gets information about animals in shalter based on provided shelter_id
def get_animals_info(shelter_id):
    # Connects to database
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    # If theres id provided, gathers info about one animal
    if shelter_id != None:
        cur.execute("SELECT * FROM animals WHERE shelter_id = ?", (shelter_id,))
    # If theres None value provided, gathers info about all animals
    else:
        cur.execute("SELECT * FROM animals")
    animals = cur.fetchall()
    # If there is no animal returns false
    if not animals:
        con.close()
        return False
    # Puts all the information in list if theres more animals
    if shelter_id == None:
        for animal in animals:
            cur.execute("SELECT name FROM shelters WHERE id = ?", (animal['shelter_id'],))
            animal['shelter'] = cur.fetchone()['name']
    con.close()
    return animals

# Gets information about single animal based on its id
def get_animal_info(animal_id):
    # Checks for animal id, if none provided, returns false
    if not animal_id:
        return False
    # Connects to database and gets animal info based on provided id
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM animals WHERE id = ?", (animal_id,))
    animal = cur.fetchone()
    con.close()
    # If theres no such animal returns false, else returns the info
    if not animal:
        flash('Animal does not exist!')
        return False
    return animal

# Gets animal vaccinations with animal id
def get_animal_vaccinations(animal_id):
    # Connects to database and gets all vaccination info from it
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM vaccinations WHERE animal_id = ?", (animal_id,))
    vaccinations = cur.fetchall()
    # If theres no info, returns false, otherwise returns the information
    if not vaccinations:
        return False
    return vaccinations