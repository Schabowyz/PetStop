from flask import Flask, render_template, request, redirect
import sqlite3

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
        # Open database and create cursor
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
