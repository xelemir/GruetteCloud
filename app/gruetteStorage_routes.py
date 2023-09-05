import datetime
import json
from flask import abort, render_template, request, redirect, session, Blueprint, send_file, jsonify, url_for
from werkzeug.utils import secure_filename
import os
import shutil
import random
import string

from pythonHelper import EncryptionHelper, SQLHelper, YouTubeHelper, TemplateHelper
from pythonHelper import IconHelper
from config import templates_path, gruetteStorage_path
    
gruetteStorage_route = Blueprint("GruetteStorage", "GruetteStorage", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()
ih = IconHelper.IconHelper()
th = TemplateHelper.TemplateHelper()

@gruetteStorage_route.route('/storage', methods=['POST', 'GET'])
def storage():
    """ Route to GrütteStorage home view

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f'/')

    username = str(session['username'])

    sql = SQLHelper.SQLHelper()

    username_database = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")

    if username_database == []:
        # Security check: Username is invalid and should be deleted. This may happen if the user was deleted from the database.
        return redirect(f'/logout')

    files = get_files(username)
    file_list = files["file_list"]
    
    return render_template("storage.html", menu=th.user(session), username=username, files=file_list, size_formatted=files["size_formatted"], size_percentage=files["size_percentage"], status=None, has_premium=bool(username_database[0]["has_premium"]), verified=bool(username_database[0]["is_verified"]), is_admin=bool(username_database[0]["is_admin"]))


def get_formatted_file_size(size):
    """ Get the formatted file size in bytes, kilobytes, megabytes, gigabytes or terabytes, based on input size in bytes

    Args:
        size (int): Size in bytes

    Returns:
        str: Formatted file size
    """

    # 1 kilobyte (KB) = 1024 bytes
    # 1 megabyte (MB) = 1024 kilobytes
    # 1 gigabyte (GB) = 1024 megabytes
    # 1 terabyte (TB) = 1024 gigabytes

    power_labels = ['B', 'KB', 'MB', 'GB', 'TB']
    n = 0

    while size >= 1024 and n < len(power_labels) - 1:
        size /= 1024
        n += 1

    return f"{size:.2f} {power_labels[n]}"


def get_total_file_size(directory):
    total_size = 0

    # Walk through the directory and its subdirectories
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
            except OSError:
                # Handle permission issues, file not found, etc.
                pass

    return total_size


def get_files(username, folder_dir=None):
    """ Get all files of a user

    Args:
        username (str): Username of the user

    Returns:
        dict: Dictionary containing the file list, the formatted size and the size percentage
    """

    sql = SQLHelper.SQLHelper()
    
    storage_dir = os.path.join(gruetteStorage_path, username)
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    
    if folder_dir != None:
        sub_dir = folder_dir.split("/")
        sub_dir.insert(0, username)
        sub_dir.insert(0, gruetteStorage_path)
        storage_dir = os.path.join(*sub_dir)

    files = os.listdir(storage_dir)
    if ".#folderconfig.json" in files:
        files.remove(".#folderconfig.json")
    
    #size_user = psutil.disk_usage(storage_dir).used
    size_user = get_total_file_size(storage_dir)
    
    #print(shutil.disk_usage(storage_dir).used)

    size_formatted = get_formatted_file_size(size_user)
    # of 5 GB
    size_percentage = int((size_user / 5368709120) * 100)
    
    file_list = []
    for file in files:
        # check if file is not a folder
        if not os.path.isdir(os.path.join(storage_dir, file)):
            file_list.append({"filename": file, "icon": ih.get_icon(os.path.join(storage_dir, file)), "size": get_formatted_file_size(os.path.getsize(os.path.join(storage_dir, file))), "type": "file"})
        else:
            # try to get the icon of the folder, its in a .#folderconfig.json file
            if os.path.exists(os.path.join(storage_dir, file, ".#folderconfig.json")):
                f = open(os.path.join(storage_dir, file, ".#folderconfig.json"), "r")
                data = json.load(f)
                color = data["color"]
                f.close()
            else:
                color = "blue"
            
            file_list.append({"filename": file, "icon": f"https://www.gruettecloud.com/static/icons/folder-{color}.svg", "size": get_formatted_file_size(get_total_file_size(os.path.join(storage_dir, file))), "type": "folder"})
        
    return {"file_list": file_list, "size_formatted": size_formatted, "size_percentage": size_percentage}

@gruetteStorage_route.route("/movefile")
def move_file():
    if "username" not in session:
        return redirect("/")

    sql = SQLHelper.SQLHelper()
    
    username = str(session["username"]).lower()
    file_path = request.args.get("file")
    new_path = request.args.get("folder")
    
    
    if file_path == None or file_path == "None":
        return redirect("/storage")
    
    if new_path == "None":
        new_path = ""
        
    if os.path.exists(os.path.join(gruetteStorage_path, username, file_path)) and os.path.exists(os.path.join(gruetteStorage_path, username, new_path)):
        shutil.move(os.path.join(gruetteStorage_path, username, file_path), os.path.join(gruetteStorage_path, username, new_path))
        if new_path != "":
            return redirect(f"/file/{new_path}")
        else:
            return redirect("/storage")
    else:
        return redirect("/storage")


@gruetteStorage_route.route("/file/<path:file_path>")
def open_file(file_path):
    if "username" not in session:
        return redirect("/")
    
    if os.path.exists(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path)):
        back_track = file_path.split("/")[:-1]
        back_track = "/".join(back_track)
        if back_track == "":
            back_track = None
        # Check if file is folder
        if os.path.isdir(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path)):
            files_in_folder = get_files(str(session["username"]).lower(), file_path)["file_list"]
            
            if os.path.exists(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path, ".#folderconfig.json")):
                f = open(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path, ".#folderconfig.json"), "r")
                data = json.load(f)
                color = data["color"]
                f.close()
            else:
                color = "blue"
                
            return render_template("folder.html", menu=th.user(session), username=str(session["username"]).lower(), folder=file_path, files=files_in_folder, back=back_track, color=color)
        
        else:
            sql = SQLHelper.SQLHelper()
            filesize = get_formatted_file_size(os.path.getsize(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path)))
            created_at = datetime.datetime.fromtimestamp(os.path.getctime(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path))).strftime("%d.%m.%Y")
            icon_path = ih.get_icon(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path))
            filename = file_path.split("/")[-1]
            search_file = sql.readSQL(f"SELECT * FROM gruttestorage_files_shared WHERE file_path = '{file_path}' AND owner = '{str(session['username'])}'")
            if search_file != []:
                is_shared = True
                code = search_file[0]["short_code"]
            else:
                is_shared = False
                code = None
            return render_template("file.html", menu=th.user(session), username=str(session["username"]).lower(), file_path=file_path, filename=filename, filesize=filesize, created_at=created_at, is_author=True, file_icon=icon_path, back=back_track, is_shared=is_shared, code=code)

    
    return redirect("/storage")

@gruetteStorage_route.route("/open/<path:file_path>")
def download(file_path):
    """ Route to download or preview a file from GrütteStorage

    Args:
        file_link (str): Link ID of the file

    Returns:
        File: File to download
    """
    
    if "username" not in session:
        return redirect("/")
    
    if "GruetteCloud" in file_path:
        filename = file_path.split("/")[-2]
        filename = filename.replace("GruetteCloud", "")
        return send_file(os.path.join(gruetteStorage_path, "GruetteCloud",filename), as_attachment=False)
            
    if os.path.exists(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path)):
        action = request.args.get("action")
        if action == "download":
            return send_file(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path), as_attachment=True)
        else:
            return send_file(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path), as_attachment=False)
    else:
        return redirect("/storage")
     
@gruetteStorage_route.route('/upload', methods=['POST'])
def upload():
    """ Post route to upload a file to GrütteStorage

    Returns:
        JSON: JSON object containing the filename, or an error message
    """

    if "username" not in session:
        return redirect(f"/")
    
    username = str(session['username'])

    if request.method == 'POST':
        sql = SQLHelper.SQLHelper()
        user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")

        if user == []:
            # Security check
            return redirect(f"/logout")

        file = request.files['file']
        if file:
            username = str(session['username'])
            storage_dir = os.path.join(gruetteStorage_path, username)
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)
                
            # Free users can only upload three files
            if not bool(user[0]["has_premium"]):
                files = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE owner = '{username}'")
                if len(files) >= 3:
                    abort(403)
                    
            filename = secure_filename(file.filename)
            file.save(os.path.join(storage_dir, filename))
            
            not_new_code = True
            while not_new_code:
                code = ''.join(random.choice(string.ascii_letters) for _ in range(5))
                if sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id ='{code}'") == []:
                    not_new_code = False
            
            files = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE owner = '{username}'")
            if files != []:
                for file in files:
                    if file["filename"] == filename:
                        # File already exists
                        return redirect("/storage")
    
            sql.writeSQL(f"INSERT INTO gruttestorage_links (filename, owner, link_id, is_shared, is_youtube, youtube_link) VALUES ('{filename}', '{username}', '{code}', '0', '0', '0')")
            
            return jsonify({"filename": filename})
        return jsonify({"error": "No file selected!"})



@gruetteStorage_route.route("/delete/<path:file_path>")
def delete(file_path):
    """ Route to delete a file from GrütteStorage

    Args:
        file_path (str): Link ID of the file

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/")
        
    if os.path.exists(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path)):
        try:
            os.remove(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path))
        except:
            shutil.rmtree(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path))
        
        return redirect("/storage")
    else:
        return redirect("/storage")
     
@gruetteStorage_route.route("/share/<path:file_path>")
def share(file_path):
    """ Route to share a file

    Args:
        file_path (str): Link ID of the file

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/storage")
    
    sql = SQLHelper.SQLHelper()
    
    if os.path.exists(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path)):
        # make sure its not a folder
        if os.path.isdir(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path)):
            return redirect("/storage")
        
        not_new_code = True
        while not_new_code:
            code = ''.join(random.choice(string.ascii_letters) for _ in range(5))
            if sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id ='{code}'") == []:
                not_new_code = False
                
        sql.writeSQL(f"INSERT INTO gruttestorage_files_shared (file_path, owner, short_code, name) VALUES ('{file_path}', '{str(session['username'])}', '{code}', '{file_path.split('/')[-1]}')")
        return redirect(f"/file/{file_path}")
    else:
        return redirect("/storage")
    

@gruetteStorage_route.route("/stopsharing/<path:file_path>")
def stopsharing(file_path):
    """ Route to disable file sharing for a file

    Args:
        file_path (str): Link ID of the file

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect(f"/storage")
    
    sql = SQLHelper.SQLHelper()
    if os.path.exists(os.path.join(gruetteStorage_path, str(session["username"]).lower(), file_path)):
        sql.writeSQL(f"DELETE FROM gruttestorage_files_shared WHERE file_path = '{file_path}'")
        return redirect(f"/file/{file_path}")
    else:
        return redirect("/storage")

@gruetteStorage_route.route("/s/<short_code>")
def shared(short_code):
    """ Route to view a shared file (short link)

    Args:
        short_code (str): Link ID of the file

    Returns:
        HTML: Rendered HTML page
    """

    sql = SQLHelper.SQLHelper()
    file = sql.readSQL(f"SELECT * FROM gruttestorage_files_shared WHERE short_code = '{short_code}'")
    
    if file == []:
        return redirect("/storage")
    else:
        if request.args.get("action") == "download":
            return send_file(os.path.join(gruetteStorage_path, str(file[0]["owner"]).lower(), file[0]['file_path']), as_attachment=True)
        elif request.args.get("action") == "preview":
            return send_file(os.path.join(gruetteStorage_path, str(file[0]["owner"]).lower(), file[0]['file_path']), as_attachment=False)
        
        elif "username" not in session or str(session["username"]).lower() != str(file[0]["owner"]).lower():
            filesize = get_formatted_file_size(os.path.getsize(os.path.join(gruetteStorage_path, str(file[0]["owner"]).lower(), file[0]['file_path'])))
            created_at = datetime.datetime.fromtimestamp(os.path.getctime(os.path.join(gruetteStorage_path, str(file[0]["owner"]).lower(), file[0]['file_path']))).strftime("%d.%m.%Y")
            icon_path = ih.get_icon(os.path.join(gruetteStorage_path, str(file[0]["owner"]).lower(), file[0]['file_path']))
            filename = file[0]['name']
            code = file[0]["short_code"]
            return render_template("file.html", menu=th.user(session), username=file[0]["owner"], file_path=file[0]['file_path'], filename=filename, filesize=filesize, created_at=created_at, is_author=False, file_icon=icon_path, is_shared=True, code=code)

        else:
            return redirect(f"/file/{file[0]['file_path']}")
    
@gruetteStorage_route.route("/create_folder/<path:folder_path>", methods=["POST", "GET"])
def create_folder(folder_path):
    if "username" not in session:
        return redirect("/")
    
    folder_name = str(request.form["name"])
    folder_color = str(request.form["color"])
    
    if folder_name in [".#folderconfig.json", "shared", "trash"]:
        return redirect("/storage")
    
    if folder_path == "home":
        os.mkdir(os.path.join(gruetteStorage_path, str(session["username"]), folder_name))
        os.chdir(os.path.join(gruetteStorage_path, str(session["username"]), folder_name))
    else:
        os.mkdir(os.path.join(gruetteStorage_path, str(session["username"]), folder_path, folder_name))
        os.chdir(os.path.join(gruetteStorage_path, str(session["username"]), folder_path, folder_name))

    f = open(".#folderconfig.json", "w")
    f.write(json.dumps({"color": folder_color}))
    f.close()
    return redirect("/storage")
    