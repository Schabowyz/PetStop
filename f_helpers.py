from flask import redirect, session, request, flash
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from email_validator import validate_email, EmailNotValidError
from f_checks import username_check, email_check, password_check, shelter_form_check, login_check, keeper_check, owner_check

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


# Checks if logged user is keeper in a shelter and if so returns it's id
def check_user_shelter():
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT shelter_id FROM keepers WHERE username = ?", (session['user'],))
    shelter_id = cur.fetchone()
    con.close()
    if not shelter_id:
        return False
    else:
        return shelter_id['shelter_id']
    

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
        animal['image'] = None
        flash('Wrong file extension, your animal was added without image')
    else:
        animal['image'] = None
     
    # Creates db input
    cur.execute("INSERT INTO animals (shelter_id, name, species, sex, description, image) VALUES (?, ?, ?, ?, ?, ?)", (
        shelter_id,
        animal['name'],
        animal['species'],
        animal['sex'],
        animal['description'],
        animal['image']
    ))
    con.commit()
    con.close()

    return True