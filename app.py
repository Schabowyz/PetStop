from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from datetime import timedelta

from f_helpers import login_required, logout_required, get_user_status, login_user, register_user, get_shelter_info, get_animals_info, add_shelter, edit_shelter_info, get_keepers, delete_keeper, add_keeper, add_owner, add_animal, get_animal_info
from f_checks import keeper_check, owner_check, check_user_shelter


# Configure application
app = Flask(__name__)

# Configure app backed server session
app.config['SESSION_PERMAMENT'] = True
app.config['PERMAMENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SECRET_KEY'] = 'key'
app.config['SESSION_TYPE'] = 'filesystem'

# Configure uploads settings
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png']
app.config['ANIMAL_IMAGES'] = 'static/animal_images'

Session(app)




############################################# ROUTES #############################################


# Index page
@app.route('/')
def index():

    return render_template('index.html', user_status=get_user_status(None))



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

    return render_template("user_profile.html", user_status=get_user_status(None), username=session['user'])


# User's shelter page
@app.route('/yourshelter')
@login_required
def shelter_yourshelter():

    shelter_id = check_user_shelter()

    if not shelter_id:
        return render_template('shelter_yourshelter.html', user_status=get_user_status(None))
    else:
        return redirect('/shelter/{}'.format(shelter_id))
    

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


# AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA                     ZROBIĆ REDIRECT NA 404 SHELTER NOT FOUND
# Shelter page
@app.route('/shelter/<shelter_id>')
def shelter_main(shelter_id):

    shelter = get_shelter_info(shelter_id)
    if not shelter:
        return redirect('/')
    
    animals = get_animals_info(shelter_id)

    return render_template('shelter_main.html', user_status=get_user_status(shelter_id), shelter=shelter, animals=animals, db={})


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

    return render_template('shelter_info.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), db={'info': 'disabled'})


# Edit needs
@app.route('/shelter/<shelter_id>/needs')
@login_required
def shelter_edit_needs(shelter_id):

    if not keeper_check(shelter_id):
        flash('You have to be shelter keeper to acces this page!')
        return redirect('/shelter/{}'.format(shelter_id))
    
    return render_template('shelter_needs.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), db={'needs': 'disabled'})


# Edit keepers
@app.route('/shelter/<shelter_id>/keepers', methods = ['GET', 'POST'])
@login_required
def eshelter_edit_keepers(shelter_id):

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
    
    if request.method == 'POST':
        if add_animal(shelter_id):
            flash('Animal was succesfully added to shelter!')
            return redirect('/shelter/{}'.format(shelter_id))
        
    return render_template('shelter_animal.html', user_status=get_user_status(shelter_id), shelter=get_shelter_info(shelter_id), keepers=get_keepers(shelter_id), db={'animal': 'disabled'})



#################### SEARCH ####################


# Search animals
@app.route('/search/animals')
def search_animals():

    return render_template('search_animals.html', user_status=get_user_status(None), animals=get_animals_info(None))


# Search shelters
@app.route('/search/shelters')
def search_shelters():

    return render_template('search_shelters.html', user_status=get_user_status(None), shelters=get_shelter_info(None))



#################### ANIMAL ####################


# AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA                     ZROBIĆ REDIRECT NA 404 ANIAL NOT FOUND
@app.route('/animal/<animal_id>')
def animal_main(animal_id):

    animal = get_animal_info(animal_id)
    if not animal:
        return redirect('/')
    
    return render_template('animal_main.html', user_status=get_user_status(animal['shelter_id']), animal=animal, shelter=get_shelter_info(animal['shelter_id']))


# Edit animal info
@app.route('/animal/<animal_id>/edit')
@login_required
def animal_info_edit(animal_id):

    animal = get_animal_info(animal_id)

    return render_template('animal_info.html', user_status=get_user_status(animal['shelter_id']), animal=animal)