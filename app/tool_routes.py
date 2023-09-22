import datetime
import os
import secrets
from flask import render_template, request, redirect, send_file, session, Blueprint, url_for
from werkzeug.security import generate_password_hash

from pythonHelper import SQLHelper, MailHelper, TemplateHelper
from config import templates_path

    
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

        mail = MailHelper.MailHelper()
        sql.writeSQL(f"UPDATE gruttechat_users SET receive_emails = {False} WHERE username = '{username}'")
        mail.send_support_mail("Unsubscribed", username, email, f"{username} unsubscribed from communication emails. Reason: {request.form['reason']}")
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
        mail = MailHelper.MailHelper()
        sql.writeSQL(f"UPDATE gruttechat_users SET receive_emails = {True} WHERE username = '{username}'")
        mail.send_support_mail("Resubscribed", username, email, f"{username} changed their mind and resubscribed to communication emails. Please manually gift them GrütteCloud PLUS")
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

@tool_route.route("/support", methods=["GET"])
def support():
    return render_template("support.html", menu=th.user(session))

@tool_route.route("/terms", methods=["GET"])
def terms():
    return render_template("terms.html", menu=th.user(session))

@tool_route.route("/support", methods=["POST"])
def send_support():
    """ Post route to send a support message to the GrütteCloud team

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/")
    
    name = str(request.form["name"])
    username = str(request.form["username"])
    email = str(request.form["mail"])
    message = str(request.form["message"])
    
    mail = MailHelper.MailHelper()
    mail.send_support_mail(name, username, email, message)
    
    return render_template("support.html", menu=th.user(session), error="success")


@tool_route.route("/apartment")
def apartment():
    items = {
        "bedroom": [
            {
                "name": "MALM",
                "price": "329€",
                "description": "Bettgestell hoch mit 2 Schubladen, 140cm x 200cm, weiß",
                "img": "https://www.ikea.com/de/de/images/products/malm-bettgestell-hoch-mit-2-schubkaesten-weiss-lindbaden__1101597_pe866769_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/malm-bettgestell-hoch-mit-2-schubkaesten-weiss-lindbaden-s59494995/",
            },
            {
                "name": "ÅKREHAMN",
                "price": "349€",
                "description": "Matratze, mittelfest, weiß, 140cm x 200cm",
                "img": "https://www.ikea.com/de/de/images/products/akrehamn-schaummatratze-mittelfest-weiss__1062618_pe851029_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/akrehamn-schaummatratze-mittelfest-weiss-30481644/",
            },
            {
                "name": "RUMSMALVA x2",
                "price": "13€",
                "description": "Kissen, ergonomisch, 40cm x 80cm, weiß, 2 Stück",
                "img": "https://www.ikea.com/de/de/images/products/rumsmalva-kissen-erg-seiten-rueckenschlaefer__0778781_pe759130_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/rumsmalva-kissen-erg-seiten-rueckenschlaefer-60446753/",
            },
            {
                "name": "SMÅSPORRE",
                "price": "23€",
                "description": "Bettdecke, mittelwarm, 140cm x 200cm",
                "img": "https://www.ikea.com/de/de/images/products/smasporre-decke-mittelwarm__0776665_pe758186_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/smasporre-decke-mittelwarm-00457004/",
            },
            {
                "name": "BERGPALM",
                "price": "40€",
                "description": "Bettwäscheset, 2-teilig, grün, Streifen, 140cm x 200cm",
                "img": "https://www.ikea.com/de/de/images/products/bergpalm-bettwaesche-set-2-teilig-gruen-streifen__0718512_pe731562_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/bergpalm-bettwaesche-set-2-teilig-gruen-streifen-20423211/",
            },
            {
                "name": "NORDKISA",
                "price": "299€",
                "description": "Kleiderschrank offen, Schiebetür, Bambus",
                "img": "https://www.ikea.com/de/de/images/products/nordkisa-kleiderschrank-offen-schiebetuer-bambus__0813677_ph165857_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/nordkisa-kleiderschrank-offen-schiebetuer-bambus-00439468/",
            },
            {
                "name": "KALLAX 2x3",
                "price": "65€",
                "description": "Regal, weiß",
                "img": "https://www.ikea.com/de/de/images/products/kallax-regal-weiss__1143200_pe881437_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/kallax-regal-weiss-90522420/",
            },
            {
                "name": "ENUDDEN",
                "price": "6€",
                "description": "Haken für Tür, weiß",
                "img": "https://www.ikea.com/de/de/images/products/enudden-aufhaenger-fuer-tuer-weiss__0863273_pe654879_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/enudden-aufhaenger-fuer-tuer-weiss-80251730/",
            },
            {
                "name": "IKORNNES",
                "price": "149€",
                "description": "Standspiegel, Esche",
                "img": "https://www.ikea.com/de/de/images/products/ikornnes-standspiegel-esche__0858773_pe658292_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/ikornnes-standspiegel-esche-30298396/",
            },
            {
                "name": "LAUTERS",
                "price": "70€",
                "description": "Standleuchte, Esche, weiß, E27 (nicht enthalten)",
                "img": "https://www.ikea.com/de/de/images/products/lauters-standleuchte-esche-weiss__0879908_pe714870_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/lauters-standleuchte-esche-weiss-30405042/",
            },
            {
                "name": "BRANÄS",
                "price": "54€",
                "description": "Korb, Rattan, passend für KALLAX",
                "img": "https://www.ikea.com/de/de/images/products/branaes-korb-rattan__0418392_pe575458_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/branaes-korb-rattan-00138432/",
            },
            {
                "name": "SKÅDIS",
                "price": "45€",
                "description": "Lochplatte, Kombination, weiß, Schrauben nicht enthalten",
                "img": "https://www.ikea.com/de/de/images/products/skadis-lochplatte-kombination__0964306_pe808972_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/skadis-lochplatte-kombination-s89406365/",
            },
            {
                "name": "BUMERANG",
                "price": "3€",
                "description": "Kleiderbügel, naturfarben",
                "img": "https://www.ikea.com/de/de/images/products/bumerang-kleiderbuegel-naturfarben__0942812_pe796632_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/bumerang-kleiderbuegel-naturfarben-60489083/",
            },
        ],
        "livingroom": [
            {
                "name": "LANDSKRONA",
                "price": "599€",
                "description": "2er-Sofa, Gunnared hellgrün, Holz",
                "img": "https://www.ikea.com/de/de/images/products/landskrona-2er-sofa-gunnared-hellgruen-holz__0828967_pe680176_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/landskrona-2er-sofa-gunnared-hellgruen-holz-s39270289/",
            },
            {
                "name": "DAGLYSA",
                "price": "199€",
                "description": "Couchtisch, Eichenfurnier",
                "img": "https://www.ikea.com/de/de/images/products/daglysa-tisch-eichenfurnier__0871261_pe680260_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/daglysa-tisch-eichenfurnier-50402288/",
            },
            {
                "name": "JOKKMOKK",
                "price": "120€",
                "description": "Stuhl, Antikbeize, 4 Stück",
                "img": "https://www.ikea.com/de/de/images/products/jokkmokk-stuhl-antikbeize__0870916_pe716638_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/jokkmokk-stuhl-antikbeize-90342688/",
            },
            {
                "name": "LAUTERS",
                "price": "70€",
                "description": "Standleuchte, Esche, weiß, E27 (nicht enthalten)",
                "img": "https://www.ikea.com/de/de/images/products/lauters-standleuchte-esche-weiss__0879908_pe714870_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/lauters-standleuchte-esche-weiss-30405042/",
            },
            {
                "name": "BESTÅ",
                "price": "204€",
                "description": "TV-Bank mit Türen, weiß, Lappviken weiß",
                "img": "https://www.ikea.com/de/de/images/products/besta-tv-bank-mit-tueren-weiss-lappviken-weiss__0995908_pe821978_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/besta-tv-bank-mit-tueren-weiss-lappviken-weiss-s89330691/",
            },
            {
                "name": "MALINDA",
                "price": "28€",
                "description": "Stuhlkissen, dunkelgrün",
                "img": "https://www.ikea.com/de/de/images/products/malinda-stuhlkissen-dunkelgruen__1138169_pe879870_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/malinda-stuhlkissen-dunkelgruen-50551061/",
            },
        ],
        "sanitary": [
            {
                "name": "RÅGRUND",
                "price": "50€",
                "description": "Regal, Bambus",
                "img": "https://www.ikea.com/de/de/images/products/ragrund-regal-bambus__0250172_pe379441_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/ragrund-regal-bambus-30253067/",
            },
        ],
        "other": [
            {
                "name": "OMAR",
                "price": "40€",
                "description": "Schuhregal, verzinkt",
                "img": "https://www.ikea.com/de/de/images/products/omar-regal-verzinkt__0650980_pe706616_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/omar-regal-verzinkt-10069763/",
            },
            {
                "name": "BAGGMUCK",
                "price": "5€",
                "description": "Schuhmatte, drinnen/draußen, grau",
                "img": "https://www.ikea.com/de/de/images/products/baggmuck-schuhmatte-drinnen-draussen-grau__0909542_pe610213_s5.jpg?f=xl",
                "url": "https://www.ikea.com/de/de/p/baggmuck-schuhmatte-drinnen-draussen-grau-60329711/",
            },
            {
                "name": "KULLEN",
                "price": "69€",
                "description": "Kommode mit 6 Schubladen, weiß",
                "img": "https://www.ikea.com/de/de/images/products/kullen-kommode-mit-6-schubladen-weiss__0778050_pe758820_s5.jpg",
                "url": "https://www.ikea.com/de/de/p/kullen-kommode-mit-6-schubladen-weiss-90309245/",
            },
        ],
    }
        
    
    return render_template("apartment.html", menu=th.user(session), items=items)