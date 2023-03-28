from flask import Flask, render_template, request, redirect
import sqlite3

from helpers import check

# Configure application
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template("add.html")

    else:
        # Open database and creates a cursor
        con = sqlite3.connect("database.db")
        cur = con.cursor()

        # Put new animal into database
        cur.execute("INSERT INTO animals (shelter_id, name, species, description, image, urgency) VALUES (?, ?, ?, ?, ?, ?)", (
            1, # TO BE CHANGED IN THE FUTURE
            request.form.get("name"),
            request.form.get("species"),
            request.form.get("description"),
            request.form.get("image"),
            request.form.get("urgency")
        ))

        # Commit the changes and close database
        con.commit()
        con.close()


        return redirect("/")
    
    
    
@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    else:
        # Opens database and creates a cursor
        con = sqlite3.connect("database.db")
        cur = con.cursor()

        # Gets informations from form and checks it for faults

        # Check name
        name = request.form.get("name")
        if name.isalnum() == False:
            print("Unallowed characters in name")
            return redirect("/")
        
        if len(name) > 30:
            print("Name must contain less than 30 characters")
            return redirect("/") 
        
        cur.execute("SELECT name FROM shelters")
        names = cur.fetchall()
        x = isinstance(names[1], tuple)
        print(names)
        print(x)
        # if name in names.values():
        #     print("Username not available")
        #     return redirect("/")
        

        # Check email
        email = request.form.get("email")
        if check(email) == False:
            print("Invalid email")
            return redirect("/")
        
        # emails = cur.execute("SELECT con_email FROM shelters")
        # if email in emails.values():
        #     print("Email already taken")
        #     return redirect("/")


    print("Alls good")
    return render_template("register.html")