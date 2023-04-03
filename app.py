from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from datetime import timedelta
from f_helpers import login_required, logout_required, get_user_status, login_user, register_user, check_user_shelter


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
        print('NIEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
        return render_template('shelter_yourshelter.html', user_status=get_user_status(None))
    else:
        return redirect('/shelter/<shelter_id>')