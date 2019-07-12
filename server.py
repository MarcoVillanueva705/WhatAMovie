from flask import Flask, render_template, session, redirect, request, flash
from mysqlconnection import connectToMySQL
from flask_bootstrap import Bootstrap
from flask_bcrypt import Bcrypt
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
passwordRegex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$')
app = Flask(__name__)
bootstrap = Bootstrap(app)
bcrypt = Bcrypt(app)
app.secret_key = "keep it secret, keep it safe"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def incorrect():
    is_valid = True
    if len(request.form["first_name"]) < 1:
        is_valid = False
        flash("First Name can't be blank!")
        return redirect("/")
    elif any(char.isdigit() for char in request.form["first_name"]) == True:
        flash("Name can't have numbers!")
        return redirect("/")
    elif len(request.form["last_name"]) < 1:
        is_valid = False
        flash("Last Name can't be blank!")
        return redirect("/")
    elif any(char.isdigit() for char in request.form["last_name"]) == True:
         flash("Name can't have numbers!")
         return redirect("/")
    elif len(request.form["email"]) < 1:
        is_valid = False
        flash("Email can't be blank!")
        return redirect("/")
    elif not EMAIL_REGEX.match(request.form["email"]):    
        flash("Invalid email address!")
        return redirect("/") 
	
    else: 
        db = connectToMySQL("project")
        query = "SELECT * FROM users WHERE email = %(em)s;"
        data = {"em": request.form["email"]
        }
        result = db.query_db(query, data)
        print(result)
        if len(result) != 0:
            flash("Account already exists! Please use another email address.") 
            return redirect("/")
    
    if len(request.form["password"]) < 8:
        is_valid = False
        flash("Password can't be less than 8 characters!")
        return redirect("/")
    elif request.form["password"] != request.form["confirm_password"]:
        flash("Password and confirm password must be the same!")
        return redirect("/")
    else:
        pw_hash = bcrypt.generate_password_hash(request.form["password"])
        print(pw_hash)
        db  = connectToMySQL("project")
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(password_hash)s, NOW(), NOW());"
        data = {
            "fn": request.form["first_name"],
            "ln": request.form["last_name"],
            "em": request.form["email"],
            "password_hash": pw_hash,
        }
        result = db.query_db(query, data)
        session["user_id"] = result
        session["first_name"] = request.form["first_name"]
        flash("Account successfully created!") 
        return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    db = connectToMySQL("project")
    query = "SELECT * FROM users WHERE email = %(em)s"
    data = {
        "em": request.form["email"]
    }
    result = db.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0] ["password"], request.form["password"]):
            session["user_id"] = result[0] ["id"]
            session["first_name"] =  result[0] ["first_name"]
            return redirect("/movies")

@app.route("/movies")
def dashboard():
    if "user_id" not in session:
        flash("you need to be logged in to view this page!")
        return redirect("/")
    else:
        db = connectToMySQL("project")
        query = "SELECT * FROM users WHERE id = %(id)s;"
        data = {
        "id": session["user_id"]
    }
    users = db.query_db(query, data)
    db = connectToMySQL("project")
    query = "SELECT * FROM movie;"
    info = db.query_db(query)
    return render_template("home.html", users = users, info = info)

@app.route("/movie_new")
def add_a_movie():
    db = connectToMySQL("project")
    query = "SELECT * FROM users where id = %(id)s;"
    data = {
        "id": session["user_id"],
    }
    users = db.query_db(query, data)
    return render_template("movie_new.html", all_users = users)

@app.route("/new_movie", methods=["POST"])
def create():
    if len(request.form["title"]) < 1:
        flash("Title field must not be blank!")
        return redirect("/movie_new")
    if len(request.form["description"]) < 1:
        flash("Description field must not be blank!")
        return redirect("/movie_new")
    if len(request.form["year"]) < 1:
        flash("Year must not be blank!")
        return redirect("/movie_new")
    else:
        db = connectToMySQL("project")
        query = "INSERT INTO movie (users_id, title, description, year) VALUES (%(uid)s, %(t)s, %(d)s, %(y)s);"
        data = {
            "uid": session["user_id"],
            "t": request.form["title"],
            "d": request.form["description"],
            "y": request.form["year"],
        }
        db.query_db(query,data)
        flash("movie added!")
        return redirect("/movies")

@app.route("/edit/movie/<movie_id>")
def update(movie_id):
    db = connectToMySQL("project")
    query = "SELECT * FROM movie WHERE movie_id = %(id)s;"
    data = {"id": movie_id,
    }
    result = db.query_db(query, data)
    return render_template("edit_movie.html", movie = result)

@app.route("/movie/edit/<movie_id>", methods=["POST"])
def edit_movie(movie_id):
    db = connectToMySQL("project")    
    query = "UPDATE movie SET description = %(d)s WHERE movie_id = %(id)s;"
    data = {
        "d": request.form["description"],      
        "id": movie_id,
    }
    db.query_db(query, data)
    flash("Movie updated!")
    return redirect("/movies") 

@app.route("/discuss/<id>")
def forum(id):	                
    db = connectToMySQL("project")
    query = "SELECT comments.id, comments.discuss, comments.rating, comments.movie_id, users.first_name FROM comments JOIN users ON users.id = comments.users_id WHERE comments.movie_id = %(cd)s;"
    #query = "SELECT * FROM comments WHERE movie_id = %(id)s;"
    data = {
        #"id": id,
        "cd": id,
    }
    comments = db.query_db(query, data)
    db = connectToMySQL("project")
    query =  "SELECT * FROM movie WHERE movie_id = %(md)s;"
    data = {
        "md": id,
    }
    results = db.query_db(query, data)
    db = connectToMySQL("project")
    query =  "SELECT AVG (rating) FROM comments WHERE movie_id = %(md)s;"
    data = {
        "md": id,
    }
    numbers = db.query_db(query, data)       
    return render_template("forum.html", discussion = results, comments = comments, numbers = numbers) #movie = movie)

@app.route("/add_discussion/<movie_id>", methods = ["POST"])
def discussion(movie_id):
    print("**********************")
    print(request.form)
    print("**********************")
    db = connectToMySQL("project")
    query = "INSERT into comments (users_id, discuss, rating, movie_id) VALUES (%(uid)s, %(d)s, %(r)s, %(id)s);"
    data = {
        "uid": session["user_id"],
        "d": request.form["discuss"],
        "r": request.form["rating"],
        "id": movie_id,
    }
    db.query_db(query, data)
    flash("Thanks for adding to the discussion!") 
    print("/discuss/"+ str (movie_id))      
    return redirect("/discuss/"+ str (movie_id))


@app.route("/logout")
def logout():
    print(session)
    session.clear()
    flash("You have been logged out!")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug = True)