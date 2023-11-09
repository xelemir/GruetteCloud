import datetime
import os
import secrets
from flask import abort, jsonify, render_template, request, redirect, send_file, session, Blueprint, url_for
import requests
from werkzeug.security import generate_password_hash
from geopy.geocoders import Nominatim
from threading import Thread

from pythonHelper import SQLHelper, MailHelper, TemplateHelper, ApartmentHelper
from config import templates_path, openrouteservice_api_key

    
tool_route = Blueprint("Tools", "Tools", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()

@tool_route.route('/logout')
def logout():
    """ Logout route

    Returns:
        str: Redirect to home page
    """    
    session.pop('username', None)
    session.clear()
    return redirect(f'/')

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

@tool_route.route("/apartment", methods=["GET", "POST"])
def apartment():
    sql = SQLHelper.SQLHelper()

    if request.method == "GET":
        items = sql.readSQL("SELECT * FROM gruttecloud_products")
        items = ApartmentHelper.ApartmentHelper().format_items(items)
        
        user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")
        is_admin = bool(user[0]["is_admin"])
        
        return render_template("apartment.html", menu=th.user(session), items=items, is_admin=is_admin)
    
    else:
        total_price = 0
        products = []
        products_string = ""
        for product, price in request.form.items():
            price = int(price.replace("€", ""))
            total_price += price
            products.append({"name": product, "price": price})
            products_string += f"""<tr style="width: 600px; max-width: 70vw; color: #000000;"><td style="width: 50%;">{product}</td><td style="width: 50%;">{price}€</td></tr>"""
        
        if len(products) >= 15 and "username" in session:
            text = f"""
                <div style="background-color: #FFFFFF; padding: 20px; border-radius: 30px; margin-bottom: 20px; margin-top: 20px;">
                    <h2 style="color: #007AFF;">Budget Approved!</h2>
                    <p style="text-wrap: balance">The budget has been approved for the following items:</p>
                    <table style="width: 600px; max-width: 70vw; text-align: left; margin-left: auto; margin-right: auto;">
                        <tr style="color: #007AFF;">
                            <td style="width: 50%;">Item</td>
                            <td style="width: 50%;">Price</td>
                        </tr>
                    </table>
                    <hr style="width: 600px; max-width: 70vw; border: 1px solid #000000; border-radius: 5px; margin: 10px auto;">
                    <table style="width: 600px; max-width: 70vw; text-align: left; margin-left: auto; margin-right: auto;">
                        {products_string}
                    </table>
                    <hr style="width: 600px; max-width: 70vw; border: 1px solid #000000; border-radius: 5px; margin: 10px auto;">
                    <table style="width: 600px; max-width: 70vw; text-align: left; margin-left: auto; margin-right: auto;">
                        <tr style="width: 600px; max-width: 70vw; color: #000000;">
                            <td style="width: 50%;">Total</td>
                            <td id="total-price" style="width: 50%;">{total_price}€</td>
                        </tr>
                    </table>
                </div>

                <div style="background-color: #FFFFFF; padding: 20px; border-radius: 30px; margin-bottom: 20px;">
                    <h2 style="color: #007AFF;">Happy Matchi</h2>
                    <img src="https://www.gruettecloud.com/static/apartment/plushies.jpg" alt="GrütteChat UI" style="height: 300px; width: auto; margin-top: 10px; margin-bottom: 10px; border-radius: 30px;">
                    <p style="text-wrap: balance">Matchi and his friends are happy you approved the budget! Now they can start their journey to their new home!</p>
                </div>
            """
            mail = MailHelper.MailHelper()
            sql = SQLHelper.SQLHelper()
            user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")
            mail.send_email(user[0]["email"], user[0]["username"], "Budget Approved", text, user[0]["verification_code"])
            
            if user[0]["username"] != "jan":
                jan = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = 'jan'")
                mail.send_email(jan[0]["email"], jan[0]["username"], "Budget Approved", text, jan[0]["verification_code"])
        
        return render_template("apartment_approved.html", menu=th.user(session), products=products, total_price=total_price)

@tool_route.route("/search_product/<path:url>", methods=["GET"])
def search_product(url):
    product = ApartmentHelper.ApartmentHelper().search_product(url)
    return jsonify(product)

@tool_route.route("/add_product", methods=["GET", "POST"])
def add_product():
    if "username" not in session:
            return redirect("/")
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")
    if not bool(user[0]["is_admin"]):
        return redirect("/")
        
    if request.method == "GET":
        return render_template("apartment_add_items.html", menu=th.user(session))
    
    else:
        name = request.form["product-name"]
        price = request.form["product-price"]
        url = request.form["product-url"]
        image_src = request.form["product-image"]
        description = request.form["product-description"]
        quantity = request.form["product-quantity"]
        category = request.form["category"]
        
        sql.writeSQL(f"INSERT INTO gruttecloud_products (name, price, url, image_src, description, quantity, category, approved) VALUES ('{name}', '{price}', '{url}', '{image_src}', '{description}', '{quantity}', '{category}', {False})")
        
        return redirect("/apartment#section2")
    
    
@tool_route.route("/apply", methods=["GET", "POST"])
def apply():
    return render_template("apartment_apply.html", menu=th.user(session))


# API Endpoints for GrütteMaps
@tool_route.route("/search_place", methods=["GET"])
def search_place():
    if request.args.get("query") == None:
        return redirect("/")
    
    locations = []
    geolocator = Nominatim(user_agent="https://www.gruettecloud.com/maps")
    
    results = geolocator.geocode(request.args.get("query"), exactly_one=False, limit=5)
    for result in results:
        locations.append(result.raw)
    print(locations)
    return jsonify(locations)
    
@tool_route.route("/nearestNode", methods=["GET"])
def nearestNode():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    
    if lat is None or lon is None:
        abort(400)

    return jsonify([1, lat, lon])

@tool_route.route("/route", methods=["GET"])
def mapsRoute():
    
    start = request.args.get("start")
    end = request.args.get("end")
        
    body = {"coordinates":[[float(start.split(",")[1]), float(start.split(",")[0])], [float(end.split(",")[1]), float(end.split(",")[0])]]}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': openrouteservice_api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }
    response = requests.post('https://api.openrouteservice.org/v2/directions/driving-car/geojson', json=body, headers=headers)
    
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

if __name__ == "__main__":
    search_place()