import datetime
import json
import os
import secrets
import time
from flask import abort, jsonify, render_template, request, redirect, send_file, session, Blueprint, url_for
from flask_socketio import SocketIO
import requests
from bs4 import BeautifulSoup
import urllib3
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from geopy.geocoders import Nominatim
from threading import Thread
from tgtg import TgtgClient


from pythonHelper import SQLHelper, MailHelper, TemplateHelper
from config import templates_path, openrouteservice_api_key, gruettedrive_path, gmail_mail, mindee_api_key, nelly_auth_key, recaptcha_secret_key, secret_key

    
tool_route = Blueprint("Tools", "Tools", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()

@tool_route.route("/logout")
def logout():
    """ Logout route

    Returns:
        str: Redirect to home page
    """    
    session.pop("user_id", None)
    session.clear()
    return redirect("/")

def create_ticket(username, message, email):
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"INSERT INTO tickets (name, username, email, message, status) VALUES ('{username}', '{username}', '{email}', '{message}', 'opened')")
        
@tool_route.route("/unsubscribe", methods=["GET", "POST"])
def unsubscribe():
    """ Route to unsubscribe from communication emails	

    Returns:
        HTML: Rendered HTML page
    """    
    if request.args.get("username") == None or request.args.get("email") == None or request.args.get("token") == None:
        if request.method == "GET":
            return render_template("unsubscribe.html", menu=th.user(session), mode="unsubscribe_input")
        else:
            sql = SQLHelper.SQLHelper()
            if "email" not in request.form or request.form["email"] == "":
                return redirect("/unsubscribe")
            email = str(request.form["email"])
            sql.writeSQL(f"UPDATE users SET receive_emails = {False} WHERE email = '{email}'")
            t1 = Thread(target=create_ticket, args=("unknown", f"Someone unsubscribed from communication emails. Email: {email}", email)).start()
            return render_template("unsubscribe.html", menu=th.user(session), mode="unsubscribe_confirmed")

    username = request.args.get("username")
    email = request.args.get("email")
    token = request.args.get("token")
    confirmed = request.args.get("confirmed")
    
    if confirmed != "true":
        return render_template("unsubscribe.html", menu=th.user(session), username=username, email=email, token=token, mode="unsubscribe")
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{username}'")

    if user == []:
        return redirect("/")
    elif user[0]["email"] != email or user[0]["verification_code"] != token:
        return redirect("/")
    else:
        user = sql.readSQL(f"SELECT * FROM users WHERE username = '{username}'")
        if user[0]["receive_emails"] == False:
            return redirect("/")

        sql.writeSQL(f"UPDATE users SET receive_emails = {False} WHERE username = '{username}'")
        t2 = Thread(target=MailHelper.MailHelper().send_support_mail, args=("Unsubscribed", username, email, f"{username} unsubscribed from communication emails. Reason: {request.form['reason']}")).start()
        t3 = Thread(target=create_ticket, args=(username, f"{username} unsubscribed from communication emails. Reason: {request.form['reason']}", email)).start()
        
        return render_template("unsubscribe.html", menu=th.user(session), username=username, email=email, token=token, mode="unsubscribe_confirmed")
    
@tool_route.route("/resubscribe")
def resubscribe():
    """ Route to resubscribe to communication emails

    Returns:
        HTML: Rendered HTML page
    """

    username = request.args.get("username")
    email = request.args.get("email")
    token = request.args.get("token")
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM users WHERE username = '{username}'")
    
    if user == []:
        return redirect("/")
    elif user[0]["email"] != email or user[0]["verification_code"] != token:
        return redirect("/")
    else:
        sql.writeSQL(f"UPDATE users SET receive_emails = {True} WHERE username = '{username}'")
        t1 = Thread(target=create_ticket, args=(username, f"{username} changed their mind and resubscribed to communication emails. Please manually gift them GrütteCloud PLUS", email)).start()
        return render_template("unsubscribe.html", menu=th.user(session), username=username, email=email, token=token, mode="resubscribe")
    
@tool_route.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    """ Route to reset a user's password using a token sent to their email

    Returns:
        HTML: Rendered HTML page
    """    
    if request.method == "GET":
        if request.args.get("token") == None:
            return render_template("reset_password.html", menu=th.user(session), action="default")
        else:
            sql = SQLHelper.SQLHelper()
            token = str(request.args.get("token"))
            
            token_db = sql.readSQL(f"SELECT * FROM password_resets WHERE token = '{token}'")
            if token_db == []:
                return redirect("/reset_password")
            
            # check if token is less than 15 minutes old
            token_time = token_db[0]["created_at"]
            time_now = datetime.datetime.now()
            time_difference = time_now - token_time
            if time_difference.seconds > 900:
                return redirect("/reset_password")
            
            # Check if token has already been used
            if bool(token_db[0]["is_used"]):
                return redirect("/reset_password")
            
            return render_template("reset_password.html", menu=th.user(session), action="create_new", token=token)
        
    else:
        if request.args.get("token") == None:
            email = str(request.form["email"])
            username = str(request.form["username"]).lower()
            mail = MailHelper.MailHelper()
            sql = SQLHelper.SQLHelper()
            
            user = sql.readSQL(f"SELECT * FROM users WHERE username = '{username}' AND email = '{email}'")
            if user == []:
                return render_template("reset_password.html", menu=th.user(session), action="email_sent", email=email)
            
            else:
                generate_token = secrets.token_hex(15)
                
                user_id = user[0]["id"]
                
                sql.writeSQL(f"INSERT INTO password_resets (user_id, token) VALUES ('{user_id}', '{generate_token}')")
                
                text = f"""
                    You have requested to reset your password.<br>
                    You can do so by clicking on the following link:<br>
                    <h2 style="color: #0A84FF;">
                        <a style="color: #0A84FF; text-decoration: none;" href="https://www.gruettecloud.com/reset_password?token={generate_token}">Reset password</a>
                    </h2>
                    or by pasting the following link into your browser:<br>
                    https://www.gruettecloud.com/reset_password?token={generate_token}<br>
                    this link will expire in 15 minutes.<br><br>
                """
                
                mail.send_email(email, username, "Reset your password", text)
                
            return render_template("reset_password.html", menu=th.user(session), action="email_sent", email=email)
        
        else:
            token = str(request.args.get("token"))
            password = str(request.form["password"])
            password_confirm = str(request.form["password_confirm"])
            
            if password != password_confirm:
                return redirect(f"/reset_password?token={token}")
            
            sql = SQLHelper.SQLHelper()
            token_db = sql.readSQL(f"SELECT * FROM password_resets WHERE token = '{token}'")
            if token_db == []:
                return redirect("/reset_password")
            
            # check if token is less than 15 minutes old
            token_time = token_db[0]["created_at"]
            time_now = datetime.datetime.now()
            time_difference = time_now - token_time
            if time_difference.seconds > 900:
                return redirect("/reset_password")
            
            # Check if token has already been used
            if bool(token_db[0]["is_used"]):
                return redirect("/reset_password")
            
            user_id = token_db[0]["user_id"]
            sql.writeSQL(f"UPDATE users SET password = '{generate_password_hash(password)}', is_2fa_enabled = {False} WHERE id = '{user_id}'")
            sql.writeSQL(f"UPDATE password_resets SET is_used = {True} WHERE user_id = '{user_id}'")
            
            return render_template("reset_password.html", menu=th.user(session), action="password_reset")
        
@tool_route.route("/help", methods=["GET"])
def help():
    return render_template("help.html", menu=th.user(session))
        
@tool_route.route("/about", methods=["GET"])
def about():
    sql = SQLHelper.SQLHelper()
    pfp_jan = sql.readSQL("SELECT profile_picture FROM users WHERE username = 'jan'")[0]["profile_picture"]
    return render_template("about.html", menu=th.user(session), pfp_jan=pfp_jan)

@tool_route.route("/discover", methods=["GET"])
def discover():
    error = request.args.get("error")
    if error == "username_or_password_empty": error = "Please enter your username and password."
    elif error == "invalid_credentials": error = "Invalid username or password."
    elif error == "passwords_not_matching": error = "Passwords do not match."
    elif error == "forbidden_characters": error = "Your username contains forbidden characters."
    elif error == "username_less_40": error = "Your username must be less than 40 characters."
    elif error == "forbidden_words": error = "Your username contains forbidden words."
    elif error == "password_between_8_40": error = "Your password must be between 8 and 40 characters."
    elif error == "invalid_email": error = "Please enter a valid email address."
    elif error == "username_already_exists": error = "This username is already taken."

    return render_template("discover.html", menu=th.user(session), error=error, traceback=request.args.get("traceback"))

@tool_route.route("/privacy", methods=["GET"])
def privacy():
    return render_template("privacy.html", menu=th.user(session))

@tool_route.route("/terms", methods=["GET"])
def terms():
    return render_template("terms.html", menu=th.user(session))

@tool_route.route("/support", methods=["GET", "POST"])
def send_support():
    """ POST route to send a support message to the GrütteCloud team

    Returns:
        HTML: Rendered HTML page
    """

    if request.method == "GET":
        return render_template("support.html", menu=th.user(session))
    
    sql = SQLHelper.SQLHelper()
    
    name = str(request.form["name"])
    username = str(request.form["username"])
    email = str(request.form["mail"])
    message = str(request.form["message"])
    
    # Check if reCAPTCHA response is valid
    recaptcha_response = request.form.get('g-recaptcha-response')
    
    # Verify the reCAPTCHA response with Google's API
    data = {
        'secret': recaptcha_secret_key,
        'response': recaptcha_response
    }
    
     # Make a POST request to Google reCAPTCHA API
    verify_response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result = verify_response.json()

    # Check if reCAPTCHA score is above the threshold
    if result['success'] and result['score'] >= 0.5:
        sql.writeSQL(f"INSERT INTO tickets (name, username, email, message, status) VALUES ('{name}', '{username}', '{email}', '{message}', 'opened')")
    
        async_mail = Thread(target=MailHelper.MailHelper().send_support_mail, args=(name, username, email, message))
        async_mail.start()
        
        if request.args.get("api") == "true":
            return jsonify({"success": True})
        
        return render_template("support.html", menu=th.user(session), error="success")
    
    else:
        return render_template("support.html", menu=th.user(session), error="recaptcha_failed")

# API Endpoints for GrütteMaps
@tool_route.route("/search_place", methods=["GET"])
def search_place():
    if request.args.get("query") == None or request.args.get("query") == "":
        abort(400)
    
    locations = []
    geolocator = Nominatim(user_agent="https://www.gruettecloud.com/maps")
    
    results = geolocator.geocode(request.args.get("query"), exactly_one=False, limit=5)
    for result in results:
        locations.append(result.raw)
    return jsonify(locations)

@tool_route.route("/route", methods=["GET"])
def mapsRoute():
    start = request.args.get("start")
    end = request.args.get("end")
    transportation_mode = request.args.get("mode")
    
    if start == None or end == None or start == "" or end == "":
        abort(400)
    
    if transportation_mode == None: transportation_mode = "driving-car"
    elif transportation_mode == "driving": transportation_mode = "driving-car"
    elif transportation_mode == "walking": transportation_mode = "foot-walking"
    elif transportation_mode == "cycling": transportation_mode = "cycling-regular"
    elif transportation_mode == "wheelchair": transportation_mode = "wheelchair"
        
    body = {"coordinates":[[float(start.split(",")[1]), float(start.split(",")[0])], [float(end.split(",")[1]), float(end.split(",")[0])]]}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': openrouteservice_api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }

    response = requests.post(f"https://api.openrouteservice.org/v2/directions/{transportation_mode}/geojson", json=body, headers=headers)
    
    if response.status_code == 200:
        response = response.json()
        response.pop("bbox", None)
        response.pop("metadata", None)
        
        # Change distance to string and add unit
        distance = response["features"][0]["properties"]["segments"][0]["distance"]
        if distance > 1000:
            distance = str(round(distance / 1000, 1)) + " km"
        else:
            distance = str(round(distance, 1)) + " m"
            
        response["features"][0]["properties"]["segments"][0]["distance"] = distance
        
        # Change duration to string and add unit
        duration = response["features"][0]["properties"]["segments"][0]["duration"]
        if duration > 3600:
            duration = str(round(duration / 3600)) + " h"
        elif duration > 60:
            duration = str(round(duration / 60)) + " min"
        else:
            duration = str(round(duration)) + " s"
        
        response["features"][0]["properties"]["segments"][0]["duration"] = duration
        
        # Change distances of steps to string and add unit
        for step in response["features"][0]["properties"]["segments"][0]["steps"]:
            distance = step["distance"]
            if distance > 1000:
                distance = str(round(distance / 1000, 1)) + "km"
            else:
                distance = str(round(distance, 1)) + "m"
            
            step["distance"] = distance
                
        return jsonify(response)

    else:
        abort(response.status_code)
        
@tool_route.route("/maps", methods=["GET", "POST"])
def maps():
    return render_template("maps.html", menu=th.user(session))

# Nelly Routes

@tool_route.route("/nelly", methods=["GET"])
def nelly():
    if "user_id" not in session:
        return redirect("/")
    elif str(session["user_id"]) != "1" and str(session["user_id"]) != "3": # Only Jan and Nele can access this page
        sql = SQLHelper.SQLHelper()
        is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
        if not is_admin:
            return abort(401)
        
    sql = SQLHelper.SQLHelper()
    stories = sql.readSQL("SELECT * FROM nelly_stories JOIN nelly_tiles ON nelly_stories.id = nelly_tiles.story_id")
    stories_dict = {}
    for story in stories:
        if story["id"] not in stories_dict:
            stories_dict[story["id"]] = {"title": story["title"], "tile_title_color": story["tile_title_color"], "layout": story["layout"], "tiles": []}
        if story["type"] == "text":
            stories_dict[story["id"]]["tiles"].append({"title": story["nelly_tiles.title"], "subtitle": story["subtitle"], "type": "text", "order_on_page": story["order_on_page"]})
        else:
            stories_dict[story["id"]]["tiles"].append({"filename": story["filename"], "type": "image", "order_on_page": story["order_on_page"]})

    #print(stories_dict)
    
    custom_stories = []
    custom_stories_mobile = []
    # iterate over stories_dict and sort the tiles by order_on_page
    for story in stories_dict.values():
        if story["layout"] == 0:
            #custom_stories.append("nelly_templates/template_0_desktop.html")
            custom_stories.append(render_template("nelly_templates/template_0_desktop.html", title=story["title"], tile_title_color=story["tile_title_color"], title0=story["tiles"][0]["title"], subtitle0=story["tiles"][0]["subtitle"], title1=story["tiles"][1]["title"], subtitle1=story["tiles"][1]["subtitle"], image0=story["tiles"][2]["filename"], image1=story["tiles"][3]["filename"], image2=story["tiles"][4]["filename"]))
            custom_stories_mobile.append(render_template("nelly_templates/template_0_mobile.html", title=story["title"], tile_title_color=story["tile_title_color"], title0=story["tiles"][0]["title"], subtitle0=story["tiles"][0]["subtitle"], title1=story["tiles"][1]["title"], subtitle1=story["tiles"][1]["subtitle"], image0=story["tiles"][2]["filename"], image1=story["tiles"][3]["filename"], image2=story["tiles"][4]["filename"]))
        elif story["layout"] == 1:
            #custom_stories.append("nelly_templates/template_1_desktop.html")
            custom_stories.append(render_template("nelly_templates/template_1_desktop.html", title=story["title"], tile_title_color=story["tile_title_color"], title0=story["tiles"][0]["title"], subtitle0=story["tiles"][0]["subtitle"], image0=story["tiles"][1]["filename"], image1=story["tiles"][2]["filename"], image2=story["tiles"][3]["filename"]))
            custom_stories_mobile.append(render_template("nelly_templates/template_1_mobile.html", title=story["title"], tile_title_color=story["tile_title_color"], title0=story["tiles"][0]["title"], subtitle0=story["tiles"][0]["subtitle"], image0=story["tiles"][1]["filename"], image1=story["tiles"][2]["filename"], image2=story["tiles"][3]["filename"]))
        elif story["layout"] == 2:
            #custom_stories.append("nelly_templates/template_2_desktop.html")
            custom_stories.append(render_template("nelly_templates/template_2_desktop.html", title=story["title"], tile_title_color=story["tile_title_color"], title0=story["tiles"][0]["title"], subtitle0=story["tiles"][0]["subtitle"], image0=story["tiles"][1]["filename"], image1=story["tiles"][2]["filename"]))
            custom_stories_mobile.append(render_template("nelly_templates/template_2_mobile.html", title=story["title"], tile_title_color=story["tile_title_color"], title0=story["tiles"][0]["title"], subtitle0=story["tiles"][0]["subtitle"], image0=story["tiles"][1]["filename"], image1=story["tiles"][2]["filename"]))    

    today = datetime.datetime.now()
    showAdventCalendar = True if today.month == 12 else False
    
    
    return render_template("nelly.html", menu=th.user(session), custom_stories=custom_stories, custom_stories_mobile=custom_stories_mobile, showAdventCalendar=showAdventCalendar)
    
@tool_route.route("/nelly_media/<path:filename>", methods=["GET"])
def nelly_media(filename):
        if "user_id" not in session:
            return abort(401)
        elif str(session["user_id"]) != "1" and str(session["user_id"]) != "3":
            sql = SQLHelper.SQLHelper()
            is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
            if not is_admin:
                return abort(401)
        
        try:
            return send_file(f"{gruettedrive_path}/nelly/{filename}")
        except Exception as e:
            print(e)
            return abort(404)
    
@tool_route.route("/send-date-emails", methods=["POST"])
def send_date_emails():
    if "user_id" not in session:
        return abort(401)
    elif str(session["user_id"]) != "1" and str(session["user_id"]) != "3":
        sql = SQLHelper.SQLHelper()
        is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
        if not is_admin:
            return abort(401)
    
    try:
        title = request.json['title']
        date = request.json['date']
        time = request.json['time']
        description = request.json['description']
        prod_mode = request.json['prod_mode']
    except Exception as e:
        print(e)
        return jsonify({"message": "Missing parameters"}), 400
    
    if title == "" or date == "" or time == "" or description == "" or prod_mode == "":
        return jsonify({"message": "Missing parameters"}), 400
    
    data = {
        "title": title,
        "date": date,
        "time": time,
        "description": description,
        "authentication": nelly_auth_key,
        "prod_mode": prod_mode
    }

    response = requests.post("https://api.gruettecloud.com/v1/send-date-email", json=data)
    
    if response.status_code == 200:
        return jsonify({"message": "Emails sent"}), 200
    else:
        return jsonify({"message": response.text}), response.status_code
        
from flask import request, jsonify

@tool_route.route("/nelly_save_story", methods=["POST"])
def nelly_save_story():
    if "user_id" not in session:
        return abort(401)
    elif str(session["user_id"]) != "1" and str(session["user_id"]) != "3":
        sql = SQLHelper.SQLHelper()
        is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
        if not is_admin:
            return abort(401)

    try:
        # Extract the 'story' JSON data from the FormData
        story = request.form.get('story')
        
        if not story:
            return jsonify({"message": "Missing story data"}), 400
        
        # Convert the story string back to a dictionary (JSON)
        story = json.loads(story)

        # Handle uploaded files (images)
        images = request.files.getlist('images')
        print("Story:", story)
        print("Images:", [image.filename for image in images])

        # Save the story to the database
        sql = SQLHelper.SQLHelper()
        sql.writeSQL(f"INSERT INTO nelly_stories (title, tile_title_color, layout) VALUES ('{story['title']}', '{story['tileTitleColor']}', '{story['layout']}')")
        story_id = sql.readSQL(f"SELECT id FROM nelly_stories WHERE title = '{story['title']}' AND layout = '{story['layout']}' AND tile_title_color = '{story['tileTitleColor']}'")[0]["id"]
        
        for i in range(len(story["tiles"])):
            sql.writeSQL(f"INSERT INTO nelly_tiles (story_id, title, subtitle, type, order_on_page) VALUES ('{story_id}', '{story['tiles'][i]['title']}', '{story['tiles'][i]['subtitle']}', 'text', '{i}')")
            
            
        for  i in range(len(images)):
            file_extension = images[i].filename.split(".")[-1]
            filename = f"{story_id}_{i}.{file_extension}"
            images[i].save(f"{gruettedrive_path}/nelly/{filename}")
            sql.writeSQL(f"INSERT INTO nelly_tiles (story_id, type, order_on_page, filename) VALUES ('{story_id}', 'image', '{i}', '{filename}')")

        return jsonify({"message": "Story saved"}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Error processing request"}), 400
    
# Advent Calendar Routes
@tool_route.route("/adventskalender", methods=["GET"])
def adventskalender():
    if "user_id" not in session:
        return redirect("/")
    elif str(session["user_id"]) != "1" and str(session["user_id"]) != "3":
        sql = SQLHelper.SQLHelper()
        is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
        if not is_admin:
            return abort(401)
    
    sql = SQLHelper.SQLHelper()
    return render_template("advent_calendar.html", menu=th.user(session))

@tool_route.route("/candlelight", methods=["GET"])
def candlelight():
    if "user_id" not in session:
        return redirect("/")
    elif str(session["user_id"]) != "1" and str(session["user_id"]) != "3":
        sql = SQLHelper.SQLHelper()
        is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
        if not is_admin:
            return abort(401)
    
    return render_template("bridgerton_render.html")
    
@tool_route.route("/instagram", methods=["GET", "POST"])
def instagram():
    if "user_id" not in session:
        return redirect("/")
    
    elif str(session["user_id"]) != "1" and str(session["user_id"]) != "3":
        sql = SQLHelper.SQLHelper()
        is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
        if not is_admin:
            return abort(401)
    
    def scan_file(file_path, list_to_append):
        with open(file_path, 'r', encoding='utf-8') as html_file:
            soup = BeautifulSoup(html_file, 'html.parser')
            
            username_span = soup.find('span', string="gruettecloud")["class"]
            username_class = " ".join(username_span)
            
            for span in soup.find_all('span', class_=username_class):
                list_to_append.append(span.text)
    
    if request.method == "POST":
        if request.form.get("delete") == "true":
            instagram_dir = os.path.join(gruettedrive_path, str(session["user_id"]), "instagram")
            if os.path.exists(instagram_dir):
                for file in os.listdir(instagram_dir):
                    os.remove(os.path.join(instagram_dir, file))
                os.rmdir(instagram_dir)
            return redirect("/instagram")
        
        elif request.form.get("analyze") == "true":
            followers = []
            following = []
            
            instagram_dir = os.path.join(gruettedrive_path, str(session["user_id"]), "instagram")
            if not os.path.exists(instagram_dir):
                return jsonify({"success": False}), 400
            
            if os.path.exists(os.path.join(instagram_dir, "followers.html")):
                scan_file(os.path.join(instagram_dir, "followers.html"), followers)
            if os.path.exists(os.path.join(instagram_dir, "following.html")):
                scan_file(os.path.join(instagram_dir, "following.html"), following)
                
            not_following_back = set(following) - set(followers)
            not_following_back = list(not_following_back)
            
            im_not_following_back = set(followers) - set(following)
            im_not_following_back = list(im_not_following_back)
            
            return jsonify({"success": True, "followers": followers, "following": following, "not_following_back": not_following_back, "im_not_following_back": im_not_following_back})
            
        
        if "followers" in request.files:
            file = request.files["followers"]
            file.save(os.path.join(gruettedrive_path, str(session["user_id"]), "instagram", "followers.html"))
            return jsonify({"success": True})
        elif "following" in request.files:
            file = request.files["following"]
            file.save(os.path.join(gruettedrive_path, str(session["user_id"]), "instagram", "following.html"))
            return jsonify({"success": True})
        
        return jsonify({"success": False}), 400
        
    
    if request.method == "GET":
        
        instagram_dir = os.path.join(gruettedrive_path, str(session["user_id"]), "instagram")
        if not os.path.exists(instagram_dir):
            os.makedirs(instagram_dir)        
        
        files = {
            "followers": {
                "filename": None,
                "date": None
            },
            "following": {
                "filename": None,
                "date": None
            }
        }
        
        
        if os.path.exists(os.path.join(instagram_dir, "followers.html")):
            files["followers"]["filename"] = "followers.html"
            files["followers"]["date"] = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(instagram_dir, "followers.html"))).strftime("%d.%m.%Y %H:%M")
        
        if os.path.exists(os.path.join(instagram_dir, "following.html")):
            files["following"]["filename"] = "following.html"
            files["following"]["date"] = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(instagram_dir, "following.html"))).strftime("%d.%m.%Y %H:%M")
            
        
        return render_template("instagram_old.html", files=files, menu=th.user(session))

@tool_route.route("/external_html/weather.html", methods=["GET"])
def external_html_weather():
    if "python-requests/" not in request.headers.get("User-Agent"):
        return abort(404)
    return send_file(os.path.join(gruettedrive_path, "external_html", "weather.html"))

@tool_route.route("/mensieren", methods=["GET"])
def mensieren():
    return "<h1>TEST ONLY</h1><a href='https://mensieren.de'>mensieren.de</a>"

    
    
# Endpoints for Flutter App

import jwt
import datetime
from config import secret_key
from werkzeug.security import check_password_hash
from pythonHelper import EncryptionHelper
from urllib.parse import unquote


@tool_route.route('/api/v1/login', methods=['POST'])
def api_v1_login():
    data = request.form
    username = str(data.get('username').lower())
    password = str(data.get('password'))

    sql = SQLHelper.SQLHelper()
    
    # Search for user in database
    user = sql.readSQL(f"SELECT * FROM users WHERE username = '{username}'")
    
    # If user exists, check if password is correct
    if user != []:
        # If username and password are correct
        if user[0]["username"].lower() == username and check_password_hash(user[0]["password"], password):
            
            # Check if the user has verified their account
            if not bool(user[0]["is_email_verified"]):
                return jsonify({'message': 'Please verify your email address before logging in.'}), 401
            
            # Check if 2FA is enabled
            if bool(user[0]["is_2fa_enabled"]):
                return jsonify({'message': '2FA is enabled on this account. This is a test endpoint which does not support 2FA.'}), 401
            
            # Check if user is an admin
            if not bool(user[0]["is_admin"]):
                return jsonify({'message': 'You are not eligible to use this endpoint.'}), 401
            
            # Log the user in
            else:
                # Generate JWT token
                token = jwt.encode({'username': username, 'exp': datetime.datetime.now() + datetime.timedelta(weeks=3)}, secret_key, algorithm="HS256")
                return jsonify({'message': f'{username}', 'token': token}), 200

        # If password is or username is incorrect
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
        
    # If user does not exist
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# TODO: Method not working, must be adapted to new database structure
@tool_route.route('/api/v1/get_chats', methods=['GET'])
def api_v1_get_chats():
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        # Check for Bearer and remove
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    return jsonify({'message': 'This endpoint is not implemented yet.'}), 501
    
    sql = SQLHelper.SQLHelper()    
    
    # Fetch active chats from the database
    active_chats_database = sql.readSQL(f"SELECT * FROM chats WHERE username_send = '{data['username']}' OR username_receive = '{data['username']}'")
    active_chats = []
                
    # Add all active chats to a list
    for chat in active_chats_database:
        if chat["username_send"].lower() == data["username"].lower():
            if chat["username_receive"].lower() not in [x["username"].lower() for x in active_chats]:
                unread_messages = len(sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{chat['username_receive']}' AND username_receive = '{data['username']}' AND is_read = '{False}'"))
                user_db = sql.readSQL(f"SELECT * FROM users WHERE id = '{chat['username_receive']}'")
                blocked = bool(sql.readSQL(f"SELECT * FROM gruttechat_blocked_users WHERE username = '{chat['username_receive']}' AND username_blocked = '{data['username']}' OR username = '{data['username']}' AND username_blocked = '{chat['username_receive']}'"))
                if user_db != []:
                    active_chats.append({"username": chat["username_receive"].lower(), "pfp": f"{user_db[0]['profile_picture']}.png", "is_verified": user_db[0]["is_verified"], "blocked": blocked, "unread_messages": unread_messages})
        else:
            if chat["username_send"].lower() not in [x["username"].lower() for x in active_chats]:
                unread_messages = len(sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{chat['username_send']}' AND username_receive = '{data['username']}' AND is_read = '{False}'"))
                user_db = sql.readSQL(f"SELECT * FROM users WHERE id = '{chat['username_send']}'")
                blocked = bool(sql.readSQL(f"SELECT * FROM gruttechat_blocked_users WHERE username = '{chat['username_send']}' AND username_blocked = '{data['username']}' OR username = '{data['username']}' AND username_blocked = '{chat['username_send']}'"))
                if user_db != []:
                    active_chats.append({"username": chat["username_send"].lower(), "pfp": f"{user_db[0]['profile_picture']}.png", "is_verified": user_db[0]["is_verified"], "blocked": blocked, "unread_messages": unread_messages})
    
    return jsonify(active_chats)

@tool_route.route('/api/v1/get_logged_in_user', methods=['GET'])
def api_v1_get_logged_in_user():    
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE username = '{data['username']}'")
    
    if user == []:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({'username': user[0]['username'], 'email': user[0]['email'], 'is_verified': bool(user[0]['is_verified']), 'is_admin': bool(user[0]['is_admin']), "has_premium": bool(user[0]['has_premium']), 'profile_picture': user[0]['profile_picture']})

# TODO: Method not working, must be adapted to new database structure
@tool_route.route('/api/v1/get_chat', methods=['GET'])
def api_v1_get_chat():
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    if request.headers.get('Username') is None:
        return jsonify({'message': 'No username provided'}), 400
    
    return jsonify({'message': 'This endpoint is not implemented yet.'}), 501
    
    sql = SQLHelper.SQLHelper()
    
    # Fetch messages from the database
    messages = sql.readSQL(f"SELECT * FROM chats WHERE username_send = '{data['username']}' AND username_receive = '{request.headers.get('username')}' OR username_send = '{request.headers.get('username')}' AND username_receive = '{data['username']}' ORDER BY created_at")
    
    # Mark all messages as read
    sql.writeSQL(f"UPDATE gruttechat_messages SET is_read = {True} WHERE username_send = '{request.headers.get('username')}' AND username_receive = '{data['username']}'")
    
    new_messages = []
    try:
        local_messages = request.headers.get('Messages').split(",")
    except:
        local_messages = []
                    
    eh = EncryptionHelper.EncryptionHelper()
    for message in messages:
        if str(message["id"]) not in local_messages:
            try:
                decrypted_message = str(eh.decrypt_message(message["message_content"]))
            except:
                decrypted_message = "Decryption Error!"
            new_messages.append({"message_id": message["id"], "message": decrypted_message, "username_send": message["username_send"], "datetime": message["created_at"].strftime("%d.%m.%Y %H:%M"), "is_read": message["is_read"]})
    
    new_messages = new_messages[::-1]
    
    return jsonify(new_messages)

# TODO: Method not working, must be adapted to new database structure
@tool_route.route('/api/v1/send_message', methods=['POST'])
def api_v1_send_message():
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    if request.headers.get('Username') is None:
        return jsonify({'message': 'No username provided'}), 400
    
    if request.headers.get('Message') is None:
        return jsonify({'message': 'No message provided'}), 400
    
    return jsonify({'message': 'This endpoint is not implemented yet.'}), 501
    
    sql = SQLHelper.SQLHelper()
    eh = EncryptionHelper.EncryptionHelper()
    
    message = str(request.headers.get('Message'))
    message = unquote(message)
    encrypted_message = eh.encrypt_message(message)
    
    sql.writeSQL(f"INSERT INTO gruttechat_messages (username_send, username_receive, message_content, is_read) VALUES ('{data['username']}', '{request.headers.get('Username')}', '{encrypted_message}', {False})")
    
    return jsonify({'message': 'Message sent'}), 200

@tool_route.route('/api/v1/get_available_chats', methods=['GET'])
def api_v1_get_available_chats():
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    if request.headers.get('query') is None:
        return jsonify({'message': 'No query provided'}), 400
    
    sql = SQLHelper.SQLHelper()
    
    # Fetch all users from the database
    users = sql.readSQL(f"SELECT * FROM users WHERE id LIKE '%{request.headers.get('query')}%' LIMIT 10")
    
    available_chats = []
    
    for user in users:
        if user["username"].lower() != data["username"]:
            available_chats.append({"username": user["username"], "is_verified": user["is_verified"], "pfp": user["profile_picture"]})

    return jsonify(available_chats)



# TODO: Method not working, must be adapted to new database structure
@tool_route.route('/api/v1/get_expenses', methods=['GET'])
def api_v1_get_expenses():
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    return jsonify({'message': 'This endpoint is not implemented yet.'}), 501
    
    sql = SQLHelper.SQLHelper()
    
    amount_spent = 0
    monthly_budget = sql.readSQL(f"SELECT finance_budget FROM users WHERE id = '{str(data['username'])}'")[0]["finance_budget"]
    amount_remaining = monthly_budget
    receipts_current_month = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE username = '{str(data['username'])}' AND MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW()) ORDER BY date DESC")
    for receipt in receipts_current_month:
        if receipt["is_income"]:
            if receipt["add_to_budget"]:
                amount_remaining += float(receipt["total"])
                amount_spent -= float(receipt["total"])
        else:
            amount_remaining -= float(receipt["total"])
            amount_spent += float(receipt["total"])

    amount_remaining = f"{float(amount_remaining):.2f}".replace(".", ",")
    
    
    percentage_spent = (amount_spent / monthly_budget) * 100
    amount_spent = f"{float(amount_spent):.2f}".replace(".", ",")
    
    receipts_date = []
    
    
    for receipt in receipts_current_month:
        receipt["total"] = f"{float(receipt['total']):.2f}".replace(".", ",")
        receipt["date"] = receipt["date"].strftime("%d.%m.%Y")

        if not receipts_date:  # Check if receipts_date is empty
            receipts_date.append([receipt])
        else:
            last_date = receipts_date[-1][0]["date"] if receipts_date[-1] else None

            if receipt["date"] != last_date:
                receipts_date.append([receipt])
            else:
                receipts_date[-1].append(receipt)
                
    return jsonify({"amount_spent": amount_spent, "amount_remaining": amount_remaining, "percentage_spent": percentage_spent, "receipts": receipts_date, "monthly_budget": monthly_budget})

# TODO: Method not working, must be adapted to new database structure
@tool_route.route('/api/v1/upload-receipt', methods=['POST'])
def api_v1_upload_receipt():
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token; Bearer tag missing'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    return jsonify({'message': 'This endpoint is not implemented yet.'}), 501
    
    if request.files['image'] is None:
        return jsonify({'message': 'No file provided'}), 400
    
    url = 'https://api.mindee.net/v1/products/mindee/expense_receipts/v5/predict'

    # Multipart/form-data payload
    files = {'document': request.files['image']}

    # Headers
    headers = {
        'Authorization': f'Token {mindee_api_key}',
    }

    # Make the API request
    response = requests.post(url, files=files, headers=headers)

    # Print the response
    r = response.json()
    items = r["document"]["inference"]["pages"][0]["prediction"]["line_items"]
    merchant_name = r["document"]["inference"]["pages"][0]["prediction"]["supplier_name"]["raw_value"]
    total = r["document"]["inference"]["pages"][0]["prediction"]["total_amount"]["value"]
    try:
        total = float(total)
    except:
        total = 0
    items_list = []
    for item in items:
        items_list.append({"name": item["description"], "price": item["total_amount"]})
    
    receipt_id = secrets.token_hex(8)
    
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"INSERT INTO gruettecloud_receipts (username, merchant_name, total, date, receipt_id, payment_method, is_income) VALUES ('{str(data['username'])}', '{merchant_name}', '{total}', NOW(), '{receipt_id}', 'other', {False})")
    for item in items_list:
        sql.writeSQL(f"INSERT INTO gruettecloud_receipt_items (receipt_id, item, price) VALUES ('{receipt_id}', '{item['name']}', '{item['price']}')")
    
    return jsonify({'message': 'Receipt uploaded', 'receipt_id': receipt_id}), 200

# TODO: Method not working, must be adapted to new database structure
@tool_route.route('/api/v1/add_transaction', methods=['POST'])
def api_v1_add_transaction():
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token; Bearer tag missing'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    if request.form.get('total') is None:
        return jsonify({'message': 'No total provided'}), 400
    
    try:
        total = float(request.form.get('total'))
    except:
        return jsonify({'message': 'Invalid total provided'}), 400
    
    if request.form.get('merchant_name') is None:
        return jsonify({'message': 'No merchant name provided'}), 400
    
    if request.form.get('payment_method') is None:
        return jsonify({'message': 'No payment method provided'}), 400
    
    return jsonify({'message': 'This endpoint is not implemented yet.'}), 501
    
    total = float(request.form.get('total'))
    merchant_name = request.form.get('merchant_name')
    payment_method = request.form.get('payment_method')
    
    add_to_budget = False
    is_income = False
    if total >= 0:
        add_to_budget = True
        is_income = True
    
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"INSERT INTO gruettecloud_receipts (username, merchant_name, total, date, receipt_id, payment_method, is_income, add_to_budget) VALUES ('{str(data['username'])}', '{merchant_name}', '{abs(total)}', NOW(), '{secrets.token_hex(8)}', '{payment_method}', {is_income}, {add_to_budget})")
    
    return jsonify({'message': 'Transaction added'}), 200