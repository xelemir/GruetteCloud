import logging
import os
import datetime
import platform
import random
import secrets
import pyotp
from flask import jsonify, render_template, request, redirect, send_file, session, Blueprint, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image


from pythonHelper import SQLHelper, MailHelper, TemplateHelper
from config import templates_path, admin_users, pfp_path

    
settings_route = Blueprint("Settings", "Settings", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()

@settings_route.route("/settings", methods=["GET", "POST"])
def settings(error=None):
    """ Settings route

    Args:
        error (string, optional): An error message to display. Defaults to None.

    Returns:
        str: The template to render
    """    
    if "username" not in session:
        return redirect(f"/")

    error = request.args.get("error")
    if error == "error":
        error = "Something went wrong on our end :/"
    elif error == "password_length_error":
        error = "Your password must between 8 and 40 characters long."
    elif error == "not_matching_password":
        error = "Your password is incorrect."
    elif error == "password_changed":
        error = "Your password has been changed."
    elif error == "email_not_valid":
        error = "Your email is not valid."
    elif error == "email_changed":
        error = "Your email has been changed."
    elif error == "not_matching_username":
        error = "Your username is incorrect."
    elif error == "not_matching_email":
        error = "Your email is incorrect."
    elif error == "already_unsubscribed":
        error = "You are already unsubscribed."
    elif error == "unsubscribed":
        error = "You have been unsubscribed."
    elif error == "pfp_wrong_format":
        error = "Your profile picture must be a .png file."
    elif error == "pfp_changed":
        error = "Your profile picture has been changed."
    elif error == "payment_cancelled":
        error = "Your payment has been cancelled."
    elif error == "payment_failed":
        error = "Your payment has failed."
    elif error == "payment_success":
        error = "You unlocked GrütteCloud PLUS!"
    elif error == "already_premium":
        error = "You already have GrütteCloud PLUS!"
    elif error == "payment_creation_failed":
        error = "Payment creation failed. Please try again."
    elif error == "username_less_40":
        error = "Your username must be less than 40 characters."
    elif error == "forbidden_words":
        error = "Your username contains forbidden words."
    elif error == "username_already_exists":
        error = "This username is already taken."
    elif error == "username_changed":
        error = "Your username has been changed."
    
    username = str(session["username"])
    verified = False
    if username in admin_users:
        verified = True
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")

    if user == []:
        error="Something went wrong on our end :/"
        selected_personality="Default"
        has_premium = False
    else:
        selected_personality = user[0]["ai_personality"]
        has_premium = bool(user[0]["has_premium"])
        created_at = user[0]["created_at"].strftime("%d.%m.%Y")
        
    if bool(user[0]["is_2fa_enabled"]) == True and user[0]["2fa_secret_key"] != '0':
        
        # Create the Google Authenticator OTP instance
        totp = pyotp.TOTP(user[0]["2fa_secret_key"])

        totp_now = totp.now()
        provisioning_uri = totp.provisioning_uri(f" {username}", issuer_name="GrütteCloud")
        
        return render_template("settings.html", created_at=created_at, email=user[0]["email"], menu=th.user(session), verified=verified, username=username, error=error, selected_personality=selected_personality, has_premium=has_premium, is_two_fa_enabled=True, qr_code_data=provisioning_uri, otp=totp_now, admin=user[0]["is_admin"])
 
    else:
        is_two_fa_enabled = False
        qr_image_base64 = None
        totp_now = None
        
    return render_template("settings.html", created_at=created_at, email=user[0]["email"], menu=th.user(session), verified=verified, username=username, error=error, selected_personality=selected_personality, has_premium=has_premium, is_two_fa_enabled=is_two_fa_enabled, qr_code=qr_image_base64, otp=totp_now, admin=user[0]["is_admin"])

@settings_route.route("/change_pfp", methods=["POST"])
def change_pfp():
    """ Post route to change the user's profile picture
        The image is cropped to a square and resized to 540x540 pixels
        before being saved publicly on the server

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    username = str(session["username"])

    if "profilePicture" not in request.files:
        return redirect(f"/profile/{username}")
    
    file = request.files["profilePicture"]
    filename = file.filename
    file_extension = filename.split(".")[-1]
    
    id_not_found = False
    while not id_not_found:
        potential_id = str(random.randint(10000000, 99999999))
        if not os.path.exists(os.path.join(pfp_path, f"{potential_id}.png")):
            filename = potential_id
            sql.writeSQL(f"UPDATE gruttechat_users SET profile_picture = '{filename}' WHERE username = '{str(session['username'])}'")
            id_not_found = True
            
    file.save(os.path.join(pfp_path, f"{filename}.{file_extension}"))
    
    try:
        # Open the input image
        with Image.open(os.path.join(pfp_path, f"{filename}.{file_extension}")) as img:
            # Determine the cropping region
            aspect_ratio = img.width / img.height
            if aspect_ratio > 1:
                # Landscape or square image, crop the center
                crop_start = (img.width - img.height) // 2
                img = img.crop((crop_start, 0, crop_start + img.height, img.height))
            elif aspect_ratio < 1:
                # Portrait image, crop top and bottom
                crop_start = (img.height - img.width) // 2
                img = img.crop((0, crop_start, img.width, crop_start + img.width))

            # Resize the cropped image to the target size
            img = img.resize((540, 540), Image.ANTIALIAS)

            # Ensure the output image is in JPG format
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save the converted image
            img.save(os.path.join(pfp_path, f"{filename}.png"), "png")
            # Remove the original image
            if file_extension != "png":
                img.close()
                os.remove(os.path.join(pfp_path, f"{filename}.{file_extension}"))
            
    except Exception as e:
        logging.error(e)
        return redirect(f"/settings")
                
    return redirect(f"/settings")

@settings_route.route("/remove_pfp")
def remove_pfp():
    """ Route to remove the user's profile picture
        The a randomly selected default picture is assigned to the user
        TODO: Right now, the old profile picture is not deleted from the server 

    Returns:
        _type_: _description_
    """

    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    sql.writeSQL(f"UPDATE gruttechat_users SET profile_picture = '{random.choice(['blue', 'green', 'purple', 'red', 'yellow'])}' WHERE username = '{str(session['username'])}'")
    return redirect(f"/settings")

@settings_route.route("/change_password", methods=["POST"])
def change_password():
    """ Post route to change the user's password

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/")

    sql = SQLHelper.SQLHelper()
    new_password = str(request.form["new_password"])
    old_password = str(request.form["old_password"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return redirect(url_for("Settings.settings", error="error"))
    
        
    if len(new_password) > 40 or len(new_password) < 8:
        return redirect(url_for("Settings.settings", error="password_length_error"))
    
    if not check_password_hash(user[0]["password"], old_password):
        return redirect(url_for("Settings.settings", error="not_matching_password"))
    else:
        sql.writeSQL(f"UPDATE gruttechat_users SET password = '{generate_password_hash(new_password)}' WHERE username = '{str(session['username'])}'")

    return redirect(url_for("Settings.settings", error="password_changed"))

@settings_route.route("/change_email", methods=["POST"])
def change_email():
    """ Post route to change the user's email

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/")
    
    sql = SQLHelper.SQLHelper()
    new_email = str(request.form["new_email"])
    password_form = str(request.form["password"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return redirect(url_for("Settings.settings", error="error"))
    else:
        if "@" not in new_email or "." not in new_email:
            return redirect(url_for("Settings.settings", error="email_not_valid"))

        if not check_password_hash(user[0]["password"], password_form):
            return redirect(url_for("Settings.settings", error="not_matching_password"))
        else:
            sql.writeSQL(f"UPDATE gruttechat_users SET email = '{str(new_email)}' WHERE username = '{str(session['username'])}'")

        return redirect(url_for("Settings.settings", error="email_changed"))
    
@settings_route.route("/change_username", methods=["POST"])
def change_username():
    """ Post route to change the user's username

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    new_username = str(request.form["new_username"])
    password_form = str(request.form["password"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    all_users = sql.readSQL(f"SELECT username FROM gruttechat_users")
    all_users_list = [x["username"].lower() for x in all_users]

    if user == []:
        return redirect(url_for("Settings.settings", error="error"))
    else:
        if len(new_username) > 40:
            return redirect(url_for("Settings.settings", error="username_less_40"))
        elif new_username.lower() in ['gruette', 'grütte', 'grutte', 'admin', 'support', 'delete', 'administrator', 'moderator', 'mod', 'gruettecloudrenders', 'gruettecloud', 'grüttecloud', 'gruettechat', 'grüttechat']:
            return redirect(url_for("Settings.settings", error="forbidden_words"))
        elif new_username.lower() in all_users_list:
            return redirect(url_for("Settings.settings", error="username_already_exists"))
        
        if not check_password_hash(user[0]["password"], password_form):
            return redirect(url_for("Settings.settings", error="not_matching_password"))
        else:
            sql.writeSQL(f"UPDATE gruttechat_users SET username = '{str(new_username)}' WHERE username = '{str(session['username'])}'")
            sql.writeSQL(f"UPDATE gruttechat_messages SET username_send = '{str(new_username)}' WHERE username_send = '{str(session['username'])}'")
            sql.writeSQL(f"UPDATE gruttechat_messages SET username_receive = '{str(new_username)}' WHERE username_receive = '{str(session['username'])}'")
            sql.writeSQL(f"UPDATE gruttestorage_links SET owner = '{str(new_username)}' WHERE owner = '{str(session['username'])}'")
            session["username"] = new_username
        return redirect(url_for("Settings.settings", error="username_changed"))

    
@settings_route.route("/change_ai_personality/<ai_personality>", methods=["GET"])
def change_ai_personality(ai_personality):
    """ Route to change the user's MyAI personality

    Args:
        ai_personality (str): The personality to change to

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/")

    username = str(session["username"])
    verified = False
    if username in admin_users:
        verified = True
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
        
    if user == []:
        return render_template("settings.html", menu=th.user(session), verified=verified, username=username, error="Something went wrong on our end :/", selected_personality="Default", has_premium=False)
    elif bool(user[0]["has_premium"]) == True:
        sql.writeSQL(f"UPDATE gruttechat_users SET ai_personality = '{str(ai_personality)}' WHERE username = '{str(session['username'])}'")
        session.pop("chat_history", None)
        return render_template("settings.html", menu=th.user(session), verified=verified, username=username, error=f"MyAI is set to {ai_personality}", selected_personality=ai_personality, has_premium=True, display_back_to_ai=True)
    else:
        return render_template("settings.html", menu=th.user(session), verified=verified, username=username, error="Please purchase GrütteCloud PLUS to change your MyAI personality!", selected_personality="Default", has_premium=False)
        
@settings_route.route("/ai-preferences", methods=["GET"])
def ai_preferences():
    """ Route to change the user's MyAI preferences
        TODO: This currently just renders Settings page with "back to MyAI button". must be solved differently in the future

    Returns:
        HTML: Rendered HTML page
    """    
    if "username" not in session:
        return redirect(f"/")
    
    username = str(session["username"])
    verified = False
    if username in admin_users:
        verified = True
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return redirect(url_for("Settings.settings", error="error"))
    else:
        return render_template("settings.html", menu=th.user(session), verified=verified, username=username, selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), display_back_to_ai=True)
        
@settings_route.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    """ Post route to delete the user's account

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/")
    if request.method == "GET":
        return redirect(f"/settings")
    
    sql = SQLHelper.SQLHelper()
    username_session = str(session["username"])
    username_form = str(request.form["username"])
    password_form = str(request.form["password"])
    email_form = str(request.form["email"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username_session}'")
        
    if user == []:
        return redirect(url_for("Settings.settings", error="error"))
    
    username_db = user[0]["username"]
    email_db = user[0]["email"]
            
    if username_db != username_form:
        return redirect(url_for("Settings.settings", error="not_matching_username"))
    elif not check_password_hash(user[0]["password"], password_form):
        return redirect(url_for("Settings.settings", error="not_matching_password"))
    elif email_db != email_form:
        return redirect(url_for("Settings.settings", error="not_matching_email"))
    else:
        sql.writeSQL(f"DELETE FROM gruttechat_users WHERE username = '{str(username_session)}'")
        session.pop('username', None)
        return redirect(f'/')

@settings_route.route("/2fa/enable")
def enable_2fa():
    """ Route to enable 2fa
        A new secret key is generated and saved in the database if the user does not have one yet

    Returns:
        HTML: Rendered HTML page
    """    
    if "username" not in session:
        return redirect(f"/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT is_2fa_enabled, 2fa_secret_key FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    if user == []:
        return redirect(f"/")
    
    if user[0]["2fa_secret_key"] == '0' and bool(user[0]["is_2fa_enabled"]):
        # If 2fa is enabled but the secret key is 0, generate a new secret key
        two_fa_secret_key = str(pyotp.random_base32())
        sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {True}, 2fa_secret_key = '{two_fa_secret_key}' WHERE username = '{str(session['username'])}'")
        return redirect(f"/settings")
    
    elif bool(user[0]["is_2fa_enabled"]):
        return redirect(f"/settings")
    elif user[0]["2fa_secret_key"] != '0':
        sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {True} WHERE username = '{str(session['username'])}'")
        return redirect(f"/settings")
    else:
        two_fa_secret_key = str(pyotp.random_base32())
        sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {True}, 2fa_secret_key = '{two_fa_secret_key}' WHERE username = '{str(session['username'])}'")
        return redirect(f"/settings")

@settings_route.route("/2fa/disable")
def disable_2fa():
    """ Route to disable 2fa
        The old key is however not deleted from the database, so the user can re-enable 2fa with the same key

    Returns:
        HTML: Rendered HTML page
    """    
    if "username" not in session:
        return redirect(f"/")
    
    sql = SQLHelper.SQLHelper()
    
    sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {False} WHERE username = '{str(session['username'])}'")
    
    return redirect(f"/settings")

@settings_route.route("/2fa/refresh")
def refresh_2fa():
    """ Route to refresh the user's 2fa secret key
        A new secret key is generated and saved in the database, e.g. if the user lost their old key

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT is_2fa_enabled, 2fa_secret_key FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return redirect(f"/")
    elif bool(user[0]["is_2fa_enabled"]) == False:
        return redirect(f"/settings")
    else:
        two_fa_secret_key = str(pyotp.random_base32())
        sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {True}, 2fa_secret_key = '{two_fa_secret_key}' WHERE username = '{str(session['username'])}'")
        return redirect(f"/settings")
    

