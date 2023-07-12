import datetime
from flask import render_template, request, redirect, session, Blueprint, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import shutil


from pythonHelper import EncryptionHelper, SQLHelper
from config import url_prefix, templates_path, gruetteStorage_path
    
gruetteStorage_route = Blueprint("GruetteStorage", "GruetteStorage", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()


@gruetteStorage_route.route('/storage', methods=['POST', 'GET'])
def storage():
    if "username" not in session:
        return redirect(f'{url_prefix}/')

    username = str(session['username'])

    sql = SQLHelper.SQLHelper()

    username_database = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{username}'")

    if username_database == []:
        return redirect(f'{url_prefix}/')
    elif not bool(username_database[0]["has_premium"]):
        return redirect(f'{url_prefix}/')

    files = get_files(username)
    
    file_list = files["file_list"]
    #file_list.extend([["test1.txt", "1 TB", "private"], ["test2.txt", "1 TB", "private"], ["test3.txt", "1 TB", "shared"], ["test4.txt", "1 TB", "private"], ["test5.txt", "1 TB", "private"], ["test6.txt", "1 TB", "shared"]])
    #file_list.extend([["test1.txt", "1 TB", "private"], ["test2.txt", "1 TB", "private"], ["test3.txt", "1 TB", "shared"], ["test4.txt", "1 TB", "private"], ["test5.txt", "1 TB", "private"], ["test6.txt", "1 TB", "shared"]])
    #file_list.extend([["test1.txt", "1 TB", "private"], ["test2.txt", "1 TB", "private"], ["test3.txt", "1 TB", "shared"], ["test4.txt", "1 TB", "private"], ["test5.txt", "1 TB", "private"], ["test6.txt", "1 TB", "shared"]])
    #file_list.extend([["test1.txt", "1 TB", "private"], ["test2.txt", "1 TB", "private"], ["test3.txt", "1 TB", "shared"], ["test4.txt", "1 TB", "private"], ["test5.txt", "1 TB", "private"], ["test6.txt", "1 TB", "shared"]])

    return render_template("storage.html", url_prefix=url_prefix, username=username, files=file_list, total_size_formatted=files["total_size_formatted"], total_size_percentage=files["total_size_percentage"], status=None)


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

    # Get list of files in user directory and remove shared directory
    files = os.listdir(user_directory)
    files.remove("shared")
    
    # Calculate file size of user directory
    size_user = sum(os.path.getsize(os.path.join(user_directory, file)) for file in files)

    # Get list of files in shared directory
    files_shared = os.listdir(user_shared_directory)
    
    # Calculate file size of shared directory
    size_shared = sum(os.path.getsize(os.path.join(user_shared_directory, file)) for file in files_shared)
    
    

    # Convert file size to human-readable format
    total_size = size_user + size_shared
    total_size_formatted = get_formatted_file_size(total_size)
    total_size_percentage = (total_size / (5 * 1073741824)) * 100  # 5 GB

    # Create file list with sublists of filename and formatted file size and sharing status
    file_list_user = [[file, get_formatted_file_size(os.path.getsize(os.path.join(user_directory, file))), "private"] for file in files]
    file_list_shared = [[file, get_formatted_file_size(os.path.getsize(os.path.join(user_shared_directory, file))), "shared"] for file in files_shared]
    file_list = file_list_shared + file_list_user
    
    return {"file_list": file_list, "total_size_formatted": total_size_formatted, "total_size_percentage": total_size_percentage}
    

@gruetteStorage_route.route('/upload', methods=['POST', 'GET'])
def upload():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    username = str(session['username'])

    if request.method == 'POST':
        sql = SQLHelper.SQLHelper()
        user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{str(session['username'])}'")

        if user == []:
            return redirect(f"{url_prefix}/")
        elif not bool(user[0]["has_premium"]):
            return redirect(f"{url_prefix}/premium")

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
    else:
        files = get_files(str(session['username']))
        file_list = files["file_list"]
        return render_template("storage.html", url_prefix=url_prefix, username=username, files=file_list, total_size_formatted=files["total_size_formatted"], total_size_percentage=files["total_size_percentage"], status="File successfully uploaded!")


@gruetteStorage_route.route("/download/<username>/<filename>/<preview>")
def download(username, filename, preview=False):
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    elif username != str(session['username']):
        return redirect(f"{url_prefix}/")

    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{str(session['username'])}'")

    if user == []:
        return redirect(f"{url_prefix}/")
    elif not bool(user[0]["has_premium"]):
        return redirect(f"{url_prefix}/premium")

    try:
        path = os.path.join(gruetteStorage_path, username, filename)
        if preview == "preview":
            return send_file(path, as_attachment=False)
        else:
            return send_file(path, as_attachment=True)
    except:
        return redirect(f"{url_prefix}/storage")

@gruetteStorage_route.route("/deletefile/<username>/<filename>")
def deletefile(username, filename):
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    elif username != str(session['username']):
        return redirect(f"{url_prefix}/")
        
    if os.path.exists(os.path.join(gruetteStorage_path, username, filename)):
        os.remove(os.path.join(gruetteStorage_path, username, filename))
    elif os.path.exists(os.path.join(gruetteStorage_path, username, "shared", filename)):
        os.remove(os.path.join(gruetteStorage_path, username, "shared", filename))
        
    return redirect(f"{url_prefix}/storage")

@gruetteStorage_route.route("/file/<username>/<filename>")
def file(username, filename):
    if "username" not in session or username != str(session['username']):
        shared_file = os.path.join(gruetteStorage_path, username, "shared", filename)
        if os.path.exists(shared_file):
            filesize = get_formatted_file_size(os.path.getsize(shared_file))
            created_at = datetime.datetime.fromtimestamp(os.path.getctime(shared_file)).strftime("%d.%m.%Y at %H:%M:%S")
            return render_template("shared.html", url_prefix=url_prefix, username=username, filename=filename, filesize=filesize, created_at=created_at, is_author=False, is_shared=True)
        else:
            return redirect(f"{url_prefix}/storage")
        
    if os.path.exists(os.path.join(gruetteStorage_path, username, filename)):
        path = os.path.join(gruetteStorage_path, username, filename)
        is_shared = False
    elif os.path.exists(os.path.join(gruetteStorage_path, username, "shared", filename)):
        path = os.path.join(gruetteStorage_path, username, "shared", filename)
        is_shared = True
    else:
        return redirect(f"{url_prefix}/storage")
    
    filesize = get_formatted_file_size(os.path.getsize(path))
    created_at = datetime.datetime.fromtimestamp(os.path.getctime(path)).strftime("%d.%m.%Y at %H:%M:%S")
        
    return render_template("shared.html", url_prefix=url_prefix, username=username, filename=filename, filesize=filesize, created_at=created_at, is_author=True, is_shared=is_shared)
    

@gruetteStorage_route.route("/share/<username>/<filename>")
def share(username, filename):
    if "username" not in session or username != str(session['username']):
        return redirect(f"{url_prefix}/storage")

    # Create user shared directory if it doesn't exist
    user_shared_directory = os.path.join(gruetteStorage_path, username, "shared")
    if not os.path.exists(user_shared_directory):
        os.makedirs(user_shared_directory)
    
    # If the file is not already in the shared directory, copy it there
    if not os.path.exists(os.path.join(user_shared_directory, filename)):
        if os.path.exists(os.path.join(gruetteStorage_path, username, filename)):
            shutil.move(os.path.join(gruetteStorage_path, username, filename), os.path.join(user_shared_directory, filename))
        else:
            return redirect(f"{url_prefix}/storage")
    
    return redirect(f"{url_prefix}/file/{username}/{filename}")

@gruetteStorage_route.route("/downloadshared/<username>/<filename>/<preview>")
def downloadshared(username, filename, preview=False):
    try:
        shared_file = os.path.join(gruetteStorage_path, username, "shared", filename)
        if os.path.exists(shared_file):
            path = os.path.join(gruetteStorage_path, username, "shared", filename)
            if preview == "preview":
                return send_file(path, as_attachment=False)
            else:
                return send_file(path, as_attachment=True)
        else:
            return redirect(f"{url_prefix}/storage")
    except:
        return redirect(f"{url_prefix}/storage")
    
@gruetteStorage_route.route("/stopsharing/<username>/<filename>")
def stopsharing(username, filename):
    if "username" not in session or username != str(session['username']):
        return redirect(f"{url_prefix}/storage")

    user_shared_directory = os.path.join(gruetteStorage_path, username, "shared")
    if os.path.exists(user_shared_directory):
        shutil.move(os.path.join(user_shared_directory, filename), os.path.join(gruetteStorage_path, username, filename))
        
    return redirect(f"{url_prefix}/file/{username}/{filename}")