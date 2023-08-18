import datetime
from flask import render_template, request, redirect, session, Blueprint, send_file, jsonify, url_for
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
icon = IconHelper.IconHelper()
th = TemplateHelper.TemplateHelper()



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
    
    return render_template("storage.html", menu=th.user(session), username=username, files=file_list, size_formatted=files["size_formatted"], size_percentage=files["size_percentage"], status=None, verified=bool(username_database[0]["is_verified"]), is_admin=bool(username_database[0]["is_admin"]))


# Helper function to convert file size to human-readable format
def get_formatted_file_size(size):
    # 1 kilobyte (KB) = 1024 bytes
    # 1 megabyte (MB) = 1024 kilobytes
    # 1 gigabyte (GB) = 1024 megabytes
    # 1 terabyte (TB) = 1024 gigabytes

    power = 2 ** 10  # 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

    while size > power:
        size /= power
        n += 1

    return f"{size:.2f} {power_labels[n]}"

def get_files(username):
    sql = SQLHelper.SQLHelper()
    
    storage_dir = os.path.join(gruetteStorage_path, username)
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

    files = os.listdir(storage_dir)
    
    size_user = sum(os.path.getsize(os.path.join(storage_dir, file)) for file in files)

    size_formatted = get_formatted_file_size(size_user)
    size_percentage = (size_user / (5 * 1073741824)) * 100  # 5 GB
    
    file_list = []
    files_database = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE owner = '{username}'")
    for file in files_database:
        try:
            if bool(file["is_shared"]):
                file_list.append({"filename": file["filename"], "size": get_formatted_file_size(os.path.getsize(os.path.join(storage_dir, file["filename"]))), "type": "shared", "link": file["link_id"]})
            elif bool(file["is_youtube"]):
                file_list.append({"filename": file["filename"], "size": get_formatted_file_size(os.path.getsize(os.path.join(storage_dir, file["filename"]))), "type": "youtube", "link": file["link_id"], "youtube_link": file["youtube_link"]})
            else:
                file_list.append({"filename": file["filename"], "size": get_formatted_file_size(os.path.getsize(os.path.join(storage_dir, file["filename"]))), "type": "private", "link": file["link_id"]})
        except:
            pass
    
    return {"file_list": file_list, "size_formatted": size_formatted, "size_percentage": size_percentage}
    
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
            storage_dir = os.path.join(gruetteStorage_path, username)
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)
                    
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

@gruetteStorage_route.route("/open/<file_link>/<preview>")
def download(file_link, preview="Default"):
    if "GruetteCloud" in file_link:
        # Links are like this: GruetteCloud12345
        actual_link = file_link[12:]
        print(actual_link)
        path = os.path.join(gruetteStorage_path, "GruetteCloud", actual_link)
        if os.path.exists(path):
            return send_file(path, as_attachment=False)
    
    sql = SQLHelper.SQLHelper()
    file = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id = '{file_link}'")
    path = os.path.join(gruetteStorage_path, file[0]["owner"], file[0]["filename"])
    
    if file == []:
        return redirect("/")
    elif bool(file[0]["is_shared"]):
        if preview == "preview":
            return send_file(path, as_attachment=False)
        else:
            return send_file(path, as_attachment=True)
        
    elif file[0]["owner"] == str(session['username']):
        if preview == "preview":
            return send_file(path, as_attachment=False)
        else:
            return send_file(path, as_attachment=True)
        
    else:
        return redirect(f"/storage")

@gruetteStorage_route.route("/delete/<file_link>")
def delete(file_link):
    if "username" not in session:
        return redirect(f"/")
        
    sql = SQLHelper.SQLHelper()
    file = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id = '{file_link}'")
    
    if file == []:
        return redirect("/")
    elif file[0]["owner"] == str(session['username']):
    
        path = os.path.join(gruetteStorage_path, file[0]["owner"], file[0]["filename"])
        os.remove(path)
        
        sql.writeSQL(f"DELETE FROM gruttestorage_links WHERE link_id = '{file_link}'")
            
    return redirect(f"/storage")

@gruetteStorage_route.route("/file/<file_link>")
def file(file_link):
    sql = SQLHelper.SQLHelper()
    
    file = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id = '{file_link}'")

    if file == []:
        return redirect("/")
    elif "username" not in session or file[0]["owner"] != str(session['username']):
        if bool(file[0]["is_shared"]):
            file_path = os.path.join(gruetteStorage_path, file[0]["owner"], file[0]["filename"])
            filesize = get_formatted_file_size(os.path.getsize(file_path))
            created_at = datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%d.%m.%Y")
            icon_path = IconHelper.IconHelper().get_icon(file_path)
            code = "https://www.gruettecloud.com/s/" + str(file_link)
            user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{file[0]['owner']}'")
            is_author_verified = False
            if user != []:
                is_author_verified = bool(user[0]["is_verified"])
                return render_template("fileinfo.html", username=file[0]["owner"], filename=file[0]["filename"], filesize=filesize, created_at=created_at, is_author=False, is_shared=True, file_icon=icon_path, link_id=file_link, is_gruettecloud_user=False, is_author_verified=is_author_verified, is_youtube_video=False, youtube_link=None)
            
        return redirect(f"/")
    
    else:
        file_path = os.path.join(gruetteStorage_path, file[0]["owner"], file[0]["filename"])
        filesize = get_formatted_file_size(os.path.getsize(file_path))
        created_at = datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%d.%m.%Y")
        icon_path = IconHelper.IconHelper().get_icon(file_path)
        code = "https://www.gruettecloud.com/s/" + str(file_link)
        user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{file[0]['owner']}'")
        is_author_verified = False
        if user != []:
            is_author_verified = bool(user[0]["is_verified"])
        return render_template("fileinfo.html", menu=th.user(session), username=file[0]["owner"], filename=file[0]["filename"], filesize=filesize, created_at=created_at, is_author=True, is_shared=bool(file[0]["is_shared"]), file_icon=icon_path, link_id=file_link, is_gruettecloud_user=True, is_author_verified=is_author_verified, is_youtube_video=bool(file[0]["is_youtube"]), youtube_link=file[0]["youtube_link"])
     

@gruetteStorage_route.route("/share/<file_link>")
def share(file_link):
    if "username" not in session:
        return redirect(f"/storage")
    
    sql = SQLHelper.SQLHelper()
    file = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id = '{file_link}'")
    
    if file == []:
        return redirect("/")
    elif bool(file[0]["is_youtube"]):
        return redirect(f"/file/{file_link}")
    elif file[0]["owner"] == str(session['username']):
        sql.writeSQL(f"UPDATE gruttestorage_links SET is_shared = {True} WHERE link_id = '{file_link}'")
        return redirect(f"/file/{file_link}")
    else:
        return redirect(f"/storage")
    


@gruetteStorage_route.route("/stopsharing/<file_link>")
def stopsharing(file_link):
    if "username" not in session:
        return redirect(f"/storage")
    
    sql = SQLHelper.SQLHelper()
    file = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id = '{file_link}'")
    
    if file == []:
        return redirect("/")
    elif file[0]["owner"] == str(session['username']):
        sql.writeSQL(f"UPDATE gruttestorage_links SET is_shared = {False} WHERE link_id = '{file_link}'")
        return redirect(f"/file/{file_link}")
    else:
        return redirect(f"/storage")
    

@gruetteStorage_route.route("/s/<link_id>")
def shared(link_id):
    sql = SQLHelper.SQLHelper()
    result = sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id ='{link_id}'")
    if result == []:
        return redirect("/")
    elif bool(result[0]["is_shared"]):
        return redirect(f"/file/{link_id}")
    
    return redirect("/")

@gruetteStorage_route.route("/youtube", methods=["GET", "POST"])
def download_from_youtube():
    if "username" not in session:
        return redirect(f"/")

    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{str(session['username'])}'")

    if user == []:
        return redirect(f"/")
    elif not bool(user[0]["has_premium"]):
        return redirect(f"/premium")

    if request.method == "GET":
        
        return render_template("youtube.html")
    elif request.method == "POST":
        try:
            video_url = str(request.form["video_url"])
            youtube = YouTubeHelper.YouTubeHelper(url=video_url)
        except:
            return jsonify({"error": "Something went wrong on our end :/"})
            
        youtube.download(username=str(session["username"]))
        video_id = youtube.get_media_title()
        
        not_new_code = True
        while not_new_code:
            code = ''.join(random.choice(string.ascii_letters) for _ in range(5))
            if sql.readSQL(f"SELECT * FROM gruttestorage_links WHERE link_id ='{code}'") == []:
                not_new_code = False
                    
        print(code)
        sql.writeSQL(f"INSERT INTO gruttestorage_links (filename, owner, link_id, is_shared, is_youtube, youtube_link) VALUES ('{video_id}.mp4', '{str(session['username'])}', '{code}', '0', '1', '{video_url}')")

        return jsonify({"filename": video_id})