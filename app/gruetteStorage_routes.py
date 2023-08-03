import datetime
from flask import render_template, request, redirect, session, Blueprint, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import shutil
import random
import string

from pythonHelper import EncryptionHelper, SQLHelper
from pythonHelper import IconHelper
from config import url_prefix, templates_path, gruetteStorage_path, admin_users
    
gruetteStorage_route = Blueprint("GruetteStorage", "GruetteStorage", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()
icon = IconHelper.IconHelper()


@gruetteStorage_route.route('/storage', methods=['POST', 'GET'])
def storage():
    if "username" not in session:
        return redirect(f'/')

    username = str(session['username'])

    sql = SQLHelper.SQLHelper()

    username_database = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")

    if username_database == []:
        # Security check: Username is invalid and should be deleted. This may happen if the user was deleted from the database.
        return redirect(f'/logout')
    elif not bool(username_database[0]["has_premium"]):
        return redirect(f'/premium')

    files = get_files(username)
    file_list = files["file_list"]
    
    return render_template("storage.html", url_prefix=url_prefix, username=username, files=file_list, total_size_formatted=files["total_size_formatted"], total_size_percentage=files["total_size_percentage"], status=None, verified=bool(username_database[0]["is_verified"]), is_admin=bool(username_database[0]["is_admin"]))


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

def get_files(username):
    # Create user directory if it doesn't exist
    user_directory = os.path.join(gruetteStorage_path, username)
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    
    # Create user shared directory if it doesn't exist
    user_shared_directory = os.path.join(gruetteStorage_path, username, "shared")
    if not os.path.exists(user_shared_directory):
        os.makedirs(user_shared_directory)
        
    # Create user YouTube directory if it doesn't exist
    user_yt_directory = os.path.join(gruetteStorage_path, username, "YouTube") 
    if not os.path.exists(user_yt_directory):
        os.makedirs(user_yt_directory)   

    # Get list of files in user directory and remove shared directory
    files = os.listdir(user_directory)
    files.remove("shared")
    files.remove("YouTube")
    
    # Calculate file size of user directory
    size_user = sum(os.path.getsize(os.path.join(user_directory, file)) for file in files)

    # Get list of files in shared directory
    files_shared = os.listdir(user_shared_directory)
    
    # Get list of files in YouTube directory
    files_yt = os.listdir(user_yt_directory)
    
    # Calculate file size of shared directory
    size_shared = sum(os.path.getsize(os.path.join(user_shared_directory, file)) for file in files_shared)
    
    # Calculate file size of YouTube directory
    size_yt = sum(os.path.getsize(os.path.join(user_yt_directory, file)) for file in files_yt)
    
    # Convert file size to human-readable format
    total_size = size_user + size_shared + size_yt
    total_size_formatted = get_formatted_file_size(total_size)
    total_size_percentage = (total_size / (5 * 1073741824)) * 100  # 5 GB

    # Create file list with sublists of filename and formatted file size and sharing status
    file_list_user = [[file, get_formatted_file_size(os.path.getsize(os.path.join(user_directory, file))), "private"] for file in files]
    file_list_shared = [[file, get_formatted_file_size(os.path.getsize(os.path.join(user_shared_directory, file))), "shared"] for file in files_shared]
    file_list_yt = [[file, get_formatted_file_size(os.path.getsize(os.path.join(user_yt_directory, file))), "youtube"] for file in files_yt]
    file_list = file_list_shared + file_list_yt + file_list_user
    
    return {"file_list": file_list, "total_size_formatted": total_size_formatted, "total_size_percentage": total_size_percentage}
    
@gruetteStorage_route.route('/upload', methods=['POST'])
def upload():
    if "username" not in session:
        return redirect(f"/")
    
    username = str(session['username'])

    if request.method == 'POST':
        sql = SQLHelper.SQLHelper()
        user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{str(session['username'])}'")

        if user == []:
            return redirect(f"/")
        elif not bool(user[0]["has_premium"]):
            return redirect(f"/premium")

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

@gruetteStorage_route.route("/open/<username>/<filename>/<preview>")
def download(username, filename, preview="Default"):
    if "username" not in session or username != str(session['username']):
        if os.path.exists(os.path.join(gruetteStorage_path, username, "shared", filename)):
            path = os.path.join(gruetteStorage_path, username, "shared", filename)
        else:
            return redirect(f"/storage")
    elif username == str(session['username']):
        if os.path.exists(os.path.join(gruetteStorage_path, username, filename)):
            path = os.path.join(gruetteStorage_path, username, filename)
        elif os.path.exists(os.path.join(gruetteStorage_path, username, "shared", filename)):
            path = os.path.join(gruetteStorage_path, username, "shared", filename)
        elif os.path.exists(os.path.join(gruetteStorage_path, username, "YouTube", filename)):
            path = os.path.join(gruetteStorage_path, username, "YouTube", filename)
        else:
            return redirect(f"/storage")
    
    if path is not None:
        if preview == "preview":
            return send_file(path, as_attachment=False)
        else:
            return send_file(path, as_attachment=True)
    else:
        return redirect(f"/storage")

@gruetteStorage_route.route("/delete/<username>/<filename>")
def delete(username, filename):
    if "username" not in session or username != str(session['username']):
        return redirect(f"/")
        
    if os.path.exists(os.path.join(gruetteStorage_path, username, filename)):
        os.remove(os.path.join(gruetteStorage_path, username, filename))
    elif os.path.exists(os.path.join(gruetteStorage_path, username, "shared", filename)):
        os.remove(os.path.join(gruetteStorage_path, username, "shared", filename))
    elif os.path.exists(os.path.join(gruetteStorage_path, username, "YouTube", filename)):
        os.remove(os.path.join(gruetteStorage_path, username, "YouTube", filename))
        
    return redirect(f"/storage")

@gruetteStorage_route.route("/file/<username>/<filename>")
def file(username, filename):
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT is_verified FROM gruttechat_users WHERE username = '{str(username)}'")
    if user == []:
        return redirect(f"/")
    
    if "username" not in session or username != str(session['username']):
        shared_file = os.path.join(gruetteStorage_path, username, "shared", filename)
        if os.path.exists(shared_file):
            filesize = get_formatted_file_size(os.path.getsize(shared_file))
            created_at = datetime.datetime.fromtimestamp(os.path.getctime(shared_file)).strftime("%d.%m.%Y")
            icon_path = IconHelper.IconHelper().get_icon(filename)
            code = "https://www.gruettecloud.com/s/" + str(SQLHelper.SQLHelper().readSQL(f"SELECT link_id FROM gruttestorage_links WHERE owner='{username}' AND filename='{filename}'")[0]["link_id"])
            return render_template("fileinfo.html", url_prefix=url_prefix, username=username, filename=filename, filesize=filesize, created_at=created_at, is_author=False, is_shared=True, file_icon=icon_path, link_id=code, is_gruettecloud_user=False, is_author_verified=user[0]["is_verified"], is_youtube_video=False)
        else:
            return redirect(f"/storage")
        
    if os.path.exists(os.path.join(gruetteStorage_path, username, filename)):
        path = os.path.join(gruetteStorage_path, username, filename)
        is_shared = False
        is_youtube_video = False
        code = ""
    elif os.path.exists(os.path.join(gruetteStorage_path, username, "shared", filename)):
        path = os.path.join(gruetteStorage_path, username, "shared", filename)
        is_shared = True
        is_youtube_video = False
        code = "https://www.gruettecloud.com/s/" + str(SQLHelper.SQLHelper().readSQL(f"SELECT link_id FROM gruttestorage_links WHERE owner='{username}' AND filename='{filename}'")[0]["link_id"])
    elif os.path.exists(os.path.join(gruetteStorage_path, username, "YouTube", filename)):
        path = os.path.join(gruetteStorage_path, username, "YouTube", filename)
        is_shared = False
        is_youtube_video = True
        code = ""
    else:
        return redirect(f"/storage")
    
    filesize = get_formatted_file_size(os.path.getsize(path))
    created_at = datetime.datetime.fromtimestamp(os.path.getctime(path)).strftime("%d.%m.%Y")
    icon_path = IconHelper.IconHelper().get_icon(filename)
    
    is_author_verified = False
    if username in admin_users:
        is_author_verified = True
    return render_template("fileinfo.html", url_prefix=url_prefix, username=username, filename=filename, filesize=filesize, created_at=created_at, is_author=True, is_shared=is_shared, file_icon=icon_path, link_id=code, is_gruettecloud_user=True, is_author_verified=user[0]["is_verified"], is_youtube_video=is_youtube_video)
    

@gruetteStorage_route.route("/share/<username>/<filename>")
def share(username, filename):
    if "username" not in session or username != str(session['username']):
        return redirect(f"/storage")

    sql = SQLHelper.SQLHelper()
    user_shared_directory = os.path.join(gruetteStorage_path, username, "shared")
    
    # If the file is not already in the shared directory, move it there
    if not os.path.exists(os.path.join(user_shared_directory, filename)):
        if os.path.exists(os.path.join(gruetteStorage_path, username, filename)):
            shutil.move(os.path.join(gruetteStorage_path, username, filename), os.path.join(user_shared_directory, filename))
            
            not_new_code = True
            while not_new_code:
                code = ''.join(random.choice(string.ascii_letters) for _ in range(5))
                if sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id ='{code}'") == []:
                    not_new_code = False
            sql.writeSQL(f"INSERT INTO gruttestorage_links (owner, link_id, filename) VALUES ('{username}', '{code}', '{filename}')")
                        
        else:
            return redirect(f"/storage")
    
    return redirect(f"/file/{username}/{filename}")

@gruetteStorage_route.route("/stopsharing/<username>/<filename>")
def stopsharing(username, filename):
    if "username" not in session or username != str(session['username']):
        return redirect(f"/storage")
    
    sql = SQLHelper.SQLHelper()
    
    try:
        user_shared_directory = os.path.join(gruetteStorage_path, username, "shared")
        if os.path.exists(user_shared_directory):
            shutil.move(os.path.join(user_shared_directory, filename), os.path.join(gruetteStorage_path, username, filename))
            sql.writeSQL(f"DELETE FROM gruttestorage_links WHERE owner='{username}' AND filename='{filename}'")
    except:
        return redirect(f"/file/{username}/{filename}")
        
    return redirect(f"/file/{username}/{filename}")

@gruetteStorage_route.route("/s/<code>")
def shared(code):
    sql = SQLHelper.SQLHelper()
    result = sql.readSQL(f"SELECT owner, filename FROM gruttestorage_links WHERE link_id ='{code}'")
    if result == []:
        return redirect(f"/")

    username = result[0]["owner"]
    filename = result[0]["filename"]
    
    return redirect(f"/file/{username}/{filename}")