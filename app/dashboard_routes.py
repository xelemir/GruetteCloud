import logging
from flask import abort, json, render_template, request, redirect, session, Blueprint, send_file, jsonify
from PIL import Image, ImageDraw, ImageOps
import os
import re
import pyotp
from pywebpush import webpush, WebPushException
import requests

from pythonHelper import EncryptionHelper, SQLHelper, MailHelper, IconHelper, TemplateHelper
from config import templates_path, admin_users, gruettedrive_path, logfiles_path, local_ip, vapid_private_key, aqsense_auth_key
    

dashboard_route = Blueprint("Dashboard", "Dashboard", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()
icon = IconHelper.IconHelper()
th = TemplateHelper.TemplateHelper()


# Helper function to convert file size to human-readable format
def get_formatted_file_size(size):
    """ Gets the formatted file size in KB, MB, GB or TB of a given file size in bytes.

    Args:
        size (int): The file size in bytes.

    Returns:
        str: The formatted file size in KB, MB, GB or TB.
    """    
    # 1 kilobyte (KB) = 1024 bytes
    # 1 megabyte (MB) = 1024 kilobytes
    # 1 gigabyte (GB) = 1024 megabytes
    # 1 terabyte (TB) = 1024 gigabytes

    power = 2 ** 10  # 1024
    n = 0
    power_labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

    while size > power:
        size /= power
        n += 1

    return f"{size:.2f} {power_labels[n]}"

@dashboard_route.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    """ Route to render the admins' dashboard page

    Returns:
        HTML: Rendered HTML page
    """

    if 'user_id' not in session:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()
    
    is_admin = sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"]
    if not bool(is_admin):
        return redirect('/')
    
    status = str(request.args.get('error'))
    if status == "None":
        status = None
    elif status == "otp":
        status = "Invalid OTP, please try again."
    elif status == "no_recipient":
        status = "No recipient specified."
    elif status == "invalid_recipient":
        status = "Invalid recipient specified."
    elif status == "sent":
        status = "Email(s) sent."
    elif status == "no_otp":
        status = "No auth secret found. Make sure you have set up 2FA enabled."
    
    platform_message = sql.readSQL(f"SELECT subject, color FROM platform_notifications")
    if platform_message == []:
        platform_message = None
    else:
        platform_message = {"subject": platform_message[0]["subject"], "color": platform_message[0]["color"]}

    all_users = sql.readSQL(f"SELECT id, username, email, has_premium FROM users")
        
    log_lines = []
    filtered_log_lines = []
    error_log_lines = []
    try:
        with open(f"{logfiles_path}access.log", 'r') as file:
            log_lines = file.read().splitlines()
        log_lines.reverse()

        for entry in log_lines:
            if str(local_ip) not in entry:
                if "python-requests" in entry or "79.222.232.209" in entry or "/static/" in entry:
                    continue
                
                # Match both IPv4 and IPv6 addresses
                date_regex = re.search(r'\[([^\]]+)\]', entry)
                ip_regex = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[a-fA-F0-9:]+:+)+[a-fA-F0-9]+\b', entry)
                
                if date_regex is not None and ip_regex is not None:
                    filtered_log_lines.append({
                        "date": date_regex.group(1),
                        "ip": ip_regex.group(0),
                        "entry": entry.replace(f"[{date_regex.group(1)}]", "").replace(ip_regex.group(0), "")
                    })
                    
        with open(f"{logfiles_path}error.log", 'r') as file:
            error_log_lines = file.read().splitlines()
        error_log_lines.reverse()

    except Exception as e:
        logging.error(e)
        
    return render_template('dashboard.html', user_id=session['user_id'], menu=th.user(session), platform_message=platform_message, all_users=all_users, events=filtered_log_lines, status=status, errors=error_log_lines)

@dashboard_route.route('/dashboard/iplookup', methods=['POST'])
def iplookup():
    if "user_id" not in session:
        return redirect('/')
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return redirect('/')
    
    ip_address = request.json['ip_address']

    response = requests.get(f'http://ip-api.com/json/{ip_address}')
    data = response.json()
        
    return data



@dashboard_route.route('/dashboard/createstatusmessage', methods=['POST'])
def create_status_message():
    """ Post route to create a new status message, which will be displayed on the app

    Returns:
        HTML: Redirect to the dashboard page
    """

    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
    if not is_admin:
        return redirect("/")

    subject = str(request.form["subject"])
    content = str(request.form["content"])
    color = str(request.form["color"])
    link = str(request.form["link"])
    decorator = str(request.form["decorator"])
    
    sql.writeSQL(f"DELETE FROM platform_notifications")
    sql.writeSQL(f"INSERT INTO platform_notifications (subject, content, color, link, decorator) VALUES ('{subject}', '{content}', '{color}', '{link}', '{decorator}')")

    return redirect("/dashboard")

@dashboard_route.route('/dashboard/deletestatusmessage')
def delete_status_message():
    """ Route to delete the current status message

    Returns:
        HTML: Redirect to the dashboard page
    """

    if "user_id" not in session:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()
    
    is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
    if not is_admin:
        return redirect("/")

    sql.writeSQL(f"DELETE FROM platform_notifications")

    return redirect("/dashboard")

@dashboard_route.route('/dashboard/deleteuser/<user_id>')
def delete_user(user_id):
    """ Route to delete a user from the database

    Args:
        user_id (str): The user ID of the user to delete

    Returns:
        HTML: Redirect to the dashboard page
    """

    if 'user_id' not in session:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()
    
    is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
    if not is_admin:
        return redirect("/")

    sql.writeSQL(f"DELETE FROM users WHERE id = '{user_id}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/giftplus/<user_id>')
def gift_plus(user_id):
    """ Route to gift a user GrütteCloud PLUS instantly and for free

    Args:
        user_id (str): The user ID of the user to gift GrütteCloud PLUS to

    Returns:
       HTML: Redirect to the dashboard page
    """

    if 'user_id' not in session:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()
    
    is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
    if not is_admin:
        return redirect("/")

    sql.writeSQL(f"UPDATE users SET has_premium = {True} WHERE id = '{user_id}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/revokeplus/<user_id>')
def revoke_plus(user_id):
    """ Route to revoke a user's GrütteCloud PLUS subscription, even if they paid for it

    Args:
        user_id (str): The user ID of the user to revoke GrütteCloud PLUS from

    Returns:
        HTML: Redirect to the dashboard page
    """

    if 'user_id' not in session:
        return redirect('/')

    sql = SQLHelper.SQLHelper()
    
    is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
    if not is_admin:
        return redirect("/")

    sql.writeSQL(f"UPDATE users SET has_premium = {False} WHERE id = '{user_id}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/sendemail', methods=['POST'])
def send_mail():
    """ Route to send an email to a specific or all users. Requires 2FA.

    Returns:
        HTML: Redirect to the dashboard page
    """
    
    if 'user_id' not in session:
        return redirect('/')
    
    sql = SQLHelper.SQLHelper()
    is_admin = bool(sql.readSQL(f"SELECT is_admin FROM users WHERE id = '{session['user_id']}'")[0]["is_admin"])
    if not is_admin:
        return redirect("/")
    
    email = MailHelper.MailHelper()
    
    recipient_username = str(request.form["username"])
    subject = str(request.form["mail_subject"])
    content = str(request.form["mail_content"])
    otp = str(request.form["otp"])
    send_to_all = False
    if "sendtoall" in request.form:
        send_to_all = True
    
    # Get auth secret from db as users here must be admins
    user = sql.readSQL(f"SELECT 2fa_secret_key FROM users WHERE id = '{session['user_id']}'")
    if user == []:
        return redirect(f'/dashboard')
    try:
        totp = pyotp.TOTP(user[0]["2fa_secret_key"])
    except:
        return redirect(f'/dashboard?error=no_otp')

    # Validate the OTP
    if not totp.verify(otp):
        return redirect(f'/dashboard?error=otp')
    
    if recipient_username == "" and not send_to_all:
        return redirect(f'/dashboard?error=no_recipient')
    
    if not send_to_all:
    
        recipient = sql.readSQL(f"SELECT email, verification_code FROM users WHERE username = '{recipient_username}'")
    
        if recipient == []:
            return redirect(f'/dashboard?error=invalid_recipient')
            
        email.send_email(recipient[0]["email"], recipient_username, subject, content, token=recipient[0]["verification_code"])
        return redirect(f'/dashboard?error=sent')
    
    else:
        for user in sql.readSQL(f"SELECT username, email, receive_emails, verification_code FROM users"):
            if bool(user["receive_emails"]):
                email.send_email(user["email"], user["username"], subject, content, token=user["verification_code"])
                
        return redirect(f'/dashboard?error=sent')
    
@dashboard_route.route("/dashboard/assignticket", methods=["POST"])
def assign_ticket():
    if "user_id" not in session:
        abort(401)
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        abort(401)
    
    ticket_id = request.json["ticket_id"]
    sql.writeSQL(f"UPDATE tickets SET assigned_to = '{session['user_id']}', status = 'in_progress' WHERE id = '{ticket_id}'")
    
    return {"success": True}, 200

@dashboard_route.route("/dashboard/reopenticket", methods=["POST"])
def reopen_ticket():
    if "user_id" not in session:
        abort(401)
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        abort(401)
    
    ticket_id = request.json["ticket_id"]
    sql.writeSQL(f"UPDATE tickets SET status = 'opened', assigned_to = NULL WHERE id = '{ticket_id}'")
    
    return {"success": True}, 200

@dashboard_route.route("/dashboard/closeticket", methods=["POST"])
def close_ticket():
    if "user_id" not in session:
        abort(401)
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        abort(401)
    
    ticket_id = request.json["ticket_id"]
    sql.writeSQL(f"UPDATE tickets SET status = 'closed', assigned_to = '{session['user_id']}' WHERE id = '{ticket_id}'")
    
    return {"success": True}, 200

@dashboard_route.route("/dashboard/giftpremium", methods=["POST"])
def gift_premium():
    if "user_id" not in session:
        abort(401)
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        abort(401)
    
    user_id = request.json["user_id"]
    sql.writeSQL(f"UPDATE users SET has_premium = {True} WHERE id = '{user_id}'")
    
    return {"success": True}, 200

@dashboard_route.route("/get_status_message")
def get_status_message():
    
    sql = SQLHelper.SQLHelper()
    
    platform_message = sql.readSQL(f"SELECT * FROM platform_notifications")
    if platform_message == []:
        platform_message = jsonify({"created_at": None, "content": None, "subject": None, "color": None, "link": None, "decorator": None})
    else:
        platform_message = jsonify({"created_at": platform_message[0]["created_at"], "content": platform_message[0]["content"], "subject": platform_message[0]["subject"], "color": platform_message[0]["color"], "link": platform_message[0]["link"], "decorator": platform_message[0]["decorator"]})
    
    return platform_message

@dashboard_route.route("/dashboard/edit_db_entry", methods=["POST"])
def edit_db_entry():
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)
    
    db_name = request.json["db_name"]
    entry_id = request.json["id"]
    column = request.json["key"]
    value = request.json["value"]
    
    success = sql.writeSQL(f"UPDATE {db_name} SET {column} = '{value}' WHERE id = '{entry_id}'", return_is_successful=True)
    
    return {"success": success}

@dashboard_route.route("/dashboard/executesql", methods=["POST"])
def execute_sql():
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)
    
    query = request.json["query"]
    
    if query.lower().startswith("select") or query.lower().startswith("show"):
        response, success = sql.readSQL(query , return_is_successful=True)
        if success: return jsonify(response), 200
        else: return jsonify({"error": "An error occurred"}), 400
    else:
        success = sql.writeSQL(query, return_is_successful=True)
        if success: return jsonify([]), 200
        else: return jsonify({"error": "An error occurred"}), 400
        
@dashboard_route.route("/dashboard/getTickets", methods=["POST"])
def get_tickets():
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)
    
    tickets = sql.readSQL(f"SELECT * FROM tickets ORDER BY created_at DESC")
    
    for ticket in tickets:
        ticket["created_at"] = ticket["created_at"].strftime("%d.%m.%Y %H:%M:%S")
        
    return jsonify(tickets)

@dashboard_route.route("/dashboard/deleteticket", methods=["POST"])
def delete_ticket():
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)
    
    ticket_id = request.json["ticket_id"]
    
    sql.writeSQL(f"DELETE FROM tickets WHERE id = '{ticket_id}'")
    
    return jsonify({"success": True})

@dashboard_route.route("/dashboard/deleteuser", methods=["POST"])
def deleteuserNew():
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)
    
    user_id = request.json["user_id"]
    
    sql.writeSQL(f"DELETE FROM users WHERE id = '{user_id}'")
    
    return jsonify({"success": True})

@dashboard_route.route("/dashboard/getTicketDetails", methods=["POST"])
def get_ticket_details():
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)
    
    ticket_id = request.json["ticket_id"]
    
    ticket = sql.readSQL(f"SELECT * FROM tickets WHERE id = '{ticket_id}'")[0]
    
    if (ticket["username"] is None or ticket["username"] == "") and (ticket["assigned_to"] is None or ticket["assigned_to"] == ""):
        ticket = sql.readSQL(f"SELECT * FROM tickets WHERE id = '{ticket_id}'")
    elif ticket["username"] is None or ticket["username"] == "":
        ticket = sql.readSQL(f"SELECT * FROM tickets JOIN users AS assigned ON tickets.assigned_to = assigned.id WHERE tickets.id = '{ticket_id}'")
    elif ticket["assigned_to"] is None or ticket["assigned_to"] == "":
        ticket = sql.readSQL(f"SELECT * FROM tickets JOIN users AS author ON tickets.username = author.id WHERE tickets.id = '{ticket_id}'")
        if ticket == []:
            ticket = sql.readSQL(f"SELECT * FROM tickets WHERE id = '{ticket_id}'")
            ticket[0]["author.username"] = ticket[0]["username"] + " (invalid)"
    else:
        ticket = sql.readSQL(f"SELECT * FROM tickets JOIN users AS author ON tickets.username = author.id JOIN users AS assigned ON tickets.assigned_to = assigned.id WHERE tickets.id = '{ticket_id}'")
        if ticket == []:
            ticket = sql.readSQL(f"SELECT * FROM tickets JOIN users AS assigned ON tickets.assigned_to = assigned.id WHERE tickets.id = '{ticket_id}'")
            ticket[0]["author.username"] = ticket[0]["username"] + " (invalid)"
    
    ticket[0]["created_at"] = ticket[0]["created_at"].strftime("%d.%m.%Y %H:%M:%S")
    
    return jsonify(ticket[0])

@dashboard_route.route("/AQSense", methods=["GET"])
def AQSense():
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)
    
    return render_template("AQSense.html")

@dashboard_route.route("/subscribe", methods=["POST"])
def subscribe():
    if "user_id" not in session:
        return abort(401)
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)

    subscription_info = request.json["subscription"]
    sql.writeSQL(f"INSERT INTO push_subscriptions (endpoint, p256dh, auth, user_id) VALUES ('{subscription_info['endpoint']}', '{subscription_info['keys']['p256dh']}', '{subscription_info['keys']['auth']}', {session['user_id']})")
    
    return jsonify({"message": "Subscribed successfully!"}), 201

@dashboard_route.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    if "user_id" not in session:
        return abort(401)
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]
    if not bool(user["is_admin"]):
        return abort(401)

    endpoint = request.json["endpoint"]
    sql.writeSQL(f"DELETE FROM push_subscriptions WHERE endpoint = '{endpoint}'")
    
    return jsonify({"message": "Unsubscribed successfully!"}), 

@dashboard_route.route("/sendpush", methods=["POST"])
def send_push():
    if "authenticity_key" not in request.json or request.json["authenticity_key"] != aqsense_auth_key:
        return abort(401)
        
    sql = SQLHelper.SQLHelper()
    subscription = sql.readSQL(f"SELECT * FROM push_subscriptions")
    
    for sub in subscription:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": {
                        "p256dh": sub["p256dh"],
                        "auth": sub["auth"]
                    }
                },
                data=json.dumps({"title": f"{request.json['title']}", "message": f"{request.json['message']}"}),
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": "mailto:info@gruettecloud.com"},
            )
        except WebPushException as ex:
            print("Error sending notification:", ex)                                                                             
    
    return jsonify({"message": "Push sent successfully!"}), 200