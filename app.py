from flask import Flask, render_template, request, session, redirect, url_for, send_file
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time

app = Flask(__name__)
app.secret_key = "super secret key"
IMAGES_DIR = os.path.join(os.getcwd(), "images")

connection = pymysql.connect(host="localhost",
                             user="root",
                             password="root",
                             db="FinalProjectDB",
                             charset="utf8mb4",
                             port=8889,
                             cursorclass=pymysql.cursors.DictCursor,
                             autocommit=True)

def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html", username=session["username"])

@app.route("/upload", methods=["GET"])
@login_required
def upload():
    return render_template("upload.html")

@app.route("/images", methods=["GET"])
@login_required
def images():
    username = session['username']
#    query = "SELECT * FROM photo"
#    query = "SELECT * FROM photo WHERE photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s) OR photoPoster = %s ORDER BY photoID DESC"---------------
   query = "SELECT * FROM photo JOIN person ON photo.photoPoster = person.username WHERE photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s) OR photoPoster = %s ORDER BY photoID DESC"
    # query = "SELECT * FROM photo JOIN person ON photo.photoPoster = person.username WHERE ((photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s) OR photoPoster = %s) AND allFollowers = 1) OR (allFollowers = 0 AND photoPoster IN (SELECT member_username FROM BelongTo WHERE owner_username = %s)) ORDER BY photoID DESC"

    with connection.cursor() as cursor:
#        cursor.execute(query)
        cursor.execute(query, (username, username))
    data = cursor.fetchall()
#    print(data)

    for j in range(len(data)):
        photoID = data[j]['photoID']

        # tagged
        query = "SELECT username, firstName, lastName FROM tagged NATURAL JOIN person WHERE photoID = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, photoID)
        tagged_list = cursor.fetchall()
        to_join = ''
        for i in tagged_list:
            to_join += i['username'] + ': ' + i['firstName'] + ' ' + i['lastName'] + ', '
        data[j]['tagged'] = to_join

        # liked
        query = "SELECT username, rating FROM likes WHERE photoID = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, photoID)
        liked_list = cursor.fetchall()
        to_join = ''
        for i in liked_list:
            to_join += i['username'] + ': ' + str(i['rating']) + ', '
        data[j]['liked'] = to_join


    return render_template("images.html", images=data)

@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/follow", methods=["GET"])
def follow():
    return render_template("follow.html")

@app.route("/friend", methods=["GET"])
def friend():
    return render_template("friend.html")

@app.route("/loginAuth", methods=["POST"])
def loginAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"]
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()

        with connection.cursor() as cursor:
            query = "SELECT * FROM person WHERE username = %s AND password = %s"
            cursor.execute(query, (username, hashedPassword))
        data = cursor.fetchone()
        if data:
            session["username"] = username
            return redirect(url_for("home"))

        error = "Incorrect username or password."
        return render_template("login.html", error=error)

    error = "An unknown error has occurred. Please try again."
    return render_template("login.html", error=error)

@app.route("/registerAuth", methods=["POST"])
def registerAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"]
        hashedPassword = hashlib.sha256(plaintextPasword.encode("utf-8")).hexdigest()
        firstName = requestData["fname"]
        lastName = requestData["lname"]

        bio = "tempory biograph, havent implemented"
        bio = requestData["bio"]

        try:
            with connection.cursor() as cursor:
#                query = "INSERT INTO person (username, password, fname, lname) VALUES (%s, %s, %s, %s)"
                query = "INSERT INTO person (username, password, firstName, lastName, bio) VALUES (%s, %s, %s, %s, %s)"

#                cursor.execute(query, (username, hashedPassword, firstName, lastName))
                cursor.execute(query, (username, hashedPassword, firstName, lastName, bio))

        except pymysql.err.IntegrityError:
            error = "%s is already taken." % (username)
            return render_template('register.html', error=error)

        return redirect(url_for("login"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)

@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username")
    return redirect("/")

@app.route("/uploadImage", methods=["POST"])
@login_required
def upload_image():
    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename

        if request.form:
            requestData = request.form
            allFollowers = requestData["allFollowers"]
            caption = requestData["caption"]

            tag_person = requestData["tag_person"]
            photoID = 0 # to be define later
            tagstatus = 1

#            allFollowers = 1
#            caption = 'The caption, to be implemented'


        photoPoster = session['username']

        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)

        query = "INSERT INTO photo (postingdate, filepath, allFollowers, caption, photoPoster) VALUES (%s, %s, %s, %s, %s)"

        query2 = "INSERT INTO Tagged (username, photoID, tagstatus) VALUES (%s, %s, %s)"

        with connection.cursor() as cursor:

            cursor.execute(query, (time.strftime('%Y-%m-%d %H:%M:%S'), image_name, allFollowers, caption, photoPoster))

            if tag_person:
                cursor.execute("SELECT MAX(photoID) FROM photo")
                photoID = cursor.fetchall()[0]['MAX(photoID)']

                if not photoID:
                    photoID = 1

                for name in tag_person.split():
                    cursor.execute(query2, (name, photoID, tagstatus))



        message = "Image has been successfully uploaded."


        return render_template("upload.html", message=message)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)

@app.route("/followSomeone", methods=["POST"])
@login_required
def followSomeone():

    if request.form:
        requestData = request.form
        username_followed = requestData["followed"]
        username_follower = session['username']
        followstatus = 1

        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM Person WHERE username = %s", username_followed)

        result = cursor.fetchall() # need to see the result
        print(result)
        if not result:
            return render_template('follow.html', error="Username you entered doesn't exist")


        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, %s)"

                cursor.execute(query, (username_followed, username_follower, followstatus))

        except pymysql.err.IntegrityError:
            error = "You have already followed %s." % (username_followed)
            return render_template('follow.html', error=error)

        return redirect(url_for("follow"))

    error = "An error has occurred. Please try again."
    return render_template("follow.html", error=error)

#import pdb; pdb.set_trace()

@app.route("/likes", methods=["POST"])
@login_required
def likes():

    if request.form:
        requestData = request.form
        username = session['username']
        photoID = requestData["photoID"]
        rating = requestData["rating"]
#        photoID = 2
#        rating = 9
#        request.form.get("something", False)

        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO Likes (username, photoID, liketime, rating) VALUES (%s, %s, %s, %s)"

                cursor.execute(query, (username, photoID, time.strftime('%Y-%m-%d %H:%M:%S'), rating))

        except pymysql.err.IntegrityError:
            error = "You have already liked post %s." % (photoID)
            return render_template('images.html', error=error)

        return redirect(url_for("images"))

    error = "An error has occurred. Please try again."
    return render_template("images.html", error=error)

@app.route("/builfFriendGroup", methods=["POST"])
@login_required
def builfFriendGroup():

    if request.form:
        requestData = request.form
        username = session['username']
        group_name = requestData["group"]
        friends = requestData["friends"]

        description = requestData['desciption']

        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM Friendgroup WHERE groupOwner = %s AND groupName = %s", (username, group_name))

        result = cursor.fetchall() # need to see the result
        if result:
            return render_template('friend.html', error="groupName already exists")

        query = "INSERT INTO Friendgroup (groupOwner, groupName, description) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, group_name, description))

        for friend in friends.split():
#            try:
            with connection.cursor() as cursor:
                query = "INSERT INTO BelongTo (member_username, owner_username, groupName) VALUES (%s, %s, %s)"

                cursor.execute(query, (friend, username, group_name))

        with connection.cursor() as cursor:
                query = "INSERT INTO BelongTo (member_username, owner_username, groupName) VALUES (%s, %s, %s)"
                cursor.execute(query, (username, username, group_name))

#            except pymysql.err.IntegrityError:
#                error = "You have already created %s." % (username_followed)
#                return render_template('follow.html', error=error)

#        return redirect(url_for("friend"))
        return render_template("friend.html", error="Successfully build!")

    error = "An error has occurred. Please try again."
    return render_template("friend.html", error=error)

if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run()
