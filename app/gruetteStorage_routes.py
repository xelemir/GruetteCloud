from flask import render_template, request, redirect, session, Blueprint, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import shutil


from pythonHelper import EncryptionHelper, SQLHelper
from config import url_suffix, templates_path, gruetteStorage_path
    
gruetteStorage_route = Blueprint("GruetteStorage", "GruetteStorage", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()


@gruetteStorage_route.route('/storage', methods=['POST', 'GET'])
def storage():
    if "username" not in session:
        return redirect(f'{url_suffix}/')

    username = str(session['username'])

    sql = SQLHelper.SQLHelper()

    username_database = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{username}'")

    if username_database == []:
        return redirect(f'{url_suffix}/')
    elif not bool(username_database[0]["has_premium"]):
        return redirect(f'{url_suffix}/')

    # Create user directory if it doesn't exist
    user_directory = os.path.join(gruetteStorage_path, username)
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)

    # Get list of files in user directory
    files = os.listdir(user_directory)

    # Calculate total file size
    total_size = sum(os.path.getsize(os.path.join(user_directory, file)) for file in files)

    # Convert file size to human-readable format
    total_size_formatted = get_formatted_file_size(total_size)

    # Create file list with sublists of filename and formatted file size
    file_list = [[file, get_formatted_file_size(os.path.getsize(os.path.join(user_directory, file)))] for file in files]
    total_size_percentage = (total_size / (5 * 1073741824)) * 100  # 5 GB

    return render_template("storage.html", url_suffix=url_suffix, username=username, files=file_list, total_size_formatted=total_size_formatted, total_size_percentage=total_size_percentage)


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



@gruetteStorage_route.route('/upload', methods=['POST'])
def upload():
    if "username" not in session:
        return redirect(f"{url_suffix}/")

    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{str(session['username'])}'")

    if user == []:
        return redirect(f"{url_suffix}/")
    elif not bool(user[0]["has_premium"]):
        return redirect(f"{url_suffix}/premium")

    file = request.files['file']
    if file:
        username = str(session['username'])
        user_directory = os.path.join(gruetteStorage_path, username)
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)
                
        filename = secure_filename(file.filename)
        file.save(os.path.join(user_directory, filename))
        return jsonify({"filename": filename})
    return jsonify({"error": "No file selected!"})

@gruetteStorage_route.route('/download/<username>/<filename>')
def download(username, filename):
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    elif username != str(session['username']):
        return redirect(f"{url_suffix}/")

    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{str(session['username'])}'")

    if user == []:
        return redirect(f"{url_suffix}/")
    elif not bool(user[0]["has_premium"]):
        return redirect(f"{url_suffix}/premium")

    try:
        path = os.path.join(gruetteStorage_path, username, filename)
        return send_file(path, as_attachment=True)
    except:
        return redirect(f"{url_suffix}/storage")

@gruetteStorage_route.route('/deletefile/<username>/<filename>')
def deletefile(username, filename):
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    elif username != str(session['username']):
        return redirect(f"{url_suffix}/")
    
    file_exists = os.path.exists(os.path.join(gruetteStorage_path, username, filename))
    
    if file_exists:
        os.remove(os.path.join(gruetteStorage_path, username, filename))
        
    return redirect(f"{url_suffix}/storage")