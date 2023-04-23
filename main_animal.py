from flask import session, request, flash
import sqlite3
import os
from datetime import datetime

from main_checks import date_check, time_check
from main_helpers import dict_factory, save_image, get_pos_hours

ANIMAL_IMAGES_PATH = 'static/animal_images/'


####################################################################################################  FUNCTIONS ASSIGNED TO ANIMAL PROFILE  ####################################################################################################
# This file contains all the functions beeing a core funcionality of the app, that are assigned to animal profile; creation, editing info, schedules etc.


##################################################    ANIMAL    ##################################################

# Adds animal to the shelter
def add_animal(shelter_id):
    # Gathers all the information from the form
    animal = {}
    animal['name'] = request.form.get('name')
    animal['species'] = request.form.get('species')
    animal['sex'] = request.form.get('sex')
    animal['description'] = request.form.get('description')
    animal['urgent'] = request.form.get('urgent')
    # Checks for any errors with information
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
    # Saves image
    image = save_image(ANIMAL_IMAGES_PATH) 
    if image != 1 and image != 2:
        animal['image'] = image
    elif image == 2:
        animal['image'] = 0
        flash('Wrong file extension, no image was added!')
    else:
        animal['image'] = 0
    # Opens db, creates cursor and new db entry
    con = sqlite3.connect("database.db")
    cur = con.cursor() 
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

# Deletes an animal
def delete_animal(animal_id):
    # Opends db, creates a cursor
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if animal with submited id exists
    cur.execute("SELECT name FROM animals WHERE id = ?", (animal_id,))
    name = cur.fetchone()
    if not name:
        con.close()
        flash('Animal does not exist!')
        return False
    # Checks if name from delete form matches name in database
    if request.form.get('name') != name['name']:
        con.close()
        flash('Wrong name provided!')
        return False
    # Removes animal image from server if there is one
    cur.execute("SELECT image FROM animals WHERE id = ?", (animal_id,))
    image = cur.fetchone()
    if image['image'] != 0:
        os.remove(image['image'])
    # Removes all the data about the animal from database
    cur.execute("DELETE FROM schedule WHERE animal_id = ?", (animal_id,))
    cur.execute("DELETE FROM saved WHERE animal_id = ?", (animal_id,))
    cur.execute("DELETE FROM vaccinations WHERE animal_id = ?", (animal_id,))
    cur.execute("DELETE FROM animals WHERE id = ?", (animal_id,))
    con.commit()
    con.close()
    flash('Animal was successfully deleted!')
    return True

# AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA           ZROBIĆ CHECK DLA LAT
# Updates animal info
def update_animal_info(animal_id):
    # Gathers all the information from the form
    animal = {}
    animal['name'] = request.form.get('name')
    animal['species'] = request.form.get('species')
    animal['sex'] = request.form.get('sex')
    animal['description'] = request.form.get('description')
    animal['urgent'] = request.form.get('urgent')
    animal['castrated'] = request.form.get('castrated')
    animal['date_birth'] = request.form.get('date_birth')
    animal['date_shelter'] = request.form.get('date_shelter')
    # Checks for any errors in provided information
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
    # If there are any errors returns false
    if errors:
        for error in errors:
            flash(error)
        return False
    # Saves image
    image = save_image(ANIMAL_IMAGES_PATH) 
    if image != 1 and image != 2:
        animal['image'] = image
    elif image == 2:
        animal['image'] = 0
        flash('Wrong file extension, no image was added!')
    else:
        animal['image'] = 0
    # Opens db, creates cursor and updates all the information
    con = sqlite3.connect("database.db")
    cur = con.cursor()
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

# Updates animal status
def update_animal_status(animal_id):
    # Gathers all the information from form
    pos_status = ['free', 'reserved', 'adopted']
    status = {}
    status['status'] = request.form.get('status')
    status['visibility'] = request.form.get('status_visibility')
    status['visitability'] = request.form.get('status_visitability')
    status['walkability'] = request.form.get('status_walkability')
    # Checks the information
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
    # Connects to db, creates the cursor and updates animal status
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


##################################################    VACCINATIONS    ##################################################

# Adds new vaccine to animal
def add_animal_vaccine(animal_id):
    # Gathers all the information from the form
    vac = {}
    vac['vac_name'] = request.form.get('vac_name')
    vac['vac_for'] = request.form.get('vac_for')
    vac['vac_series'] = request.form.get('vac_series')
    vac['vac_date'] = request.form.get('vac_date')
    vac['vac_exp'] = request.form.get('vac_exp')
    # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA             DODAĆ TESTY                 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    # Connects to db, creates cursor and new db entry
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
    # Connects to db, checks if the vaccine exists and if so removes it
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


##################################################    SCHEDULE    ##################################################

# Schedules an appointment
def schedule_appointment(animal_id):
    # Gets the date from the form and checks it's correctnes
    date = session['appointment']
    app_type = request.form.get('app_type')
    time = request.form.get('app_time')
    if not date_check(date) or not time_check(time):
        flash('Incorrect date!')
        return False
    # Connects to db
    con = sqlite3.connect('database.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if animal with submited id exists
    cur.execute("SELECT id FROM animals WHERE id = ?", (animal_id,))
    if not cur.fetchone():
        con.close()
        flash('Animal does not exist!')
        return False
    # Checks if user already has up to 10 visits scheduled
    cur.execute("SELECT COUNT(*) FROM schedule WHERE username = ? AND date >= ?", (session['user'], datetime.today()))
    count = cur.fetchone()['COUNT(*)']
    if count > 10:
        flash('You can have only up to 10 appointments scheduled!')
        return False
    # Checks if user has already appointment with the animal scheduled for that day
    cur.execute("SELECT username FROM schedule WHERE animal_id = ? AND username = ? AND date = ?", (animal_id, session['user'], date))
    if cur.fetchone():
        con.close()
        flash('You already have an appointment with this animal scheduled for that day!')
        return False
    # Creates an event in animals schedule
    cur.execute("INSERT INTO schedule (animal_id, username, type, date, time) VALUES (?, ?, ?, ?, ?)", (animal_id, session['user'], app_type, date, time))
    con.commit()
    con.close()
    flash('Visit was scheduled for {}!'.format(date))
    session.pop('appointment')
    return True

# Deletes event from animals schedule
def delete_animal_schedule(event_id):
    # Open database and create cursor
    con = sqlite3.connect("database.db")
    con.row_factory = dict_factory
    cur = con.cursor()
    # Checks if event with such id exists and if so
    cur.execute("SELECT username FROM schedule WHERE id = ?", (event_id,))
    event = cur.fetchone()
    if not event:
        con.close()
        flash('There is no such event scheduled for this you!')
        return False
    # Checks if user assigned to the event is same as logged user
    if event['username'] != session['user']:
        con.close()
        flash('It is not your event, you can not delete it!')
        return False
    # Deletes event from schedule
    cur.execute("DELETE FROM schedule WHERE id = ?", (event_id,))
    con.commit()
    con.close()
    flash('Event was successfully deleted from your schedule!')
    return True


##################################################    ANIMAL SEARCH    ##################################################

# Search for animals using filters and keywords
def search_for_animals(shelter_id):
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
    if request.form.get('species') == 'True':
        if filters != 0:
            query += ' OR'
        query += ' species LIKE ?'
        filters += 1
    if request.form.get('description') == 'True':
        if filters != 0:
            query += ' OR'
        query += ' description LIKE ?'
        filters += 1
    if request.form.get('location') == 'True':
        if filters !=0:
            query += ' OR'
        query += ' shelter_id IN (SELECT shelter_id FROM shelters WHERE loc_city LIKE ?)'
        filters += 1
    # Checks if there are any search parameters
    if query == '':
        flash('No animals were found!')
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
    if shelter_id == None:
        cur.execute(f"SELECT * FROM animals WHERE{query}", params)
    else:
        params += (shelter_id,)
        cur.execute(f"SELECT * FROM animals WHERE{query} AND shelter_id = ?", params)
    animals = cur.fetchall()
    con.close()
    # Returns search results
    if animals:
        return animals
    else:
        flash('No animals were found!')
        return False