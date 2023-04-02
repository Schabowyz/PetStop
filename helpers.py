from email_validator import validate_email, EmailNotValidError
from flask import redirect, session, request
from functools import wraps
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid

UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png']
ANIMAL_IMAGES_PATH = 'static/animal_images/'
SHELTER_IMAGES_PATH = 'static/shelter_images/'


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


# Function to convert tuple to string, if tuple is empty, it returns None
def conv_tup_to_str(tup):
    if tup != None:
        string = ''.join(tup)
        return string
    else:
        return None


# Login requirement decorator for routs in app
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Keeper requirment decorator for routs in app
def keeper_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if shelter_check() == False:
            return redirect("/yourshelter")
        return f(*args, **kwargs)
    return decorated_function


# Saves image from form, if theres no image returns False, else returns it's path
def save_image(save_path):
    image = request.files['image']
    if image.filename != '':
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in UPLOAD_EXTENSIONS:
            return 1
        else:
            image_id = str(uuid.uuid4())
            image_path = save_path + image_id + ext
            image.save(image_path)
            return image_path
    else:
        return 2


# Checks if user is logged in 
def login_check():
    if "user" in session:
        return True
    else:
        return False
    

# Check registriation parameters with other functions
def registration_check(username, email, password, conpass):
    errors = []
    for error in username_check(username):
        errors.append(error)
    for error in email_check('users', email):
        errors.append(error)
    for error in password_check(password, conpass):
        errors.append(error)
    return errors

# Username check
def username_check(username): 
    errors = []

    if len(username) < 4 or len(username) > 20:
        errors.append("Username lenght must be between 4 and 20 characters!")

    if not username.isalnum():
        errors.append("Username must contain only letters and numbers!")

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    if username == conv_tup_to_str(cur.fetchone()):
        errors.append("Username is already taken!")

    return errors

# Email check
def email_check(table, email):
    errors = []
    print(table, email)

    try:
        validate = validate_email(email)
        email = validate["email"]
    except EmailNotValidError:
        errors.append("Incorrect email adress!")

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT con_email FROM " +table+ " WHERE con_email = ?", (email,))
    if email == conv_tup_to_str(cur.fetchone()):
        errors.append("Email adress already taken!")

    return errors

# Password check
def password_check(password, conpass):
    errors = []

    if password != conpass:
        errors.append("Passwords don't match!")
    
    if len(password) < 3 or len(password) > 20:
        errors.append("Password must be between 8 and 20 characters long!")

    return errors


# Register new user
def register_user(username, email, password):
    
    # Create hash password form password
    password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO users (username, con_email, password) VALUES (?, ?, ?)", (username, email, password))
    con.commit()
    con.close()

    session["user"] = username

    return


# Check login parameters
def login_user(username, password):
    # Connects to database, requesting for dictionaries instead of tuples
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    # Checks if username is in database
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    try:
        username = cur.fetchone()["username"]
    except TypeError:
        con.close()
        return "Wrong username or password!"
    
    # Checks if usrname fits password
    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    correct_password = cur.fetchone()["password"]
    if not check_password_hash(correct_password, password):
        con.close()
        return "Wrong username or password!"
    
    con.close()
    return


# Check if logged person is a keeper
def shelter_check():
    # Connects to database, requesting for dictionaries instead of tuples
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    # Try to get shelters id, if not possible return False
    try:
        cur.execute("SELECT * FROM keepers WHERE username = ?", (session['user'],))
        shelter_id = cur.fetchone()['shelter_id']
        con.close()
        return shelter_id
    except TypeError:
        con.close()
        return False
    except KeyError:
        con.close()
        return False
    

# Adds new keeper to shelter
def add_keeper(username, shelter_id):
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (username,))
    check = cur.fetchone()
    if not check:
        return "There's no user named {}".format(username)
    cur.execute("SELECT username FROM keepers WHERE username = ?", (username,))
    check = cur.fetchone()
    if check != None:
        if check['username'] == username:
            return "{} is already a keeper in this shelter".format(username)
    cur.execute("INSERT INTO keepers VALUES (?, ?, 0)", (username, shelter_id))
    con.commit()
    con.close()
    return None


# Makes new shelter owner
def make_owner(username, shelter_id):
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username FROM keepers WHERE shelter_id = ? AND owner = 1", (shelter_id,))
    check = cur.fetchone()
    if not check:
        return "There's no such user"
    if check['username'] != session['user']:
        return "Only shelter owner can make a new owner"
    if check['username'] == username:
        return "{} is already a shelter owner".format(username)
    cur.execute("SELECT username FROM keepers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    check = cur.fetchone()
    if not check:
        return "{} is not keeper of this shelter and can't be made an owner".format(username)
    
    cur.execute("UPDATE keepers SET owner = 0 WHERE shelter_id = ? AND owner = 1", (shelter_id,))
    cur.execute("UPDATE keepers SET owner = 1 WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    con.commit()
    con.close()
    return "{} is a new shelter owner".format(username)
    

# Gets all shelter information in form of dictionary, using shelter id
def get_shelter_info(shelter_id):
    # Connects to database
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Gets information and returns them
    cur.execute("SELECT * FROM shelters WHERE id = ?", (shelter_id,))
    shelter_info = cur.fetchone()
    con.close()

    return shelter_info


def check_shelter_form():
    errors = []

    # Gets all information from form
    shelter = {}
    shelter['name'] = request.form.get('name')
    shelter['loc_city'] = request.form.get('loc_city')
    shelter['loc_adress'] = request.form.get('loc_adress')
    shelter['loc_postal'] = request.form.get('loc_postal')
    shelter['con_phone'] = request.form.get('con_phone')
    shelter['con_email'] = request.form.get('con_email')
    shelter['description'] = request.form.get('description')

    # Checks all the data
    if shelter['name'].isalnum() == False:
        errors.append("Shelter name can only contain letters and numbers")
    if len(shelter['name']) < 4 or len(shelter['name']) > 20:
        errors.append("Shlelter name must be between 4 and 20 character long")
    
    if shelter['loc_city'].isalnum() == False:
        errors.append("Please provide right city name")

    if not shelter['loc_adress']:
        errors.append("Please provide right adress")

    if not shelter['loc_postal']:
        errors.append("Please provide right postal code")

    if not shelter['con_phone']:
        errors.append("Please provide right phone number")

    if len(shelter['description']) > 1000:
        errors.append("Description must be shorter than 1000 characters")

    return shelter, errors


# Create shelter
def create_new_shelter():
    # If there are any errors, returns errors list, else proceeds to put shelter in db
    info = check_shelter_form()
    errors = info[1]
    errors = errors + email_check('shelters', info[0]['con_email'])
    if errors:
        return False, errors
    
    shelter = info[0]

    image = save_image(SHELTER_IMAGES_PATH)
    if image != 1 and image != 2:
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

    add_keeper(session['user'], shelter_id)

    return shelter_id, errors


# Edits shelter information
def edit_shelter_information(shelter_id):

    # Gets info from shelter from and it's correctness
    info = check_shelter_form()
    shelter = info[0]
    errors = info[1]

    # Checks if email was changed, if so checks it's correctness
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT con_email FROM shelters WHERE id = ?", (shelter_id,))
    curr_email = conv_tup_to_str(cur.fetchone())
    if curr_email != shelter['con_email']:
        errors = errors + email_check('shelters', shelter['con_email'])

    # If there are any errors returns False and errors list
    if errors:
        con.close()
        return False, errors
    
    # If theres a new image in form and it's ok removes old one and repalaces it with new one, otherwise leaves old one
    cur.execute("SELECT image FROM shelters WHERE id = ?", (shelter_id,))
    curr_image = cur.fetchone()
    if curr_image[0] != None:
        curr_image = conv_tup_to_str(curr_image)
    else:
        curr_image = None
    image = save_image(SHELTER_IMAGES_PATH)
    if image != 1 and image != 2:
        if curr_image != None:
            os.remove(curr_image)
        shelter['image'] = image
    else:
        shelter['image'] = curr_image

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

    return True, errors
    

# Gets all shelter keepers using shelter id
def get_shelter_keepers(shelter_id):
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    cur.execute("SELECT username FROM keepers WHERE shelter_id = ?", (shelter_id,))
    shelter_keepers = cur.fetchall()
    con.close()

    return shelter_keepers


# Gets information about profile using username
def get_profile_info(username):
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    cur.execute("SELECT username, con_email, name, surname, phone FROM users WHERE username = ?", (username,))
    profile_info = cur.fetchone()
    con.close()

    return profile_info


# Creates a list of shelter keepers, together with all their info
def get_keepers_info(shelter_id):
    shelter_keepers = get_shelter_keepers(shelter_id)
    for keeper in shelter_keepers:
        keeper.update(get_profile_info(keeper['username']))
    return shelter_keepers


# Checks if animal info is ok and puts it in database
def insert_animal_info(shelter_id):
    errors = []

    animal = {}
    animal['name'] = request.form.get('name')
    animal['species'] = request.form.get('species')
    animal['sex'] = request.form.get('sex')
    animal['description'] = request.form.get('description')

    if len(animal['name']) < 1 or len(animal['name']) > 20:
        errors.append("Animal's name must be between 1 and 20 characters long")
    if not animal['name'].isalnum():
        errors.append("Animal's name can contain only letters and numbers")

    if len(animal['species']) < 1 or len(animal['species']) > 20:
        errors.append("Animal's species must be between 1 and 20 characters long")

    if animal['sex'] != 'male' and animal['sex'] != 'female':
        errors.append("Animal's sex must be either male or female")

    if len(animal['description']) > 500:
        errors.append("Description must be shorter than 500 characters")

    # Checks if any errors occured
    if not errors:

        # Opens db and creates cursor
        con = sqlite3.connect("database.db")
        cur = con.cursor()

        # Saves image
        image = save_image(ANIMAL_IMAGES_PATH) 
        if image != 1 and image != 2:
            animal['image'] = image
        elif image == 2:
            errors.append('Wrong file extension, your animal was added without image')
         
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

    return errors

def get_shelter_animals(shelter_id):

    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()

    cur.execute("SELECT name, species, image, description FROM animals WHERE shelter_id = ?", (shelter_id,))
    animals = cur.fetchall()
    con.close()

    return animals


def remove_keeper(username, shelter_id):

    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("SELECT username FROM keepers WHERE shelter_id = ? AND owner = 1", (shelter_id))
    if cur.fetchone()['username'] != session['user']:
        con.close()
        return "You have to be shelter owner to remove a keeper."
    cur.execute("SELECT owner FROM keepers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    if cur.fetchone()['owner'] == 1:
        con.close()
        return "You can't remove owner, you have to set different owner first."
    cur.execute("DELETE FROM keepers WHERE username = ? AND shelter_id = ?", (username, shelter_id))
    con.commit()
    con.close()
    return "You have succesfully removed {} from shelter keepers.".format(username)