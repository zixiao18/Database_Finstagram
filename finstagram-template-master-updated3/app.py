from __future__ import print_function # In python 2.7

from flask import Flask, render_template, request, session, redirect, url_for, send_file
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time
import sys


app = Flask(__name__)
app.secret_key = "super secret key"
IMAGES_DIR = os.path.join(os.getcwd(), "static")

connection = pymysql.connect(host="localhost",
                             user="root",
                             password="root",
                             db="finstagram",
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
    query = "SELECT * FROM photo JOIN person ON photo.photoPoster = person.username WHERE ((photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s AND followstatus = 1) OR photoPoster = %s) AND allFollowers = 1) OR (allFollowers = 0 AND photoPoster IN (SELECT owner_username FROM BelongTo WHERE member_username = %s)) ORDER BY postingDate DESC"

    with connection.cursor() as cursor:
#        cursor.execute(query)
        cursor.execute(query, (username, username, username))
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
        
        # commented
        query = "SELECT username, comment FROM comments WHERE photoID = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, photoID)
        commented_list = cursor.fetchall()
        to_join = ''
        for i in commented_list:
            to_join += i['username'] + ': ' + str(i['comment']) + ', '
        data[j]['commented'] = to_join

    return render_template("images.html", images=data)

@app.route("/images_highest_ratings", methods=["GET"])
@login_required
def highest_images():
    username = session['username']
    query = "SELECT filepath, photoID, caption, photoPoster, firstName, lastName, AVG(rating) \
    FROM (photo JOIN person ON photo.photoPoster = person.username) JOIN Likes USING (photoID) \
    WHERE ((photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s AND followstatus = 1) \
                    OR photoPoster = %s) AND allFollowers = 1) OR \
            (allFollowers = 0 AND photoPoster IN \
                             (SELECT owner_username FROM BelongTo WHERE member_username = %s)) \
    GROUP BY filepath, photoID, caption, photoPoster, firstName, lastName\
    ORDER BY AVG(rating) DESC"
        
    with connection.cursor() as cursor:
#        cursor.execute(query)
        cursor.execute(query, (username, username, username))
    data = cursor.fetchall()
    
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
        
        # commented
        query = "SELECT username, comment FROM comments WHERE photoID = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, photoID)
        commented_list = cursor.fetchall()
        to_join = ''
        for i in commented_list:
            to_join += i['username'] + ': ' + str(i['comment']) + ', '
        data[j]['commented'] = to_join

    return render_template("images_highest_ratings.html", images=data)

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

@app.route("/unfollow", methods=["GET"])
def unfollow():
    return render_template("unfollow.html")

@app.route("/friend", methods=["GET"])
def friend():
    return render_template("friend.html")

@app.route("/friend_groups", methods=["GET"])
def friend_groups():
    username = session['username']
    query = "SELECT groupName, description FROM Friendgroup WHERE groupOwner = %s "
    with connection.cursor() as cursor:
        cursor.execute(query, (username))
    data = cursor.fetchall()
    
    return render_template("friend_groups.html", friend_groups=data)

@app.route("/add_friend", methods=["GET",'POST'])

def add_friend():
    username = session['username']
    requestData = request.form
    groupname = requestData['request_group']
    query = "SELECT member_username FROM BelongTo WHERE groupname = %s AND member_username != %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (groupname, username))
    data = cursor.fetchall()
    
    return render_template("add_friend.html", friends=data, groupname=groupname)

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
        tagstatus = 1
        
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
                # generate a photo ID
                cursor.execute("SELECT MAX(photoID) FROM photo")
                photoID = cursor.fetchall()[0]['MAX(photoID)']
                if not photoID:
                    photoID = 1
                    
                # execute 
                for tagged_name in tag_person.split():
                    cursor.execute(query2, (tagged_name, photoID, tagstatus))
            
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

        if not result:
            return render_template('follow.html', error="Username you entered doesn't exist")    
        
        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, %s)"
                followstatus = 0
                cursor.execute(query, (username_followed, username_follower, followstatus))
                
        except pymysql.err.IntegrityError:
            error = "You have already followed %s." % (username_followed)
            return render_template('follow.html', error=error)    

        return render_template("follow.html", message="request sent to %s successfully" %username_followed)

    error = "An error has occurred. Please try again."
    return render_template("follow.html", error=error)

@app.route("/view_follow_status", methods=['POST','GET'])
@login_required
def view_follow_status():
    username = session['username']                
    query = "SELECT * FROM follow WHERE username_followed = %s AND followstatus = 0"

    with connection.cursor() as cursor:
        cursor.execute(query, (username))
    data = cursor.fetchall()

    return render_template("view_follow_status.html", follow_lists=data)

@app.route("/reject_follow", methods=['POST','GET'])
@login_required
def reject_follow():
    if 1:
        requestData = request.form
        username = session['username']
        # print(str(requestData), file=sys.stderr)
        to_reject = requestData["username_follower"]

        with connection.cursor() as cursor:
            query = "DELETE FROM Follow WHERE Follow.username_followed = %s AND Follow.username_follower = %s"
            cursor.execute(query, (username, to_reject))
        return render_template("view_follow_status.html", message="request rejected successfully.")
    
    else:
        error = "An error has occurred. Please try again."
        return render_template("images.html", error=error)

@app.route("/accept_follow", methods=['POST','GET'])
@login_required
def accept_follow():
    if 1:
        requestData = request.form
        username = session['username']
        to_accept = requestData["username_follower"]

        with connection.cursor() as cursor:
            query = "UPDATE Follow SET followstatus = 1 WHERE Follow.username_followed = %s AND Follow.username_follower = %s"
            cursor.execute(query, (username, to_accept))
        return render_template("view_follow_status.html", message="request accepted successfully.")
    
    else:
        error = "An error has occurred. Please try again."
        return render_template("images.html", error=error)

@app.route("/unfollowSomeone", methods=["POST"])
@login_required
def unfollowSomeone():

    if request.form:
        requestData = request.form
        username_unfollowed = requestData["unfollowed"]
        username_follower = session['username']
#        followstatus = 1
        
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM Person WHERE username = %s", username_unfollowed)
        result = cursor.fetchall() # need to see the result
#        print(result)
        if not result:
            return render_template('unfollow.html', error="Username you entered doesn't exist")  
        
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM Follow WHERE username_followed = %s AND username_follower = %s AND followstatus = 1", (username_unfollowed, username_follower))
        result = cursor.fetchall() # need to see the result
#        print(result)
        if not result:
            return render_template('unfollow.html', error="You never followed user: " + username_unfollowed) 
        
        try:
            with connection.cursor() as cursor:
#                query = "INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, %s)"
                query = "DELETE FROM Follow WHERE username_followed = %s AND username_follower = %s"

                cursor.execute(query, (username_unfollowed, username_follower))
                
        except pymysql.err.IntegrityError:
            error = "Deletion goes wrong"
            return render_template('unfollow.html', error=error)    

        return render_template("unfollow.html", message="Unfollowed %s successfuly" %username_unfollowed)

    error = "An error has occurred. Please try again."
    return render_template("unfollow.html", error=error)

#import pdb; pdb.set_trace()

@app.route("/likes", methods=["POST"])
@login_required
def likes():
    if request.form:
        requestData = request.form
        username = session['username']
        photoID = requestData["photoID"]
        rating = requestData["rating"]
        
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


@app.route("/comments", methods=["POST"])
@login_required
def comments():
    
    if request.form:
        requestData = request.form
        username = session['username']
        photoID = requestData["photoID"]
        comment = requestData["commenting"]
        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO Comments (username, photoID, commenttime, comment) VALUES (%s, %s, %s, %s)"

                cursor.execute(query, (username, photoID, time.strftime('%Y-%m-%d %H:%M:%S'), comment))
                
        except pymysql.err.IntegrityError:
            error = "You have already commented post %s." % (photoID)
            return render_template('images.html', error=error)    

        return redirect(url_for("images"))

    error = "An error has occurred. Please try again."
    return render_template("images.html", error=error)

@app.route("/images_poster", methods=['POST','GET'])
@login_required
def images_poster():
    if 1:
        requestData = request.form
        query_name = requestData["images_poster"]
        username = session['username']
        query = "SELECT * FROM photo JOIN person ON photo.photoPoster = person.username WHERE photoPoster = %s AND ((photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s AND followstatus = 1) OR photoPoster = %s) AND allFollowers = 1) OR (allFollowers = 0 AND photoPoster IN (SELECT owner_username FROM BelongTo WHERE member_username = %s)) ORDER BY postingDate DESC"
        with connection.cursor() as cursor:
            cursor.execute(query, (query_name, username, username, username))
        data = cursor.fetchall()
        
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
            
            # commented
            query = "SELECT username, comment FROM comments WHERE photoID = %s"
            with connection.cursor() as cursor:
                cursor.execute(query, photoID)
            commented_list = cursor.fetchall()
            to_join = ''
            for i in commented_list:
                to_join += i['username'] + ': ' + str(i['comment']) + ', '
            data[j]['commented'] = to_join
    
        return render_template("images_poster.html", images=data, query_name=query_name)
    
    else:
        error = "An error has occurred. Please try again."
        return render_template("images_poster.html", error=error)

@app.route("/images_tag", methods=['POST','GET'])
@login_required
def images_tag():
    if request.form:
        requestData = request.form
        query_name = requestData["images_tag"]
    username = session['username']
    query = "SELECT * FROM (photo JOIN person ON photo.photoPoster = person.username) \
    JOIN Tagged USING(photoID) \
    WHERE Tagged.username = %s AND ((photoPoster IN (SELECT username_followed FROM Follow \
    WHERE username_follower = %s AND followstatus = 1) OR photoPoster = %s) AND allFollowers = 1) OR \
    (allFollowers = 0 AND photoPoster IN (SELECT owner_username FROM BelongTo \
    WHERE member_username = %s)) ORDER BY postingDate DESC"
    
    with connection.cursor() as cursor:
#        cursor.execute(query)
        cursor.execute(query, (query_name, username, username, username))
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
        
        # commented
        query = "SELECT username, comment FROM comments WHERE photoID = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, photoID)
        commented_list = cursor.fetchall()
        to_join = ''
        for i in commented_list:
            to_join += i['username'] + ': ' + str(i['comment']) + ', '
        data[j]['commented'] = to_join

    return render_template("images_tag.html", images=data, query_name=query_name)

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
    if not os.path.isdir("static"):
        os.mkdir(IMAGES_DIR)
    app.run()
    
  #  app.run('127.0.0.1', 5000, debug = True)
