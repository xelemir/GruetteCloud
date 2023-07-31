import os
import datetime
import platform
import pyotp
from flask import jsonify, render_template, request, redirect, send_file, session, Blueprint

from pythonHelper import SQLHelper, EncryptionHelper, MailHelper, YouTubeHelper
from config import url_prefix, templates_path, admin_users, gruetteStorage_path

    
utilities_route = Blueprint("Utilities", "Utilities", template_folder=templates_path)

@utilities_route.route('/chat/delete/<recipient>')
def delete_chat(recipient):
    """ Delete chat route

    Args:
        recipient (str): The chat to delete

    Returns:
        str: Redirect to home page
    """    
    if 'username' not in session:
        return redirect(f'{url_prefix}/')

    username = str(session['username'])
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"DELETE FROM gruttechat_messages WHERE username_send = '{username}' AND username_receive = '{recipient}' OR username_send = '{recipient}' AND username_receive = '{username}'")
    return redirect(f'{url_prefix}/')

@utilities_route.route('/logout')
def logout():
    """ Logout route

    Returns:
        str: Redirect to home page
    """    
    session.pop('username', None)
    return redirect(f'{url_prefix}/')

@utilities_route.route("/settings", methods=["GET", "POST"])
def settings(error=None):
    """ Settings route

    Args:
        error (string, optional): An error message to display. Defaults to None.

    Returns:
        str: The template to render
    """    
    if "username" not in session:
        return redirect(f"{url_prefix}/")

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
        
    if bool(user[0]["is_2fa_enabled"]) == True and user[0]["2fa_secret_key"] != '0':
        
        # Create the Google Authenticator OTP instance
        totp = pyotp.TOTP(user[0]["2fa_secret_key"])

        # Generate the QR code image
        provisioning_uri = totp.provisioning_uri(username, issuer_name="GrütteCloud")
        """qr = qrcode.make(provisioning_uri)
        qr_image_data = io.BytesIO()
        qr.save(qr_image_data, format='PNG')
        qr_image_base64 = base64.b64encode(qr_image_data.getvalue()).decode('utf-8')
        is_two_fa_enabled = True"""
        totp_now = totp.now()
        provisioning_uri = totp.provisioning_uri(username, issuer_name="GrütteCloud")
        
        return render_template("settings.html", verified=verified, username=username, error=error, selected_personality=selected_personality, has_premium=has_premium, url_prefix=url_prefix, is_two_fa_enabled=True, qr_code_data=provisioning_uri, otp=totp_now)
        
        
    else:
        is_two_fa_enabled = False
        qr_image_base64 = None
        totp_now = None
        
    return render_template("settings.html", verified=verified, username=username, error=error, selected_personality=selected_personality, has_premium=has_premium, url_prefix=url_prefix, is_two_fa_enabled=is_two_fa_enabled, qr_code=qr_image_base64, otp=totp_now)

@utilities_route.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    if request.method == "GET":
        return redirect(f"{url_prefix}/settings")
    
    username = str(session["username"])
    verified = False
    if username in admin_users:
        verified = True

    sql = SQLHelper.SQLHelper()
    eh = EncryptionHelper.EncryptionHelper()
    selected_personality = "Default"
    new_password = str(request.form["new_password"])
    old_password = str(request.form["old_password"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return render_template("settings.html", verified=verified, username=username, error="Something went wrong on our end :/", selected_personality=selected_personality, has_premium=False, url_prefix=url_prefix)
    else:
        selected_personality = user[0]["ai_personality"]
        
    if len(new_password) > 40 or len(new_password) < 8:
        return render_template('settings.html', error='Password must be between 8 and 40 characters', selected_personality=selected_personality, has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)
    
    password = eh.decrypt_message(str(user[0]["password"]))
    if password != old_password:
        return render_template("settings.html", verified=verified, username=username, error="Passwords aren't matching!", selected_personality=selected_personality, has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)
    else:
        encrypt_new_password = eh.encrypt_message(str(new_password))
        sql.writeSQL(f"UPDATE gruttechat_users SET password = '{str(encrypt_new_password)}' WHERE username = '{str(session['username'])}'")

    return render_template("settings.html", verified=verified, username=username, error="Password changed successfully!", selected_personality=selected_personality, has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)

@utilities_route.route("/change_email", methods=["GET", "POST"])
def change_email():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    if request.method == "GET":
        return redirect(f"{url_prefix}/settings")
    
    username = str(session["username"])
    verified = False
    if username in admin_users:
        verified = True
    sql = SQLHelper.SQLHelper()
    eh = EncryptionHelper.EncryptionHelper()
    new_email = str(request.form["new_email"])
    password_form = str(request.form["password"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    

    if user == []:
        return render_template("settings.html", verified=verified, username=username, error="Something went wrong on our end :/", selected_personality="Default", has_premium=False, url_prefix=url_prefix)
    else:
        if "@" not in new_email or "." not in new_email:
            return render_template("settings.html", verified=verified, username=username, error="Please enter a valid email address!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)

        password = eh.decrypt_message(str(user[0]["password"]))
        if password_form != password:
            return render_template("settings.html", verified=verified, username=username, error="Passwords aren't matching!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)
        else:
            sql.writeSQL(f"UPDATE gruttechat_users SET email = '{str(new_email)}' WHERE username = '{str(session['username'])}'")

        return render_template("settings.html", verified=verified, username=username, error="Email changed successfully!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)
    
@utilities_route.route("/change_ai_personality/<ai_personality>", methods=["GET"])
def change_ai_personality(ai_personality):
    if "username" not in session:
        return redirect(f"{url_prefix}/")

    username = str(session["username"])
    verified = False
    if username in admin_users:
        verified = True
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
        
    if user == []:
        return render_template("settings.html", verified=verified, username=username, error="Something went wrong on our end :/", selected_personality="Default", has_premium=False, url_prefix=url_prefix)
    elif bool(user[0]["has_premium"]) == True:
        sql.writeSQL(f"UPDATE gruttechat_users SET ai_personality = '{str(ai_personality)}' WHERE username = '{str(session['username'])}'")
        return render_template("settings.html", verified=verified, username=username, error=f"MyAI is set to {ai_personality}", selected_personality=ai_personality, has_premium=True, display_back_to_ai=True, url_prefix=url_prefix)
    else:
        return render_template("settings.html", verified=verified, username=username, error="Please purchase GrütteCloud PLUS to change your MyAI personality!", selected_personality="Default", has_premium=False, url_prefix=url_prefix)
        
@utilities_route.route("/ai-preferences", methods=["GET"])
def ai_preferences():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    username = str(session["username"])
    verified = False
    if username in admin_users:
        verified = True
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return render_template("settings.html", verified=verified, username=username, error="Something went wrong on our end :/", selected_personality="Default", has_premium=False, url_prefix=url_prefix)
    else:
        return render_template("settings.html", verified=verified, username=username, selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), display_back_to_ai=True, url_prefix=url_prefix)
        
@utilities_route.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    if request.method == "GET":
        return redirect(f"{url_prefix}/settings")
    
    sql = SQLHelper.SQLHelper()
    eh = EncryptionHelper.EncryptionHelper()
    username_session = str(session["username"])
    username_form = str(request.form["username"])
    password_form = str(request.form["password"])
    email_form = str(request.form["email"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username_session}'")
    verified = False
    if username_session in admin_users:
        verified = True
        
    if user == []:
        return render_template("settings.html", verified=verified, username=username_session, error="Something went wrong on our end :/", selected_personality="Default", has_premium=False, url_prefix=url_prefix)
    
    username_db = user[0]["username"]
    password_db = eh.decrypt_message(str(user[0]["password"]))
    email_db = user[0]["email"]
    
    if username_db == username_form and password_db == password_form and email_db == email_form:
        sql.writeSQL(f"DELETE FROM gruttechat_users WHERE username = '{str(username_session)}'")
        session.pop('username', None)
        return redirect(f'{url_prefix}/')
    elif username_db != username_form:
        return render_template("settings.html", verified=verified, username=username_session, error="Username isn't matching!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)
    elif password_db != password_form:
        return render_template("settings.html", verified=verified, username=username_session, error="Password isn't matching!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)
    elif email_db != email_form:
        return render_template("settings.html", verified=verified, username=username_session, error="Email isn't matching!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_prefix=url_prefix)

@utilities_route.route("/help", methods=["GET"])
def help():
    return render_template("help.html", url_prefix=url_prefix)
        
@utilities_route.route("/about", methods=["GET"])
def about():
    return render_template("about.html", url_prefix=url_prefix)

@utilities_route.route("/privacy", methods=["GET"])
def privacy():
    return render_template("privacy.html", url_prefix=url_prefix)

@utilities_route.route("/support", methods=["GET"])
def support():
    return render_template("support.html", url_prefix=url_prefix)

@utilities_route.route("/aboutus", methods=["GET"])
def aboutus():
    return render_template("aboutus.html", url_prefix=url_prefix)

@utilities_route.route("/terms", methods=["GET"])
def terms():
    return render_template("terms.html", url_prefix=url_prefix)

@utilities_route.route("/support", methods=["POST"])
def send_support():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    name = str(request.form["name"])
    username = str(request.form["username"])
    email = str(request.form["mail"])
    message = str(request.form["message"])
    
    mail = MailHelper.MailHelper()
    mail.send_support_mail(name, username, email, message)
    
    return render_template("support.html", error="Your message has been sent!", url_prefix=url_prefix)

@utilities_route.route("/youtube", methods=["GET", "POST"])
def download_from_youtube():
    if "username" not in session:
        return redirect(f"{url_prefix}/")

    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{str(session['username'])}'")

    if user == []:
        return redirect(f"{url_prefix}/")
    elif not bool(user[0]["has_premium"]):
        return redirect(f"{url_prefix}/premium")

    if request.method == "GET":
        
        return render_template("youtube.html", url_prefix=url_prefix)
    elif request.method == "POST":
        try:
            video_url = str(request.form["video_url"])
            youtube = YouTubeHelper.YouTubeHelper(url=video_url)
        except:
            return jsonify({"error": "Something went wrong on our end :/"})
            
        youtube.download(username=str(session["username"]))
        video_id = youtube.get_media_title()
        return jsonify({"filename": video_id})

@utilities_route.route("/2fa/enable")
def enable_2fa():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT is_2fa_enabled, 2fa_secret_key FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    if user == []:
        return redirect(f"{url_prefix}/")
    
    if user[0]["2fa_secret_key"] == '0' and bool(user[0]["is_2fa_enabled"]):
        # If 2fa is enabled but the secret key is 0, generate a new secret key
        two_fa_secret_key = str(pyotp.random_base32())
        sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {True}, 2fa_secret_key = '{two_fa_secret_key}' WHERE username = '{str(session['username'])}'")
        return redirect(f"{url_prefix}/settings")
    
    elif bool(user[0]["is_2fa_enabled"]):
        return redirect(f"{url_prefix}/settings")
    elif user[0]["2fa_secret_key"] != '0':
        sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {True} WHERE username = '{str(session['username'])}'")
        return redirect(f"{url_prefix}/settings")
    if user[0]["2fa_secret_key"] == '0':
        return redirect(f"{url_prefix}/settings")
    
    else:
        two_fa_secret_key = str(pyotp.random_base32())
        sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {True}, 2fa_secret_key = '{two_fa_secret_key}' WHERE username = '{str(session['username'])}'")
        return redirect(f"{url_prefix}/settings")

@utilities_route.route("/2fa/disable")
def disable_2fa():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    sql = SQLHelper.SQLHelper()
    
    sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {False} WHERE username = '{str(session['username'])}'")
    
    return redirect(f"{url_prefix}/settings")

@utilities_route.route("/2fa/refresh")
def refresh_2fa():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT is_2fa_enabled, 2fa_secret_key FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return redirect(f"{url_prefix}/")
    elif bool(user[0]["is_2fa_enabled"]) == False:
        return redirect(f"{url_prefix}/settings")
    else:
        two_fa_secret_key = str(pyotp.random_base32())
        sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {True}, 2fa_secret_key = '{two_fa_secret_key}' WHERE username = '{str(session['username'])}'")
        return redirect(f"{url_prefix}/settings")