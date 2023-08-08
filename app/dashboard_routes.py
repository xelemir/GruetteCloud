import subprocess
from flask import render_template, request, redirect, session, Blueprint, send_file, jsonify

import os
import re
import pyotp

from pythonHelper import EncryptionHelper, SQLHelper
from pythonHelper import MailHelper
from pythonHelper import IconHelper
from config import templates_path, admin_users, gruetteStorage_path, logfiles_path, local_ip
    

dashboard_route = Blueprint("Dashboard", "Dashboard", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()
icon = IconHelper.IconHelper()

# Helper function to convert file size to human-readable format
def get_formatted_file_size(size):
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
    if 'username' not in session:
        return redirect(f'/')
    elif session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()
    
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
    
    platform_message = sql.readSQL(f"SELECT subject, color FROM gruttechat_platform_messages")
    if platform_message == []:
        platform_message = None
    else:
        platform_message = {"subject": platform_message[0]["subject"], "color": platform_message[0]["color"]}
    
    used_space_unformatted = sum(os.path.getsize(os.path.join(gruetteStorage_path, item)) for item in os.listdir(gruetteStorage_path))
    used_space = get_formatted_file_size(used_space_unformatted)
    used_space_percent = (used_space_unformatted / (8 * 1073741824)) * 100  # 8 GB

    all_users = sql.readSQL(f"SELECT username, email, has_premium FROM gruttechat_users")
        
    log_lines = []
    filtered_log_lines = []
    try:
        with open(f"{logfiles_path}access.log", 'r') as file:
            log_lines = file.read().splitlines()
        log_lines.reverse()

        for entry in log_lines:
            if str(local_ip) not in entry:
                date_regex = re.search(r'\[([^\]]+)\]', entry)
                ip_regex = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', entry)
                if date_regex is not None:
                    filtered_log_lines.append({"date": date_regex.group(1), "ip": ip_regex.group(0), "entry": entry.replace(f"[{date_regex.group(1)}]", "").replace(ip_regex.group(0), "")})
    except:
        pass
    
    return render_template('dashboard.html', username=session['username'], used_space=used_space, used_space_percent=used_space_percent, platform_message=platform_message, all_users=all_users, events=filtered_log_lines, status=status)

@dashboard_route.route('/dashboard/createstatusmessage', methods=['POST'])
def create_status_message():
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')
    
    sql = SQLHelper.SQLHelper()

    subject = str(request.form["subject"])
    content = str(request.form["content"])
    color = str(request.form["color"])

    sql.writeSQL(f"DELETE FROM gruttechat_platform_messages")
    sql.writeSQL(f"INSERT INTO gruttechat_platform_messages (subject, content, color) VALUES ('{subject}', '{content}', '{color}')")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/deletestatusmessage')
def delete_status_message():
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"DELETE FROM gruttechat_platform_messages")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/deleteuser/<username>')
def delete_user(username):
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"DELETE FROM gruttechat_users WHERE username = '{username}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/giftplus/<username>')
def gift_plus(username):
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {True} WHERE username = '{username}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/revokeplus/<username>')
def revoke_plus(username):
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {False} WHERE username = '{username}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/sendemail', methods=['POST'])
def send_mail():
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')
    
    email = MailHelper.MailHelper()
    sql = SQLHelper.SQLHelper()
    
    recipient_username = str(request.form["username"])
    subject = str(request.form["subject"])
    content = str(request.form["content"])
    otp = str(request.form["otp"])
    send_to_all = False
    if "sendtoall" in request.form:
        send_to_all = True
    
    # Get auth secret from db as users here must be admins
    user = sql.readSQL(f"SELECT 2fa_secret_key FROM gruttechat_users WHERE username = '{session['username']}'")
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
    
        recipient = sql.readSQL(f"SELECT email FROM gruttechat_users WHERE username = '{recipient_username}'")
    
        if recipient == []:
            return redirect(f'/dashboard?error=invalid_recipient')
        else:
            recipient_email = recipient[0]["email"]
            
        email.send_email(recipient_email, recipient_username, subject, content)
        return redirect(f'/dashboard?error=sent')
    
    else:
        for user in sql.readSQL(f"SELECT username, email, receive_emails FROM gruttechat_users"):
            if bool(user["receive_emails"]):
                email.send_email(user["email"], user["username"], subject, content)
                
        return redirect(f'/dashboard?error=sent')