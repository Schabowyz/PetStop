from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from datetime import timedelta

from main_helpers import login_required, logout_required, get_user_status, get_shelter_info, get_animals_info, get_keepers, get_animal_info, get_animal_vaccinations, get_user_saved, get_user_schedule, get_shelter_volunteers, get_user_info, get_user_shelters, get_coords, get_shelter_supplies, get_pos_day, get_pos_hours, get_animal_schedule, get_opening_hours
from main_user import login_user, register_user, save_user_animal, delete_user_animal, delete_user, user_edit_info, user_edit_pass
from main_shelter import add_shelter, edit_shelter_info, delete_keeper, add_keeper, add_owner, add_volunteer, delete_volunteer, search_for_shelters, add_supply, delete_supply
from main_animal import add_animal, update_animal_status, update_animal_info, add_animal_vaccine, delete_animal_vaccine, schedule_appointment, delete_animal_schedule, delete_animal, search_for_animals
from main_checks import keeper_check, owner_check, animal_walk_check

from keys import secret_key, api_key


# Configure application
app = Flask(__name__)

# Configure app backed server session
app.config['SESSION_PERMAMENT'] = True
app.config['PERMAMENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SECRET_KEY'] = secret_key
app.config['SESSION_TYPE'] = 'filesystem'

# Configure uploads settings
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png']
app.config['ANIMAL_IMAGES'] = 'static/animal_images'

Session(app)

POS_SPECIES = ['dog', 'cat', 'bunny', 'chameleon']



############################################# ROUTES #############################################


# Index page
@app.route('/')
def index():

    return render_template('index.html', user_status=get_user_status(None))


# Page not found
@app.route('/404')
def not_found():

    return render_template('404.html', user_status=get_user_status(None))


#################### USER ####################


# Login page
@app.route('/login', methods = ['GET', 'POST'])
@logout_required
def user_login():

    # Clears all information that could be stored in session
    session.clear()

    if request.method == 'POST':
        # Tries to log user
        log = login_user()
        if log == True:
            return redirect ('/')

    return render_template('user_login.html', user_status=get_user_status(None))


# Logout
@app.route('/logout')
@login_required
def user_logout():

    # Clears all session info and redirects to homepage
    session.clear()
    return redirect('/')


# Register page
@app.route('/register', methods = ['GET', 'POST'])
@logout_required
def user_register():

    # Clears all information that could be stored in session
    session.clear()

    if request.method == 'POST':
        reg = register_user()
        # Tries to register user
        if reg == True:
            return redirect('/')

    return render_template('user_register.html', user_status=get_user_status(None))


# User profile page
@app.route('/profile')
@login_required
def user_profile():

    return render_template('user_profile.html', user_status=get_user_status(None), user=get_user_info(session['user']), animals=get_user_saved(session['user']), shelters=get_user_shelters())


# User profile delete
@app.route('/profile/delete', methods = ['POST'])
@login_required
def user_delete():

    if delete_user():
        return redirect('/')
    else:
        return redirect('/profile')  


# User profile edit
@app.route('/profile/information', methods = ['GET', 'POST'])
@login_required
def user_edit_information():

    if request.method == 'POST':
        if user_edit_info():
            return redirect('/profile')

    return render_template('user_info.html', user_status=get_user_status(None), user=get_user_info(session['user']))


# User password change
@app.route('/profile/information/password', methods = ['GET', 'POST'])
@login_required
def user_edit_password():

    if request.method == 'POST':
        if user_edit_pass():
            return redirect('/profile')
        
    return render_template('user_password.html', user_status=get_user_status(None))


# User saved animals
@app.route('/youranimals')
@login_required
def user_animals():

    return render_template('user_youranimals.html', user_status=get_user_status(None), animals=get_user_saved(session['user']))


# User saved animals remove
@app.route('/youranimals/<animal_id>/delete')
@login_required
def user_animals_delete(animal_id):

    delete_user_animal(animal_id)

    return redirect('/youranimals')


# Users schedule
@app.route('/yourschedule')
@login_required
def user_schedule():

    return render_template('user_yourschedule.html', user_status=get_user_status(None), schedule=get_user_schedule())


# Delete event from schedule
@app.route('/yourschedule/delete/<event_id>')
@login_required
def animal_schedule_delete(event_id):

    delete_animal_schedule(event_id)

    return redirect('/yourschedule')


# User's shelter page
@app.route('/yourshelters')
@login_required
def shelter_yourshelter():

    return render_template('user_yourshelters.html', user_status=get_user_status(None), shelters=get_user_shelters())
    

# Create new shelter
@app.route('/createshelter', methods = ['GET', 'POST'])
@login_required
def shelter_create():

    if request.method == 'POST':
        # Tries to create new shelter, if it works redirects to its page
        shelter_id = add_shelter()
        if not shelter_id:
            return render_template('shelter_create.html', user_status = get_user_status(None))
        else:
            return redirect('/shelter/{}'.format(shelter_id))
    
    return render_template('shelter_create.html', user_status = get_user_status(None))
   


#################### SHELTER ####################


# Shelter page
@app.route('/shelter/<shelter_id>', methods = ['GET', 'POST'])
def shelter_main(shelter_id):

    coords = get_coords(shelter_id)

    shelter = get_shelter_info(shelter_id)
    if not shelter:
        return redirect('/404')
    
    animals = get_animals_info(shelter_id)

    if request.method == 'POST':
        animals = search_for_animals(shelter_id)

    return render_template('shelter_main.html', user_status=get_user_status(shelter_id), shelter=shelter, animals=animals, db={}, coords=coords, api_key=api_key, supplies=get_shelter_supplies(shelter_id), opening_hours=get_opening_hours(shelter_id))


# Edit information
@app.route('/shelter/<shelter_id>/information', methods = ['GET', 'POST'])
@login_required
def shelter_edit_information(shelter_id):

    if not keeper_check(shelter_id):
        flash('You have to be shelter keeper to acces this page!')
        return redirect('/shelter/{}'.format(shelter_id))
    
    # Makes changes in shelter information
    if request.method == 'POST':
        if edit_shelter_info(shelter_id):
            flash('Changes were successfully implemented!')

    return render_template('shelter_info.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), db={'info': 'disabled'}, opening_hours=get_opening_hours(shelter_id))


# Edit needs
@app.route('/shelter/<shelter_id>/needs', methods = ['GET', 'POST'])
def shelter_edit_needs(shelter_id):

    if request.method == 'POST':
        add_supply(shelter_id)
    
    return render_template('shelter_needs.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), db={'needs': 'disabled'}, supplies=get_shelter_supplies(shelter_id))


# Delete needs
@app.route('/shelter/<shelter_id>/needs/delete/<supply_id>')
@login_required
def shelter_delete_supply(shelter_id, supply_id):

    if not keeper_check(shelter_id):
        flash('You have to be shelter keeper to do it!')
        return redirect('/shelter/{}'.format(shelter_id))
    
    delete_supply(shelter_id, supply_id)

    return redirect('/shelter/{}/needs'.format(shelter_id))


# Edit keepers
@app.route('/shelter/<shelter_id>/keepers', methods = ['GET', 'POST'])
@login_required
def shelter_edit_keepers(shelter_id):

    if not keeper_check(shelter_id):
        flash('You have to be shelter keeper to acces this page!')
        return redirect('/shelter/{}'.format(shelter_id))
    
    if request.method == 'POST':
        if add_keeper(request.form.get('username'), shelter_id):
            flash('{} was successfully added as shelter keeper!'.format(request.form.get('username')))

    return render_template('shelter_keepers.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), keepers=get_keepers(shelter_id), db={'keepers': 'disabled'})


# Delete keeper
@app.route('/shelter/<shelter_id>/delete/<username>')
@login_required
def shelter_remove_keeper(shelter_id, username):

    if not owner_check(shelter_id):
        flash('Only shelter owner can remove a shalter keeper!')
        return redirect('/shleter/{}/keepers'.format(shelter_id))
    
    if not delete_keeper(shelter_id, username):
        return redirect('/shelter/{}/keepers'.format(shelter_id))
    
    return render_template('shelter_keepers.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), keepers=get_keepers(shelter_id), db={'keepers': 'disabled'})


# Make owner
@app.route('/shelter/<shelter_id>/owner/<username>')
@login_required
def shelter_make_owner(username, shelter_id):

    if not owner_check(shelter_id):
        flash('Only shelter owner can set a new owner!')
        return redirect('/shleter/{}/keepers'.format(shelter_id))
    
    if not add_owner(username, shelter_id):
        return redirect('/shelter/{}/keepers'.format(shelter_id))
    
    return render_template('shelter_keepers.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), keepers=get_keepers(shelter_id), db={'keepers': 'disabled'})


# Add new animal to shelter
@app.route('/shelter/<shelter_id>/addanimal', methods = ['GET', 'POST'])
@login_required
def shelter_add_animal(shelter_id):

    if not keeper_check(shelter_id):
        flash('Only shelter keepers can add a new animal to the shelter!')
        return redirect('/shelter/{}'.format(shelter_id))
    
    if request.method == 'POST':
        if add_animal(shelter_id):
            flash('Animal was succesfully added to shelter!')
            return redirect('/shelter/{}'.format(shelter_id))
        
    return render_template('shelter_animal.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), keepers=get_keepers(shelter_id), db={'animal': 'disabled'}, species=POS_SPECIES)


# Check adopted animals from a shelter
@app.route('/shelter/<shelter_id>/adopted')
@login_required
def shelter_adopted_animals(shelter_id):

    shelter = get_shelter_info(shelter_id)
    if not shelter:
        return redirect('/404')

    if not keeper_check(shelter_id):
        flash('Only shelter keepers can add a new animal to the shelter!')
        return redirect('/shelter/{}'.format(shelter_id))
    
    animals = get_animals_info(shelter_id)
    
    return render_template('shelter_adopted.html', user_status=get_user_status(shelter_id), shelter=shelter, animals=animals, db={'adopted': 'disabled'}, supplies=get_shelter_supplies(shelter_id), opening_hours=get_opening_hours(shelter_id))


# Edit volunteers
@app.route('/shelter/<shelter_id>/volunteers', methods = ['GET', 'POST'])
@login_required
def shelter_edit_volunteers(shelter_id):
    
    if not keeper_check(shelter_id):
        flash('Only shelter keepers can access this page!')
        return redirect('/shelter/{}'.format(shelter_id))
    
    if request.method == 'POST':
        add_volunteer(request.form.get('username'), shelter_id)

    return render_template('shelter_volunteers.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), volunteers=get_shelter_volunteers(shelter_id), db={'volunteers': 'disabled'})


# Delete volunteer
@app.route('/shelter/<shelter_id>/volunteers/delete/<username>')
@login_required
def shelter_delete_volunteer(shelter_id, username):

    if not keeper_check(shelter_id):
        flash('Only shelter keepers can delete volunteers!')
        return redirect('/shelter/{}/volunteers'.format(shelter_id))
    
    delete_volunteer(shelter_id, username)

    return redirect('/shelter/{}/volunteers'.format(shelter_id))



#################### ANIMAL ####################


@app.route('/animal/<animal_id>')
def animal_main(animal_id):

    animal = get_animal_info(animal_id)
    if not animal:
        return redirect('/404')
    coords = get_coords(animal['shelter_id'])
    
    return render_template('animal_main.html', user_status=get_user_status(animal['shelter_id']), animal=animal, shelter=get_shelter_info(animal['shelter_id']), vaccinations=get_animal_vaccinations(animal_id), coords=coords, api_key=api_key, opening_hours=get_opening_hours(animal['shelter_id']))


# Edit animal info
@app.route('/animal/<animal_id>/edit', methods = ['GET', 'POST'])
@login_required
def animal_info_edit(animal_id):

    animal = get_animal_info(animal_id)
    if keeper_check(animal['shelter_id']) != True:
        flash('You have to be animal keeper to acces this page!')
        return redirect('/animal/{}'.format(animal_id))
    
    if request.method == 'POST':
        update_animal_info(animal_id)
        animal = get_animal_info(animal_id)

    return render_template('animal_info.html', user_status=get_user_status(animal['shelter_id']), animal=animal, pos_species=POS_SPECIES)


# Change animal status
@app.route('/animal/<animal_id>/status', methods = ['GET', 'POST'])
@login_required
def animal_status_update(animal_id):

    animal = get_animal_info(animal_id)
    if keeper_check(animal['shelter_id']) != True:
        flash('You have to be animal keeper to acces this page!')
        return redirect('/animal/{}'.format(animal_id))
    
    if request.method == 'POST':
        update_animal_status(animal_id)
        animal = get_animal_info(animal_id) 
    
    return render_template('animal_status.html', user_status=get_user_status(animal['shelter_id']), animal=animal)


# Add new vaccine
@app.route('/animal/<animal_id>/vaccinations', methods = ['GET', 'POST'])
@login_required
def animal_vaccination_update(animal_id):

    animal = get_animal_info(animal_id)
    if keeper_check(animal['shelter_id']) != True:
        flash('You have to be animal keeper to acces this page!')
        return redirect('/animal/{}'.format(animal_id))
    
    if request.method == 'POST':
        add_animal_vaccine(animal_id)

    return render_template('animal_vaccinations.html', user_status=get_user_status(animal['shelter_id']), animal=animal, vaccinations=get_animal_vaccinations(animal_id))


# Remove vaccine
@app.route('/animal/<animal_id>/vaccinations/delete/<vac_id>')
@login_required
def animal_vaccination_delete(animal_id, vac_id):

    animal = get_animal_info(animal_id)
    if keeper_check(animal['shelter_id']) != True:
        flash('You have to be animal keeper to do that!')
        return redirect('/animal/{}'.format(animal_id))
    else:
        if delete_animal_vaccine(vac_id):
            flash('Vaccine was successfully deleted!')
        else:
            flash('This vaccine does not exist!')
    
    return redirect ('/animal/{}/vaccinations'.format(animal_id))


# Saves animal in users saved
@app.route('/animal/<animal_id>/save')
@login_required
def user_animal_save(animal_id):

    save_user_animal(animal_id)

    return redirect('/animal/{}'.format(animal_id))


# Delete animal
@app.route('/animal/<animal_id>/delete', methods = ['POST'])
@login_required
def animal_delete(animal_id):

    if delete_animal(animal_id):
        return redirect('/')
    else:
        return redirect('/animal/{}'.format(animal_id))
    

# Animal schedule
@app.route('/animal/<animal_id>/schedule/')
def animal_schedule(animal_id):

    animal = get_animal_info(animal_id)

    return render_template('animal_schedule.html', user_status=get_user_status(animal['shelter_id']), animal=animal, schedule=get_animal_schedule(animal_id))
    

# Schedule an appointment day
@app.route('/animal/<animal_id>/schedule/day', methods = ['GET', 'POST'])
@login_required
def animal_schedule_day(animal_id):

    animal = get_animal_info(animal_id)

    if request.method == 'POST':
        return render_template('animal_schedule_time.html', user_status=get_user_status(animal['shelter_id']), animal=animal, shelter=get_shelter_info(animal['shelter_id']), pos_day=get_pos_day(), pos_hours=get_pos_hours(animal_id), walk=animal_walk_check(animal_id), day=request.form.get('app_day'), opening_hours=get_opening_hours(animal['shelter_id']))

    return render_template('animal_schedule_day.html', user_status=get_user_status(animal['shelter_id']), animal=animal, shelter=get_shelter_info(animal['shelter_id']), pos_day=get_pos_day(), opening_hours=get_opening_hours(animal['shelter_id']))


# Schedule an appointment time
@app.route('/animal/<animal_id>/schedule/time', methods = ['POST'])
@login_required
def animal_schedule_time(animal_id):

    if schedule_appointment(animal_id):
        return redirect('/animal/{}'.format(animal_id))
    else:
        return redirect('/animal/{}/schedule/day'.format(animal_id))


#################### SEARCH ####################


# Search animals
@app.route('/search/animals', methods = ['GET', 'POST'])
def search_animals():
    animals = get_animals_info(None)

    if request.method == 'POST':
        results = search_for_animals(None)
        if results:
            animals = results

    return render_template('search_animals.html', user_status=get_user_status(None), animals=animals)


# Search shelters
@app.route('/search/shelters', methods = ['GET', 'POST'])
def search_shelters():
    shelters = get_shelter_info(None)

    if request.method == 'POST':
        results = search_for_shelters()
        if results:
            shelters = results

    return render_template('search_shelters.html', user_status=get_user_status(None), shelters=shelters)

























# test route
@app.route('/test')
def test():

    


    return redirect('/')