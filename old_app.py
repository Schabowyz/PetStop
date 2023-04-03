from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from datetime import timedelta
import os

from old_helpers import login_required, keeper_required, login_check, registration_check, register_user, login_user, shelter_check, get_shelter_info, get_keepers_info, insert_animal_info, get_shelter_animals, edit_shelter_information, create_new_shelter, remove_keeper, add_keeper, make_owner

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


@app.route("/")
def index():
    return render_template("index.html", login = login_check())


@app.route("/login", methods = ["GET", "POST"])
def login():

    # Clears all information that could be stored in session and set errors value to correct
    session.clear()
    errors = None

    # Route for form
    if request.method == "POST":

        # Checks users login and password and if theres no error, creates a session and redirects user to homepage
        username = request.form.get("username")
        errors = login_user(username, request.form.get("password"))
        if errors == None:
            session["user"] = username
            return redirect("/")

    return render_template("login.html", login = login_check(), errors = errors)


@app.route("/logout")
@login_required
def logout():
    
    # Clears session and redirects user to homepage
    session.clear()
    return redirect("/")


@app.route("/register", methods = ["GET", "POST"])
def register():

    # Sets errors to empty list
    errors = []

    # Route for form
    if request.method == "POST":

        # Gets information form form and checks if it's correct, if not creates errors list
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        errors = registration_check(username, email, password, request.form.get("conpassword"))

        # Creates a new user in database and returns to homepage if theres no error in errors list
        if not errors:
            register_user(username, email, password)
            return redirect("/")
        
    return render_template("register.html", login = login_check(), errors=errors)


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", login = login_check())


@app.route("/yourshelter")
def yourshelter():
    # Gets id of users shelter via shelter_check and redirects to it, if user doesn't have one, redirects to yourshelter
    shelter_id = shelter_check()
    if shelter_id == False:
        return render_template("yourshelter.html", login = login_check())
    else:
        return redirect("/shelter/{}".format(shelter_id))
        

@app.route("/shelter/<shelter_id>")
def shelter(shelter_id):
    
    # Gets shelter information in form of dictionary, if shelter doesnt exists, sets errors variable
    errors = None
    shelter_info = get_shelter_info(shelter_id)
    if shelter_info == None:
        errors = "Shelter does not exist"

    # Check if logged person is shelters keeper
    if shelter_check() == int(shelter_id):
        keeper = session["user"]
    else:
        keeper = None

    # Gets all animals that are currently in a shelter
    animals = get_shelter_animals(shelter_id)

    return render_template("shelter.html", login = login_check(), errors=errors, keeper = keeper, shelter_info = shelter_info, animals = animals)


@app.route("/createshelter", methods = ['GET', 'POST'])
@login_required
def create_shelter():
    errors = []
    if request.method == "POST":
        info = create_new_shelter()
        shelter_id = info[0]
        print(shelter_id)
        errors = info[1]
        print(errors)
        if shelter_id != False:
            return redirect("shelter/{}".format(shelter_id))
    return render_template("createshelter.html", login = login_check(), errors=errors)


### SHELTER INFORMATION EDIT ###
@app.route("/shelterinformation")
@login_required
@keeper_required
def shelter_information():
    # Gets id of users shelter via shelter_check and redirects to it, if user doesn't have one, redirects to yourshelter
    shelter_id = shelter_check()
    if shelter_id == False:
        return redirect("/")
    else:
        return redirect("/shelterinformation/{}".format(shelter_id))

@app.route("/shelterinformation/<shelter_id>", methods = ['GET', 'POST'])
@login_required
@keeper_required
def shelter_information_edit(shelter_id):
    errors = []
    shelter_info = get_shelter_info(shelter_id)
    keeper = session['user']
    db = {1: 'disabled'}

    if request.method == 'POST':
        info = edit_shelter_information(shelter_id)
        print(info)
        if info[0] == True:
            return redirect("/shelter/{}".format(shelter_id))
        else:
            errors = info[1]

    return render_template("shelterinformation.html", login = login_check(), keeper=keeper, shelter_info=shelter_info, db=db, errors=errors)


### SHELTER NEEDS EDIT ###
@app.route("/shelterneeds")
@login_required
@keeper_required
def shelter_needs():
    # Gets id of users shelter via shelter_check and redirects to it, if user doesn't have one, redirects to yourshelter
    shelter_id = shelter_check()
    if shelter_id == False:
        return redirect("/")
    else:
        return redirect("/shelterneeds/{}".format(shelter_id))
    
@app.route("/shelterneeds/<shelter_id>")
@login_required
@keeper_required
def shelter_needs_edit(shelter_id):
    shelter_info = get_shelter_info(shelter_id)
    keeper = session['user']
    db = {2: 'disabled'}

    return render_template("shelterneeds.html", login = login_check(), keeper=keeper, shelter_info=shelter_info, db=db)


### SHELTER EDIT KEEPERS ###
@app.route("/shelterkeepers")
@login_required
@keeper_required
def shelter_keepers():
    # Gets id of users shelter via shelter_check and redirects to it, if user doesn't have one, redirects to yourshelter
    shelter_id = shelter_check()
    if shelter_id == False:
        return redirect("/")
    else:
        return redirect("/shelterkeepers/{}".format(shelter_id))

@app.route("/shelterkeepers/<shelter_id>", methods = ['GET', 'POST'])
@login_required
@keeper_required
def shelter_keepers_edit(shelter_id):
    shelter_info = get_shelter_info(shelter_id)
    keeper = session['user']
    db = {3: 'disabled'}
    shelter_keepers = get_keepers_info(shelter_id)
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            flash("Please provide a username.")
            return redirect("/shelterkeepers")
        else:
            result = add_keeper(username, shelter_id)
        if result != None:
            flash(result)
            return redirect("/shelterkeepers")
        else:
            flash("{} was succesfully added as shelter keeper".format(username))
            return redirect("/shelterkeepers")
        
    return render_template("shelterkeepers.html", login = login_check(), keeper=keeper, shelter_info=shelter_info, db=db, shelter_keepers = shelter_keepers)

@app.route("/shelterkeepers/<shelter_id>/delete/<username>")
@login_required
@keeper_required
def shelter_keeper_delete(username, shelter_id):
    result = remove_keeper(username, shelter_id)
    flash(result)
    return redirect("/shelterkeepers")


@app.route("/shelterkeepers/<shelter_id>/owner/<username>")
@login_required
@keeper_required
def shelter_owner_make(username, shelter_id):
    result = make_owner(username, shelter_id)
    flash(result)
    return redirect("/shelterkeepers")


### SHELTER ADD AN ANIMAL ###
@app.route("/shelteranimal")
@login_required
@keeper_required
def shelter_animal():
    # Gets id of users shelter via shelter_check and redirects to it, if user doesn't have one, redirects to yourshelter
    shelter_id = shelter_check()
    if shelter_id == False:
        return redirect("/")
    else:
        return redirect("/shelteranimal/{}".format(shelter_id))

@app.route("/shelteranimal/<shelter_id>", methods = ['GET', 'POST'])
@login_required
@keeper_required
def shelter_add_animal(shelter_id):

    errors = None
    shelter_info = get_shelter_info(shelter_id)
    keeper = session['user']
    db = {4: 'disabled'}

    # When form is filled and executed, creates a new db entry
    if request.method == 'POST':
        errors = insert_animal_info(shelter_id)
        if not errors:
            return redirect("/shelter/{}".format(shelter_id))

    return render_template("shelteranimal.html", login = login_check(), keeper=keeper, shelter_info=shelter_info, db=db, errors=errors)





# @app.route("/registershelter", methods = ["GET", "POST"])
# def registershelter():
#     if request.method == "GET":
#         return render_template("registershelter.html")

#     else:
#         # Opens database and creates a cursor
#         con = sqlite3.connect("database.db")
#         cur = con.cursor()

#         # Gets informations from form and checks it for faults

#         # Check name
#         name = request.form.get("name")

#         if name.isalnum() == False:
#             print("Unallowed characters in name")
#             return redirect("/")
        
#         if len(name) > 30:
#             print("Name must contain less than 30 characters")
#             return redirect("/") 
        
#         cur.execute("SELECT name FROM shelters")
#         names = cur.fetchall()
#         names = [item for t in names for item in t]
#         if name in names:
#             print("Username not available")
#             return redirect("/")
        

#         # Check email
#         email = request.form.get("email")

#         if check_email(email) == False:
#             print("Invalid email")
#             return redirect("/")
        
#         cur.execute("SELECT con_email FROM shelters")
#         emails = cur.fetchall()
#         emails = [item for t in emails for item in t]
#         if email in emails:
#             print("Email already taken")
#             return redirect("/")
        

#         # Check password
#         password = request.form.get("password")
#         conpas = request.form.get("conpas")

#         if password != conpas:
#             print("Passwords don't match")
#             return redirect("/")
        
#         if len(password) < 8 or len(password) > 30:
#             print("Password must contain between 8 and 30 characters")
#             return redirect("/")
        

#         # Check city
#         city = request.form.get("city")

#         if city.isalpha() == False or not city:
#             print("Please provide right city name")
#             return redirect("/")
        

#         # Check adress
#         adress = request.form.get("adress")

#         if not adress:
#             print("Please provide the right adress")
#             return redirect("/")
        

#         # Check postal code
#         postal = request.form.get("postal")

#         if not postal:
#             print("Please provide the right postal code")
#             return redirect("/")
        

#         # Check number
#         phone = request.form.get("phone")

#         if not phone:
#             print("Please provide the right phone number")
#             return redirect("/")


#     print("Alls good")
#     return render_template("register.html")



# @app.route("/add", methods=["GET", "POST"])
# def add():
#     if request.method == "GET":
#         return render_template("add.html")

#     else:
#         # Open database and creates a cursor
#         con = sqlite3.connect("database.db")
#         cur = con.cursor()

#         # Put new animal into database
#         cur.execute("INSERT INTO animals (shelter_id, name, species, description, image, urgency) VALUES (?, ?, ?, ?, ?, ?)", (
#             1, # TO BE CHANGED IN THE FUTURE
#             request.form.get("name"),
#             request.form.get("species"),
#             request.form.get("description"),
#             request.form.get("image"),
#             request.form.get("urgency")
#         ))

#         # Commit the changes and close database
#         con.commit()
#         con.close()


#         return redirect("/")