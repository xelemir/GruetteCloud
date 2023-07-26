from flask import render_template, request, redirect, session, Blueprint, send_file, jsonify

import os

from pythonHelper import EncryptionHelper, SQLHelper
from pythonHelper import IconHelper
from config import url_prefix, templates_path, admin_users, gruetteStorage_path, logfiles_path, local_ip
    
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
        return redirect(f'{url_prefix}/')
    elif session['username'] not in admin_users:
        return redirect(f'{url_prefix}/')

    sql = SQLHelper.SQLHelper()
    
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
    with open(f"{logfiles_path}access.log", 'r') as file:
        log_lines = file.read().splitlines()
    log_lines.reverse()

    for entry in log_lines:
        if str(local_ip) not in entry:
            filtered_log_lines.append(entry)
    
    return render_template('dashboard.html', url_prefix=url_prefix, username=session['username'], used_space=used_space, used_space_percent=used_space_percent, platform_message=platform_message, all_users=all_users, events=filtered_log_lines)

@dashboard_route.route('/dashboard/createstatusmessage', methods=['POST'])
def create_status_message():
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'{url_prefix}/')

    sql = SQLHelper.SQLHelper()

    subject = str(request.form["subject"])
    content = str(request.form["content"])
    color = str(request.form["color"])

    sql.writeSQL(f"DELETE FROM gruttechat_platform_messages")
    sql.writeSQL(f"INSERT INTO gruttechat_platform_messages (subject, content, color) VALUES ('{subject}', '{content}', '{color}')")

    return redirect(f'{url_prefix}/dashboard')

@dashboard_route.route('/dashboard/deletestatusmessage')
def delete_status_message():
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'{url_prefix}/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"DELETE FROM gruttechat_platform_messages")

    return redirect(f'{url_prefix}/dashboard')

@dashboard_route.route('/dashboard/deleteuser/<username>')
def delete_user(username):
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'{url_prefix}/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"DELETE FROM gruttechat_users WHERE username = '{username}'")

    return redirect(f'{url_prefix}/dashboard')

@dashboard_route.route('/dashboard/giftplus/<username>')
def gift_plus(username):
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'{url_prefix}/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {True} WHERE username = '{username}'")

    return redirect(f'{url_prefix}/dashboard')

@dashboard_route.route('/dashboard/revokeplus/<username>')
def revoke_plus(username):
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'{url_prefix}/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {False} WHERE username = '{username}'")

    return redirect(f'{url_prefix}/dashboard')