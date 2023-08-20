import os
import datetime
import platform
import pyotp
from flask import jsonify, render_template, request, redirect, send_file, session, Blueprint, url_for

from pythonHelper import SQLHelper, EncryptionHelper, MailHelper, TemplateHelper
from config import templates_path, admin_users, gruetteStorage_path

    
utilities_route = Blueprint("Utilities", "Utilities", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()

@utilities_route.route('/chat/delete/<recipient>')
def delete_chat(recipient):
    """ Delete chat route

    Args:
        recipient (str): The chat to delete

    Returns:
        str: Redirect to home page
    """    
    if 'username' not in session:
        return redirect(f'/')

    username = str(session['username'])
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"DELETE FROM gruttechat_messages WHERE username_send = '{username}' AND username_receive = '{recipient}' OR username_send = '{recipient}' AND username_receive = '{username}'")
    return redirect(f'/chat')

@utilities_route.route('/logout')
def logout():
    """ Logout route

    Returns:
        str: Redirect to home page
    """    
    session.pop('username', None)
    return redirect(f'/')

@utilities_route.route("/settings", methods=["GET", "POST"])
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

        totp_now = totp.now()
        provisioning_uri = totp.provisioning_uri(f" {username}", issuer_name="GrütteCloud")
        
        return render_template("settings.html", menu=th.user(session), verified=verified, username=username, error=error, selected_personality=selected_personality, has_premium=has_premium, is_two_fa_enabled=True, qr_code_data=provisioning_uri, otp=totp_now)
 
    else:
        is_two_fa_enabled = False
        qr_image_base64 = None
        totp_now = None
        
    return render_template("settings.html", menu=th.user(session), verified=verified, username=username, error=error, selected_personality=selected_personality, has_premium=has_premium, is_two_fa_enabled=is_two_fa_enabled, qr_code=qr_image_base64, otp=totp_now)

@utilities_route.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect(f"/")
    if request.method == "GET":
        return redirect(f"/settings")
    
    username = str(session["username"])

    sql = SQLHelper.SQLHelper()
    eh = EncryptionHelper.EncryptionHelper()
    new_password = str(request.form["new_password"])
    old_password = str(request.form["old_password"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return redirect(url_for("Utilities.settings", error="error"))
    
        
    if len(new_password) > 40 or len(new_password) < 8:
        return redirect(url_for("Utilities.settings", error="password_length_error"))
    
    password = eh.decrypt_message(str(user[0]["password"]))
    if password != old_password:
        return redirect(url_for("Utilities.settings", error="not_matching_password"))
    else:
        encrypt_new_password = eh.encrypt_message(str(new_password))
        sql.writeSQL(f"UPDATE gruttechat_users SET password = '{str(encrypt_new_password)}' WHERE username = '{str(session['username'])}'")

    return redirect(url_for("Utilities.settings", error="password_changed"))

@utilities_route.route("/change_email", methods=["GET", "POST"])
def change_email():
    if "username" not in session:
        return redirect(f"/")
    if request.method == "GET":
        return redirect(f"/settings")
    
    username = str(session["username"])
    sql = SQLHelper.SQLHelper()
    eh = EncryptionHelper.EncryptionHelper()
    new_email = str(request.form["new_email"])
    password_form = str(request.form["password"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return redirect(url_for("Utilities.settings", error="error"))
    else:
        if "@" not in new_email or "." not in new_email:
            return redirect(url_for("Utilities.settings", error="email_not_valid"))

        password = eh.decrypt_message(str(user[0]["password"]))
        if password_form != password:
            return redirect(url_for("Utilities.settings", error="not_matching_password"))
        else:
            sql.writeSQL(f"UPDATE gruttechat_users SET email = '{str(new_email)}' WHERE username = '{str(session['username'])}'")

        return redirect(url_for("Utilities.settings", error="email_changed"))
    
@utilities_route.route("/change_ai_personality/<ai_personality>", methods=["GET"])
def change_ai_personality(ai_personality):
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
        
@utilities_route.route("/ai-preferences", methods=["GET"])
def ai_preferences():
    if "username" not in session:
        return redirect(f"/")
    
    username = str(session["username"])
    verified = False
    if username in admin_users:
        verified = True
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    if user == []:
        return redirect(url_for("Utilities.settings", error="error"))
    else:
        return render_template("settings.html", menu=th.user(session), verified=verified, username=username, selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), display_back_to_ai=True)
        
@utilities_route.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if "username" not in session:
        return redirect(f"/")
    if request.method == "GET":
        return redirect(f"/settings")
    
    sql = SQLHelper.SQLHelper()
    eh = EncryptionHelper.EncryptionHelper()
    username_session = str(session["username"])
    username_form = str(request.form["username"])
    password_form = str(request.form["password"])
    email_form = str(request.form["email"])
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username_session}'")
        
    if user == []:
        return redirect(url_for("Utilities.settings", error="error"))
    
    username_db = user[0]["username"]
    password_db = eh.decrypt_message(str(user[0]["password"]))
    email_db = user[0]["email"]
    
    if username_db == username_form and password_db == password_form and email_db == email_form:
        sql.writeSQL(f"DELETE FROM gruttechat_users WHERE username = '{str(username_session)}'")
        session.pop('username', None)
        return redirect(f'/')
    elif username_db != username_form:
        return redirect(url_for("Utilities.settings", error="not_matching_username"))
    elif password_db != password_form:
        return redirect(url_for("Utilities.settings", error="not_matching_password"))
    elif email_db != email_form:
        return redirect(url_for("Utilities.settings", error="not_matching_email"))

@utilities_route.route("/help", methods=["GET"])
def help():
    return render_template("help.html", menu=th.user(session))
        
@utilities_route.route("/about", methods=["GET"])
def about():
    return render_template("about.html", menu=th.user(session))

@utilities_route.route("/discover", methods=["GET"])
def discover():
    return render_template("discover.html", menu=th.user(session))

@utilities_route.route("/privacy", methods=["GET"])
def privacy():
    return render_template("privacy.html", menu=th.user(session))

@utilities_route.route("/support", methods=["GET"])
def support():
    return render_template("support.html", menu=th.user(session))

@utilities_route.route("/terms", methods=["GET"])
def terms():
    return render_template("terms.html", menu=th.user(session))

@utilities_route.route("/support", methods=["POST"])
def send_support():
    if "username" not in session:
        return redirect(f"/")
    
    name = str(request.form["name"])
    username = str(request.form["username"])
    email = str(request.form["mail"])
    message = str(request.form["message"])
    
    mail = MailHelper.MailHelper()
    mail.send_support_mail(name, username, email, message)
    
    return render_template("support.html", menu=th.user(session), error="Your message has been sent!")

@utilities_route.route("/2fa/enable")
def enable_2fa():
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

@utilities_route.route("/2fa/disable")
def disable_2fa():
    if "username" not in session:
        return redirect(f"/")
    
    sql = SQLHelper.SQLHelper()
    
    sql.writeSQL(f"UPDATE gruttechat_users SET is_2fa_enabled = {False} WHERE username = '{str(session['username'])}'")
    
    return redirect(f"/settings")

@utilities_route.route("/2fa/refresh")
def refresh_2fa():
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
    
@utilities_route.route("/resubscribe")
def resubscribe():
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
        # Gift the user GrütteCloud PLUS
        sql.writeSQL(f"UPDATE gruttechat_users SET receive_emails = {True}, has_premium = {True} WHERE username = '{username}'")
        return render_template("unsubscribe.html", menu=th.user(session), username=username, email=email, token=token, mode="resubscribe")
    
@utilities_route.route("/unsubscribe", methods=["GET", "POST"])
def unsubscribe():
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
        sql.writeSQL(f"UPDATE gruttechat_users SET receive_emails = {False} WHERE username = '{username}'")
        return render_template("unsubscribe.html", menu=th.user(session), username=username, email=email, token=token, mode="unsubscribe_confirmed")