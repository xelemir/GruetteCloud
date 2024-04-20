import datetime
import json
import os
import secrets
from flask import abort, jsonify, render_template, request, redirect, send_file, session, Blueprint, url_for
from flask_socketio import SocketIO
import requests
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from geopy.geocoders import Nominatim
from threading import Thread
from tgtg import TgtgClient


from pythonHelper import SQLHelper, MailHelper, TemplateHelper
from config import templates_path, openrouteservice_api_key, gruettedrive_path, gmail_mail

    
tool_route = Blueprint("Tools", "Tools", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()

@tool_route.route("/logout")
def logout():
    """ Logout route

    Returns:
        str: Redirect to home page
    """    
    session.pop("username", None)
    session.clear()
    return redirect("/")

def create_ticket(username, message, email):
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"INSERT INTO gruttecloud_tickets (name, username, email, message, status) VALUES ('{username}', '{username}', '{email}', '{message}', 'opened')")
        
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
            sql.writeSQL(f"UPDATE gruttechat_users SET receive_emails = {False} WHERE email = '{email}'")
            t1 = Thread(target=create_ticket, args=("unknown", f"Someone unsubscribed from communication emails. Email: {email}", email)).start()
            return render_template("unsubscribe.html", menu=th.user(session), mode="unsubscribe_confirmed")

    username = request.args.get("username")
    email = request.args.get("email")
    token = request.args.get("token")
    confirmed = request.args.get("confirmed")
    
    if confirmed != "true":
        return render_template("unsubscribe.html", menu=th.user(session), username=username, email=email, token=token, mode="unsubscribe")
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")

    if user == []:
        return redirect("/")
    elif user[0]["email"] != email or user[0]["verification_code"] != token:
        return redirect("/")
    else:
        user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
        if user[0]["receive_emails"] == False:
            return redirect("/")

        sql.writeSQL(f"UPDATE gruttechat_users SET receive_emails = {False} WHERE username = '{username}'")
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
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    
    if user == []:
        return redirect("/")
    elif user[0]["email"] != email or user[0]["verification_code"] != token:
        return redirect("/")
    else:
        sql.writeSQL(f"UPDATE gruttechat_users SET receive_emails = {True} WHERE username = '{username}'")
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
            
            token_db = sql.readSQL(f"SELECT * FROM reset_password WHERE token = '{token}'")
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
            
            user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}' AND email = '{email}'")
            if user == []:
                return render_template("reset_password.html", menu=th.user(session), action="email_sent", email=email)
            
            else:
                generate_token = secrets.token_hex(15)
                
                sql.writeSQL(f"INSERT INTO reset_password (username, token) VALUES ('{username}', '{generate_token}')")
                
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
            token_db = sql.readSQL(f"SELECT * FROM reset_password WHERE token = '{token}'")
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
            
            username = token_db[0]["username"]
            sql.writeSQL(f"UPDATE gruttechat_users SET password = '{generate_password_hash(password)}', is_2fa_enabled = {False} WHERE username = '{username}'")
            sql.writeSQL(f"UPDATE reset_password SET is_used = {True} WHERE token = '{token}'")
            
            return render_template("reset_password.html", menu=th.user(session), action="password_reset")
        
@tool_route.route("/help", methods=["GET"])
def help():
    return render_template("help.html", menu=th.user(session))
        
@tool_route.route("/about", methods=["GET"])
def about():
    sql = SQLHelper.SQLHelper()
    pfp_jan = sql.readSQL("SELECT profile_picture FROM gruttechat_users WHERE username = 'jan'")[0]["profile_picture"]
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
    """ Post route to send a support message to the GrütteCloud team

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
    
    sql.writeSQL(f"INSERT INTO gruttecloud_tickets (name, username, email, message, status) VALUES ('{name}', '{username}', '{email}', '{message}', 'opened')")
    
    async_mail = Thread(target=MailHelper.MailHelper().send_support_mail, args=(name, username, email, message))
    async_mail.start()
    
    return render_template("support.html", menu=th.user(session), error="success")
    
    
@tool_route.route("/apply", methods=["GET", "POST"])
def apply():
    if request.method == "GET":
        return render_template("apartment_apply.html", menu=th.user(session))
    
    else:
        try:
            application_id = request.form["application_id"]
            new_application = False
        except:
            application_id = secrets.token_hex(8)
            new_application = True
        
        name = request.form["name"]
        age = request.form["age"]
        pronouns = request.form["pronouns"]
        email = request.form["email"]
        move_in_date = request.form["move_in_date"]
        occupation = request.form["occupation"]
        languages = request.form["language"]
        dietry_preferences = request.form["dietry_preferences"]
        coffee_or_tea = request.form["coffee_or_tea"]
        about = request.form["about"]
        expectations = request.form["expectations"]
        parties = request.form["parties"]
        alcohol = request.form["alcohol"]
        smoker = request.form["smoker"]
        shared_apartment_experience = request.form["shared_apartment_experience"]
        
        
        file1 = request.files["file1"]
        file2 = request.files["file2"]
        file3 = request.files["file3"]
        
        if file1:
            file1Filename = secure_filename(application_id + file1.filename)
            file1.save(os.path.join(gruettedrive_path, "GruetteCloud", file1Filename))
        else:
            if new_application: file1Filename = None
            else:
                file1Filename = request.form["file1Filename"]
                if file1Filename == "None": file1Filename = None
        
        if file2:
            file2Filename = secure_filename(application_id + file2.filename)
            file2.save(os.path.join(gruettedrive_path, "GruetteCloud", file2Filename))
        else:
            if new_application: file2Filename = None
            else:
                file2Filename = request.form["file2Filename"]
                if file2Filename == "None": file2Filename = None
        
        if file3:
            file3Filename = secure_filename(application_id + file3.filename)
            file3.save(os.path.join(gruettedrive_path, "GruetteCloud", file3Filename))
        else:
            if new_application: file3Filename = None
            else:
                file3Filename = request.form["file3Filename"]
                if file3Filename == "None": file3Filename = None
            
            
        application = {
            "application_id": application_id,
            "name": name,
            "age": age,
            "pronouns": pronouns,
            "email": email,
            "move_in_date": move_in_date,
            "occupation": occupation,
            "languages": languages,
            "dietry_preferences": dietry_preferences,
            "coffee_or_tea": coffee_or_tea,
            "about": about,
            "expectations": expectations,
            "parties": parties,
            "alcohol": alcohol,
            "smoker": smoker,
            "shared_apartment_experience": shared_apartment_experience,
            "file1": file1Filename,
            "file2": file2Filename,
            "file3": file3Filename
        }
        
        json_object = json.dumps(application, indent=4)
        
        with open(os.path.join(gruettedrive_path, "GruetteCloud", f"Application_{application_id}.json"), "w") as outfile:
            outfile.write(json_object)

        if new_application:
            return render_template("apartment_apply.html", menu=th.user(session), application_id=application_id, error="success", application=application)
        else:
            return render_template("apartment_apply.html", menu=th.user(session), application_id=application_id, error="changes_saved", application=application)
    
@tool_route.route("/application/<application_id>", methods=["GET"])
def application(application_id):
    if os.path.exists(os.path.join(gruettedrive_path, "GruetteCloud", f"Application_{application_id}.json")):
        with open(os.path.join(gruettedrive_path, "GruetteCloud", f"Application_{application_id}.json"), "r") as infile:
            application = json.load(infile)
        return render_template("apartment_apply.html", menu=th.user(session), application=application)

    else:
        return redirect("/apply")
            


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

@tool_route.route("/log_user_location", methods=["GET"])
def log_user_location():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    useragent = request.args.get("useragent")
    
    sql = SQLHelper.SQLHelper()

    if "username" in session:
        username = session["username"]
        sql.writeSQL(f"INSERT INTO gruttecloud_tickets (username, message, status) VALUES ('{username}', '{username} logged their location. Lat: {lat}, Lon: {lon}', 'opened')")
    else:
        username = None
        sql.writeSQL(f"INSERT INTO gruttecloud_tickets (message, status) VALUES ('{username} logged their location. Lat: {lat}, Lon: {lon}', 'opened')")
        
    sql.writeSQL(f"INSERT INTO gruettecloud_user_locations (username, lat, lon, useragent) VALUES ('{username}', '{lat}', '{lon}', '{useragent}')")
    
    return jsonify({"success": True})

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
    mobile = request.args.get("mobile")
    if mobile == "true":
        return render_template("mapsMobile.html", menu=th.user(session))
    else:
        return render_template("maps.html", menu=th.user(session))
    
    
@tool_route.route("/zuffenhausen", methods=["GET", "POST"])
def zuffenhausen():
    if request.method == "GET":
        if request.args.get("id") == None:
            return render_template("zuffenhausen.html", menu=th.user(session), mode="form")
        else:
            application = SQLHelper.SQLHelper().readSQL(f"SELECT * FROM zuffenhausen_visits WHERE application_id = '{request.args.get('id')}'")
            if application == []: abort(500)
                        
            visitorsToString = ""
            for visitor in [application[0]["visitor1"], application[0]["visitor2"], application[0]["visitor3"], application[0]["visitor4"], application[0]["visitor5"], application[0]["visitor6"], application[0]["visitor7"], application[0]["visitor8"]]:
                if visitor != "None":
                    visitorsToString += f"{visitor}, "
                    
            visitorsToString = visitorsToString[:-2]
            
            date = datetime.datetime.strptime(str(application[0]["date"]), "%Y-%m-%d %H:%M:%S")
            date = date.strftime("%d.%m.%Y %H:%M")
            
            return render_template("zuffenhausen.html", menu=th.user(session), mode="success", application_id=application[0]["application_id"], date=date, visitors=visitorsToString, reasons=application[0]["reasons"], status=application[0]["status"], note=application[0]["note"])
            
    else:
        date = request.form["date"]
        visitor1 = request.form["visitor1"]
        visitor2 = request.form["visitor2"] if "visitor2" in request.form else None
        visitor3 = request.form["visitor3"] if "visitor3" in request.form else None
        visitor4 = request.form["visitor4"] if "visitor4" in request.form else None
        visitor5 = request.form["visitor5"] if "visitor5" in request.form else None
        visitor6 = request.form["visitor6"] if "visitor6" in request.form else None
        visitor7 = request.form["visitor7"] if "visitor7" in request.form else None
        visitor8 = request.form["visitor8"] if "visitor8" in request.form else None
        reasons = request.form["reasons"]
        email = request.form["email"]
        
        date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M")
        
        visitorsToString = ""
        for visitor in [visitor2, visitor3, visitor4, visitor5, visitor6, visitor7, visitor8]:
            if visitor != None:
                visitorsToString += f"{visitor}, "
                
        if visitorsToString != "": visitorsToString = visitorsToString[:-2]
        
        accompaniedBy = f"{visitor1} will be accompanied by {visitorsToString}." if visitorsToString != "" else f"{visitor1} will come alone."
        application_id = secrets.token_hex(4)

        email_jan = SQLHelper.SQLHelper().readSQL(f"SELECT * FROM gruttechat_users WHERE username = 'jan'")[0]["email"]
        
        SQLHelper.SQLHelper().writeSQL(f"INSERT INTO zuffenhausen_visits (date, visitor1, visitor2, visitor3, visitor4, visitor5, visitor6, visitor7, visitor8, reasons, status, application_id, email) VALUES ('{date}', '{visitor1}', '{visitor2}', '{visitor3}', '{visitor4}', '{visitor5}', '{visitor6}', '{visitor7}', '{visitor8}', '{reasons}', 'pending', '{application_id}', '{email}')")
        SQLHelper.SQLHelper().writeSQL(f"INSERT INTO gruttecloud_tickets (message, status, assigned_to) VALUES ('#Z#{ application_id }# {visitor1} wants to visit you on {date.strftime('%d.%m.%Y %H:%M')}. They are coming for the following reasons: {reasons}. {accompaniedBy}', 'in_progress', 'jan')")
        ticket_id_with_application = SQLHelper.SQLHelper().readSQL(f"SELECT * FROM gruttecloud_tickets WHERE message = '#Z#{ application_id }# {visitor1} wants to visit you on {date.strftime('%d.%m.%Y %H:%M')}. They are coming for the following reasons: {reasons}. {accompaniedBy}'")[0]["id"]

        Thread(target=MailHelper.MailHelper().send_email, args=(email_jan, "jan", f"{visitor1} wants to visit on {date.strftime('%d.%m.%Y %H:%M')}", f"{visitor1} wants to visit you on {date.strftime('%d.%m.%Y %H:%M')}. They are coming for the following reasons: {reasons}. {accompaniedBy}.<br><br><a href='https://www.gruettecloud.com/zuffenhausen/modify?type=approve&id={ticket_id_with_application}' style='text-decoration: none; color: #0A84FF;'>Approve</a> | <a href='https://www.gruettecloud.com/zuffenhausen/modify?type=deny&id={ticket_id_with_application}' style='text-decoration: none; color: #0A84FF;'>Deny</a><br><br>", "None", "https://www.gruettecloud.com/static/gruettecloud_logo.png", True)).start()
        Thread(target=MailHelper.MailHelper().send_email, args=(email, visitor1, f"Your visit to Jan on {date.strftime('%d.%m.%Y %H:%M')}", f"Your visit to Zuffenhausen on {date.strftime('%d.%m.%Y %H:%M')} has been requested. You will receive an email once your visit request has been approved or declined. You can always check the status of your request using the link below.<p><a href='https://www.gruettecloud.com/zuffenhausen?id={application_id}' style='text-decoration: none; color: #0A84FF;'>https://www.gruettecloud.com/zuffenhausen?id={application_id}</a></p>", "None", "https://www.gruettecloud.com/static/gruettecloud_logo.png", True)).start()
        
        return redirect(f"/zuffenhausen?id={application_id}")

@tool_route.route("/visit", methods=["GET"])
def visit():
    return redirect("/zuffenhausen")

@tool_route.route("/zuffenhausen/modify", methods=["GET"])
def zuffenhausen_modify():
    if "type" not in request.args or "id" not in request.args:
        abort(404)
        
    if request.args.get("type") == "delete":
        SQLHelper.SQLHelper().writeSQL(f"DELETE FROM zuffenhausen_visits WHERE application_id = '{request.args.get('id')}'")
        return render_template("zuffenhausen.html", menu=th.user(session), mode="deleted")
    
    if request.args.get("type") == "approve":
        user = SQLHelper.SQLHelper().readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")
        if user[0]["is_admin"] == False: abort(403)
        ticket_message =SQLHelper.SQLHelper().readSQL(f"SELECT message FROM gruttecloud_tickets WHERE id = '{request.args.get('id')}'")
        application_id = ticket_message[0]["message"].split("#")[2]
        SQLHelper.SQLHelper().writeSQL(f"UPDATE zuffenhausen_visits SET status = 'approved' WHERE application_id = '{application_id}'")
        SQLHelper.SQLHelper().writeSQL(f"UPDATE gruttecloud_tickets SET message = '#Z#{application_id}# Visit approved.' WHERE id = '{request.args.get('id')}'")
        visit = SQLHelper.SQLHelper().readSQL(f"SELECT * FROM zuffenhausen_visits WHERE application_id = '{application_id}'")[0]
        date = visit["date"].strftime("%d.%m.%Y %H:%M")
        Thread(target=MailHelper.MailHelper().send_email, args=(visit["email"], visit["visitor1"], f"Your visit to Jan on {date}", f"Your visit to Jan on {date} has been APPROVED. You can always check the status of your request using the link below.<p><a href='https://www.gruettecloud.com/zuffenhausen?id={application_id}' style='text-decoration: none; color: #0A84FF;'>https://www.gruettecloud.com/zuffenhausen?id={application_id}</a></p>", "None", "https://www.gruettecloud.com/static/gruettecloud_logo.png", True)).start()
        return redirect("/dashboard")
    
    if request.args.get("type") == "deny":
        user = SQLHelper.SQLHelper().readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")
        if user[0]["is_admin"] == False: abort(403)
        ticket_message =SQLHelper.SQLHelper().readSQL(f"SELECT message FROM gruttecloud_tickets WHERE id = '{request.args.get('id')}'")
        application_id = ticket_message[0]["message"].split("#")[2]
        SQLHelper.SQLHelper().writeSQL(f"UPDATE zuffenhausen_visits SET status = 'denied' WHERE application_id = '{application_id}'")
        SQLHelper.SQLHelper().writeSQL(f"UPDATE gruttecloud_tickets SET message = '#Z#{application_id}# Visit denied.' WHERE id = '{request.args.get('id')}'")
        visit = SQLHelper.SQLHelper().readSQL(f"SELECT * FROM zuffenhausen_visits WHERE application_id = '{application_id}'")[0]
        date = visit["date"].strftime("%d.%m.%Y %H:%M")
        Thread(target=MailHelper.MailHelper().send_email, args=(visit["email"], visit["visitor1"], f"Your visit to Zuffenhausen on {date}", f"Your visit to Jan on {date} has been DENIED. You can always check the status of your request using the link below.<p><a href='https://www.gruettecloud.com/zuffenhausen?id={application_id}' style='text-decoration: none; color: #0A84FF;'>https://www.gruettecloud.com/zuffenhausen?id={application_id}</a></p>", "None", "https://www.gruettecloud.com/static/gruettecloud_logo.png", True)).start()
        return redirect("/dashboard")
        
    if request.args.get("type") == "note":
        if "note" not in request.args: abort(400)
        user = SQLHelper.SQLHelper().readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")
        if user[0]["is_admin"] == False: abort(403)
        ticket_message =SQLHelper.SQLHelper().readSQL(f"SELECT message FROM gruttecloud_tickets WHERE id = '{request.args.get('id')}'")
        application_id = ticket_message[0]["message"].split("#")[2]
        SQLHelper.SQLHelper().writeSQL(f"UPDATE zuffenhausen_visits SET note = '{request.args.get('note')}' WHERE application_id = '{application_id}'")
        return redirect("/dashboard")
    
@tool_route.route("/api/v1/tgtg", methods=["GET", "POST"])
def tgtg():
    if "username" not in session: abort(403)
    username = session["username"]
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    if user == [] or bool(user[0]["is_admin"]) == False: abort(403)
    
    if request.args.get("action") is None or request.args.get("id") is None or request.args.get("access_token") is None or request.args.get("refresh_token") is None or request.args.get("user_id") is None or request.args.get("cookie") is None: abort(400)
    if request.args.get("action") == "accept":
        client = TgtgClient(access_token=request.args.get("access_token"), refresh_token=request.args.get("refresh_token"), user_id=request.args.get("user_id"), cookie=request.args.get("cookie"))
        client.abort_order(request.args.get("id"))
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})
    
    
    

# Test Endpoints for Flutter App

import jwt
import datetime
from config import secret_key
from werkzeug.security import check_password_hash
from pythonHelper import EncryptionHelper


@tool_route.route('/api/login', methods=['POST'])
def api_login():
    data = request.form
    username = str(data.get('username').lower())
    password = str(data.get('password'))

    sql = SQLHelper.SQLHelper()
    
    # Search for user in database
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    
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
                token = jwt.encode({'username': username, 'exp': datetime.datetime.now() + datetime.timedelta(minutes=30)}, secret_key, algorithm="HS256")
                return jsonify({'message': f'{username}', 'token': token}), 200

        # If password is or username is incorrect
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
        
    # If user does not exist
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@tool_route.route('/api/get_chats', methods=['GET'])
def api_get_chats():
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
    
    sql = SQLHelper.SQLHelper()    
    
    # Fetch active chats from the database
    active_chats_database = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{data['username']}' OR username_receive = '{data['username']}'")
    active_chats = []
                
    # Add all active chats to a list
    for chat in active_chats_database:
        if chat["username_send"].lower() == data["username"].lower():
            if chat["username_receive"].lower() not in [x["username"].lower() for x in active_chats]:
                unread_messages = len(sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{chat['username_receive']}' AND username_receive = '{data['username']}' AND is_read = '{False}'"))
                user_db = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{chat['username_receive']}'")
                blocked = bool(sql.readSQL(f"SELECT * FROM gruttechat_blocked_users WHERE username = '{chat['username_receive']}' AND username_blocked = '{data['username']}' OR username = '{data['username']}' AND username_blocked = '{chat['username_receive']}'"))
                if user_db != []:
                    active_chats.append({"username": chat["username_receive"].lower(), "pfp": f"{user_db[0]['profile_picture']}.png", "is_verified": user_db[0]["is_verified"], "blocked": blocked, "unread_messages": unread_messages})
        else:
            if chat["username_send"].lower() not in [x["username"].lower() for x in active_chats]:
                unread_messages = len(sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{chat['username_send']}' AND username_receive = '{data['username']}' AND is_read = '{False}'"))
                user_db = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{chat['username_send']}'")
                blocked = bool(sql.readSQL(f"SELECT * FROM gruttechat_blocked_users WHERE username = '{chat['username_send']}' AND username_blocked = '{data['username']}' OR username = '{data['username']}' AND username_blocked = '{chat['username_send']}'"))
                if user_db != []:
                    active_chats.append({"username": chat["username_send"].lower(), "pfp": f"{user_db[0]['profile_picture']}.png", "is_verified": user_db[0]["is_verified"], "blocked": blocked, "unread_messages": unread_messages})
    
    return jsonify(active_chats)

@tool_route.route('/api/get_logged_in_user', methods=['GET'])
def api_get_logged_in_user():    
    print(request.headers)
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
    
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{data['username']}'")
    
    if user == []:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({'username': user[0]['username'], 'email': user[0]['email'], 'is_verified': bool(user[0]['is_verified']), 'is_admin': bool(user[0]['is_admin']), "has_premium": bool(user[0]['has_premium']), 'profile_picture': user[0]['profile_picture']})


@tool_route.route('/api/get_chat', methods=['GET'])
def api_get_chat():
    if request.headers.get('Token-Authorization') is None:
        return jsonify({'message': 'No token provided'}), 401
    
    try:
        auth = request.headers.get('Token-Authorization').split(" ")
        if auth[0] != "Bearer":
            return jsonify({'message': 'Invalid token'}), 401
        data = jwt.decode(auth[1], secret_key, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    if request.headers.get('username') is None:
        return jsonify({'message': 'No username provided'}), 400
    
    sql = SQLHelper.SQLHelper()
    
    # Fetch messages from the database
    messages = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{data['username']}' AND username_receive = '{request.headers.get('username')}' OR username_send = '{request.headers.get('username')}' AND username_receive = '{data['username']}' ORDER BY created_at")
    
    # Mark all messages as read
    sql.writeSQL(f"UPDATE gruttechat_messages SET is_read = {True} WHERE username_send = '{request.headers.get('username')}' AND username_receive = '{data['username']}'")
    
    new_messages = []
    try:
        local_messages = request.headers.get('local_messages').split(",")
    except:
        local_messages = []
            
    eh = EncryptionHelper.EncryptionHelper()
    for message in messages:
        if str(message["id"]) not in local_messages:
            try:
                decrypted_message = str(eh.decrypt_message(message["message_content"]))
            except:
                decrypted_message = "Decryption Error!"
            new_messages.append({"message_id": message["id"], "message": decrypted_message, "username_send": message["username_send"], "created_at": message["created_at"].strftime("%d.%m.%Y %H:%M"), "is_read": message["is_read"]})
    
    return jsonify(new_messages)


@tool_route.route('/api/get_expenses', methods=['GET'])
def api_get_expenses():
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
    
    amount_spent = 0
    monthly_budget = sql.readSQL(f"SELECT finance_budget FROM gruttechat_users WHERE username = '{str(session['username'])}'")[0]["finance_budget"]
    amount_remaining = monthly_budget
    receipts_current_month = sql.readSQL(f"SELECT * FROM gruettecloud_receipts WHERE username = '{str(session['username'])}' AND MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW()) ORDER BY date DESC")
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
                
    return jsonify({"amount_spent": amount_spent, "amount_remaining": amount_remaining, "percentage_spent": percentage_spent, "receipts": receipts_date})