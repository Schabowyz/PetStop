from flask import redirect, session, request, flash
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from email_validator import validate_email, EmailNotValidError
from f_checks import username_check, email_check, password_check, shelter_form_check, login_check, keeper_check, owner_check, date_check, volunteer_check

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


# Checks status of application user; logged/keeper/owner
def get_user_status(shelter_id):
    user_status = {}
    user_status['login'] = login_check()
    user_status['volunteer'] = volunteer_check(shelter_id)
    user_status['keeper'] = keeper_check(shelter_id)
    user_status['owner'] = owner_check(shelter_id)
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

        session['user'] = username
        flash('You were successfully registered!')
        return True
    

# Gets info about shelter based on provided id
def get_shelter_info(shelter_id):
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    if shelter_id != None:
        cur.execute("SELECT * FROM shelters WHERE id = ?", (shelter_id,))
        shelter = cur.fetchone()
    else:
        cur.execute("SELECT * FROM shelters")
        shelter = cur.fetchall()
    con.close()
    if not shelter:
        flash('Shelter does not exist')
        return False
    else:
        return shelter
    

# Gets information about animals in shalter based on provided shelter_id
def get_animals_info(shelter_id):
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    if shelter_id != None:
        cur.execute("SELECT * FROM animals WHERE shelter_id = ?", (shelter_id,))
    else:
        cur.execute("SELECT * FROM animals")
    animals = cur.fetchall()
    if not animals:
        con.close()
        return False
    if shelter_id == None:
        for animal in animals:
            cur.execute("SELECT name FROM shelters WHERE id = ?", (animal['shelter_id'],))
            animal['shelter'] = cur.fetchone()['name']
    con.close()
    return animals


# Gets information about single animal based on its id
def get_animal_info(animal_id):
    if not animal_id:
        return False
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM animals WHERE id = ?", (animal_id,))
    animal = cur.fetchone()
    con.close()
    if not animal:
        flash('Animal does not exist!')
        return False
    return animal
    
    

# Gets information about keepers of shelter
def get_keepers(shelter_id):
    if not get_shelter_info(shelter_id):
        return False
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
    

# Creates new shelter in database
def add_shelter():
    shelter = {}
    shelter['name'] = request.form.get('name')
    shelter['con_email'] = request.form.get('con_email')
    shelter['loc_city'] = request.form.get('loc_city')
    shelter['loc_adress'] = request.form.get('loc_adress')
    shelter['loc_postal'] = request.form.get('loc_postal')
    shelter['con_phone'] = request.form.get('con_phone')
    shelter['description'] = request.form.get('description')

    errors = shelter_form_check(shelter)
    errors += email_check('shelters', shelter['con_email'])

    if errors:
        for error in errors:
            flash(error)
        return False
    
    image = save_image(SHELTER_IMAGES_PATH)
    if image != False:
        shelter['image'] = image
    else:
        shelter['image'] = None

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

    add_keeper(session['user'], shelter_id)
    add_owner(session['user'], shelter_id)

    return shelter_id


# Edits shelter information
def edit_shelter_info(shelter_id):
    shelter = {}
    shelter['name'] = request.form.get('name')
    shelter['con_email'] = request.form.get('con_email')
    shelter['loc_city'] = request.form.get('loc_city')
    shelter['loc_adress'] = request.form.get('loc_adress')
    shelter['loc_postal'] = request.form.get('loc_postal')
    shelter['con_phone'] = request.form.get('con_phone')
    shelter['description'] = request.form.get('description')

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

    if errors:
        for error in errors:
            flash(error)
        return False
    
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute('SELECT image FROM shelters WHERE id = ?', (shelter_id,))
    curr_image = cur.fetchone()
    print(curr_image)

    image = save_image(SHELTER_IMAGES_PATH)
    if image != False:
        shelter['image'] = image
        if curr_image['image']:
            os.remove(curr_image['image'])
    else:
        shelter['image'] = curr_image['image']

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
    cur.execute("DELETE FROM keepers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    con.commit()
    con.close()
    flash('You have succesfully removed {} from shelter keepers.'.format(username))
    return True


# Adds animal to the shelter
def add_animal(shelter_id):
    animal = {}
    animal['name'] = request.form.get('name')
    animal['species'] = request.form.get('species')
    animal['sex'] = request.form.get('sex')
    animal['description'] = request.form.get('description')
    animal['urgent'] = request.form.get('urgent')
 
    # Checks for any errors with form
    errors = []
    if len(animal['name']) < 1 or len(animal['name']) > 20:
        errors.append("Animal's name must be between 1 and 20 characters long")
    if not animal['name'].replace(' ','').isalnum():
        errors.append("Animal's name can contain only letters and numbers")

    if len(animal['species']) < 1 or len(animal['species']) > 20:
        errors.append("Animal's species must be between 1 and 20 characters long")
    if not animal['species'].replace(' ','').isalnum():
        errors.append("Animal's species can contain only letters and numbers")

    if animal['sex'] != 'male' and animal['sex'] != 'female':
        errors.append("Animal's sex must be either male or female")

    if len(animal['description']) > 500:
        errors.append("Description must be shorter than 500 characters")

    if animal['urgent'] != 'True':
        animal['urgent'] = False
    else:
        animal['urgent'] = True

    # If there are any errors returns false
    if errors:
        for error in errors:
            flash(error)
        return False
    
    # Opens db and creates cursor
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    # Saves image
    image = save_image(ANIMAL_IMAGES_PATH) 
    if image != 1 and image != 2:
        animal['image'] = image
    elif image == 2:
        animal['image'] = 0
        flash('Wrong file extension, no image was added!')
    else:
        animal['image'] = 0
     
    # Creates db input
    cur.execute("INSERT INTO animals (shelter_id, name, species, sex, description, image, urgent) VALUES (?, ?, ?, ?, ?, ?, ?)", (
        shelter_id,
        animal['name'],
        animal['species'],
        animal['sex'],
        animal['description'],
        animal['image'],
        animal['urgent']
    ))
    con.commit()
    con.close()

    return True


# Changes animal status
def update_animal_status(animal_id):

    pos_status = ['free', 'reserved', 'adopted']
    status = {}
    status['status'] = request.form.get('status')
    status['visibility'] = request.form.get('status_visibility')
    status['visitability'] = request.form.get('status_visitability')
    status['walkability'] = request.form.get('status_walkability')

    if status['status'] not in pos_status:
        return False

    if status['visibility'] == 'True':
        status['visibility'] = True
    else:
        status['visibility'] = False
    
    if status['visitability'] == 'True':
        status['visitability'] = True
    else:
        status['visitability'] = False

    if status['walkability'] == 'True':
        status['walkability'] = True
    else:
        status['walkability'] = False


    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("UPDATE animals SET status = ?, status_visibility = ?, status_visitability = ?, status_walkability = ? WHERE id = ?", (
        status['status'],
        status['visibility'],
        status['visitability'],
        status['walkability'],
        animal_id
    ))
    con.commit()
    con.close()

    flash('Animal status was succesfully updated!')
    return True


# AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA           ZROBIĆ CHECK DLA LAT
# Updates animal info
def update_animal_info(animal_id):
    animal = {}
    animal['name'] = request.form.get('name')
    animal['species'] = request.form.get('species')
    animal['sex'] = request.form.get('sex')
    animal['description'] = request.form.get('description')
    animal['urgent'] = request.form.get('urgent')
    animal['castrated'] = request.form.get('castrated')
    animal['date_birth'] = request.form.get('date_birth')
    animal['date_shelter'] = request.form.get('date_shelter')

    # Checks for any errors with form
    errors = []
    if len(animal['name']) < 1 or len(animal['name']) > 20:
        errors.append("Animal's name must be between 1 and 20 characters long!")
    if not animal['name'].replace(' ','').isalnum():
        errors.append("Animal's name can contain only letters and numbers!")

    if len(animal['species']) < 1 or len(animal['species']) > 20:
        errors.append("Animal's species must be between 1 and 20 characters long!")
    if not animal['species'].replace(' ','').isalnum():
        errors.append("Animal's species can contain only letters and numbers!")

    if animal['sex'] != 'male' and animal['sex'] != 'female':
        errors.append("Animal's sex must be either male or female!")

    if len(animal['description']) > 500:
        errors.append("Description must be shorter than 500 characters!")

    if animal['urgent'] != 'True':
        animal['urgent'] = False
    else:
        animal['urgent'] = True

    if animal['castrated'] != 'True':
        animal['castrated'] = False
    else:
        animal['castrated'] = True

    if errors:
        for error in errors:
            flash(error)
        return False
    
    # Opens db and creates cursor
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    # Saves image
    image = save_image(ANIMAL_IMAGES_PATH) 
    if image != 1 and image != 2:
        animal['image'] = image
    elif image == 2:
        animal['image'] = 0
        flash('Wrong file extension, no image was added!')
    else:
        animal['image'] = 0

    # Creates db input
    cur.execute("UPDATE animals SET name = ?, species = ?, sex = ?, description = ?, image = ?, urgent = ?, castrated = ?, date_birth = ?, date_shelter = ? WHERE id = ?", (
        animal['name'],
        animal['species'],
        animal['sex'],
        animal['description'],
        animal['image'],
        animal['urgent'],
        animal['castrated'],
        animal['date_birth'],
        animal['date_shelter'],
        animal_id
    ))
    con.commit()
    con.close()

    flash('Animal information were succesfully updated!')
    return True


# Gets animal vaccinations with animal id
def get_animal_vaccinations(animal_id):
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM vaccinations WHERE animal_id = ?", (animal_id,))
    vaccinations = cur.fetchall()
    if not vaccinations:
        return False
    return vaccinations


# Adds new vaccine to animal
def add_animal_vaccine(animal_id):
    vac = {}
    vac['vac_name'] = request.form.get('vac_name')
    vac['vac_for'] = request.form.get('vac_for')
    vac['vac_series'] = request.form.get('vac_series')
    vac['vac_date'] = request.form.get('vac_date')
    vac['vac_exp'] = request.form.get('vac_exp')

    # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA             DODAĆ TESTY

    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("INSERT INTO vaccinations (animal_id, vac_name, vac_for, vac_series, vac_date, vac_exp) VALUES (?, ?, ?, ?, ?, ?)", (
        animal_id,
        vac['vac_name'],
        vac['vac_for'],
        vac['vac_series'],
        vac['vac_date'],
        vac['vac_exp']
    ))
    con.commit()
    con.close()

    flash('Vaccine was successfully added!')
    return True


# Deletes vaccine with vaccine id
def delete_animal_vaccine(vac_id):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT id FROM vaccinations WHERE id = ?", (vac_id,))
    if not cur.fetchone():
        con.close()
        return False
    cur.execute("DELETE FROM vaccinations WHERE id = ?", (vac_id,))
    con.commit()
    con.close()
    return True


# Get users saved
def get_user_saved(username):
     con = sqlite3.connect('database.db')
     con.row_factory = dict_factory
     cur = con.cursor()
     cur.execute("SELECT * FROM animals WHERE id IN (SELECT animal_id FROM saved WHERE username = ?)", (username,))
     animals = cur.fetchall()
     con.close()
     if not animals:
         return False
     return animals


# Save animal in users saved
def save_user_animal(animal_id):
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
    if not cur.fetchone():
        flash('Animal does not exist!')
        con.close()
        return False
    cur.execute("SELECT animal_id FROM saved WHERE username = ? AND animal_id = ?", (session['user'], animal_id))
    if cur.fetchone():
        flash('Animal already in saved list!')
        con.close()
        return False
    cur.execute('INSERT INTO saved VALUES (?, ?)', (session['user'], animal_id))
    con.commit()
    con.close()
    flash('Animal was saved!')
    return True


# Delete animal in users saved
def delete_user_animal(animal_id):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM saved WHERE username = ? AND animal_id = ?", (session['user'], animal_id))
    if not cur.fetchone():
        flash('Animal is not saved!')
        con.close()
        return False
    cur.execute("DELETE FROM saved WHERE username = ? AND animal_id = ?", (session['user'], animal_id))
    con.commit()
    con.close()
    flash('Animal was succesfully deleted from saved!')
    return True


# Schedules a visit
def schedule_visit(animal_id):
    date = request.form.get('visit')
    if not date_check(date):
        flash('Incorrect date!')
        return False
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
    if not cur.fetchone():
        con.close()
        flash('Animal does not exist!')
        return False
    cur.execute("SELECT username FROM schedule WHERE animal_id = ? AND username = ? AND type = 'visit' AND date = ?", (animal_id, session['user'], date))
    if cur.fetchone():
        con.close()
        flash('You already have a visit with this animal scheduled for that day!')
        return False
    cur.execute("INSERT INTO schedule (animal_id, username, type, date) VALUES (?, ?, 'visit', ?)", (animal_id, session['user'], date))
    con.commit()
    con.close()
    flash('Visit was scheduled for {}!'.format(date))
    return True


# Schedules a walk
def schedule_walk(animal_id):
    date = request.form.get('visit')
    if not date_check(date):
        flash('Incorrect date!')
        return False
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
    if not cur.fetchone():
        con.close()
        flash('Animal does not exist!')
        return False
    cur.execute("SELECT username FROM schedule WHERE animal_id = ? AND username = ? AND type = 'walk' AND date = ?", (animal_id, session['user'], date))
    if cur.fetchone():
        con.close()
        flash('You already have a walk with this animal scheduled for that day!')
        return False
    cur.execute("INSERT INTO schedule (animal_id, username, type, date) VALUES (?, ?, 'walk', ?)", (animal_id, session['user'], date))
    con.commit()
    con.close()
    flash('Walk was scheduled for {}!'.format(date))
    return True


# Gets animals form users schedule
def get_user_schedule():
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM schedule WHERE username = ?", (session['user'],))
    schedule = cur.fetchall()
    if not schedule:
        con.close()
        return False
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


# Gets shelter volunteers
def get_shelter_volunteers(shelter_id):
    if not shelter_id:
        return False
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username IN (SELECT username FROM volunteers WHERE shelter_id = ?)", (shelter_id,))
    volunteers = cur.fetchall()
    con.close()
    if not volunteers:
        return False
    return volunteers


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
    cur.execute("SELECT * FROM volunteers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    if not cur.fetchone():
        con.close()
        flash('{} is not a volunteer in this shelter!'.format(username))
        return False
    cur.execute("DELETE FROM volunteers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    con.commit()
    con.close()
    flash('You have succesfully removed {} from shelter volunteers.'.format(username))
    return True


# Deletes event from animals schedule
def delete_animal_schedule(event_id):

    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username FROM schedule WHERE id = ?", (event_id,))
    event = cur.fetchone()
    if not event:
        con.close()
        flash('There is no such event scheduled for this you!')
        return False
    if event['username'] != session['user']:
        con.close()
        flash('It is not your event, you can not delete it!')
        return False
    cur.execute("DELETE FROM schedule WHERE id = ?", (event_id,))
    con.commit()
    con.close()
    flash('Event was successfully deleted from your schedule!')
    return True


# Get user info
def get_user_info(username):

    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username, con_email, name, surname, phone FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    con.close()
    if not user:
        return False
    else:
        return user
    

# Gets users shelters where user is an owner
def get_user_owners():

    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM shelters WHERE id IN (SELECT shelter_id FROM keepers WHERE username = ? AND owner = 1)", (session['user'],))
    owner_shelters = cur.fetchall()
    con.close()
    if not owner_shelters:
        return []
    else:
        for shelter in owner_shelters:
            shelter['role'] = 'Owner'
        return owner_shelters
    

# Gets users shelters where user is a keeper
def get_user_keepers():

    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM shelters WHERE id IN (SELECT shelter_id FROM keepers WHERE username = ? AND owner = 0)", (session['user'],))
    keeper_shelters = cur.fetchall()
    con.close()
    if not keeper_shelters:
        return []
    else:
        for shelter in keeper_shelters:
            shelter['role'] = 'Keeper'
        return keeper_shelters
    

# Gets users shelters where user is a volunteer
def get_user_volunteers():
 
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT * FROM shelters WHERE id IN (SELECT shelter_id FROM volunteers WHERE username = ?)", (session['user'],))
    volunteer_shelters = cur.fetchall()
    con.close()
    if not volunteer_shelters:
        return []
    else:
        for shelter in volunteer_shelters:
            shelter['role'] = 'Volunteer'
        return volunteer_shelters
    

# Gets users shelters where user is owner, keeper or volunteer in this order
def get_user_shelters():

    shelters = []
    shelters += get_user_owners()
    shelters += get_user_keepers()
    shelters += get_user_volunteers()
    if not shelters:
        return False
    else:
        return shelters


# Deletes users account
def delete_user():

    if request.form.get('username') != session['user']:
        flash('Wrong username provided!')
        return False
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT username FROM keepers WHERE username = ? AND owner = 1", (session['user'],))
    if cur.fetchone():
        con.close()
        flash('You can not delete your account as long as you are a shelter owner!')
        return False
    cur.execute("DELETE FROM saved WHERE username = ?", (session['user'],))
    cur.execute("DELETE FROM schedule WHERE username = ?", (session['user'],))
    cur.execute("DELETE FROM volunteers WHERE username = ?", (session['user'],))
    cur.execute("DELETE FROM keepers WHERE username = ?", (session['user'],))
    con.commit()
    con.close()
    session.clear()
    flash('Your account was successfully deleted!')
    return True


# Deletes an animal
def delete_animal(animal_id):

    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT name FROM animals WHERE id = ?", (animal_id,))
    name = cur.fetchone()
    if not name:
        con.close()
        flash('Animal does not exist!')
        return False
    if request.form.get('name') != name['name']:
        con.close()
        flash('Wrong name provided!')
        return False
    cur.execute("DELETE FROM schedule WHERE animal_id = ?", (animal_id,))
    cur.execute("DELETE FROM saved WHERE animal_id = ?", (animal_id,))
    cur.execute("DELETE FROM vaccinations WHERE animal_id = ?", (animal_id,))
    cur.execute("DELETE FROM animals WHERE id = ?", (animal_id,))
    con.commit()
    con.close()
    flash('Animal was successfully deleted!')
    return True