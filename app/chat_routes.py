import os
import random
import time
from flask import abort, render_template, request, redirect, send_file, session, jsonify, Blueprint, url_for
import logging
from werkzeug.utils import secure_filename

from pythonHelper import EncryptionHelper, SQLHelper, TemplateHelper#, OpenAIWrapper 
from config import templates_path, gruettedrive_path

chat_route = Blueprint("Chat", "Chat", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()
th = TemplateHelper.TemplateHelper()

@chat_route.route("/get_messages", methods=["GET"])
def get_messages():
    """ Route to load messages into the chat if there are new messages on the server

    Returns:
        str: The messages list as JSON
    """
    
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    user_id = int(request.headers.get("userid"))
    recipient_id = int(request.headers.get("recipientid"))

    messageIDs_old_string = request.headers.get("messageIDs")    
    messageIDs_old = messageIDs_old_string.split(',')
    messageIDs_old = [number for number in messageIDs_old]
    
    messages_list = []
    messageIDs_new = []
    
    if user_id != session["user_id"]:        
        return abort(401)
    
    # Fetch all messages from the database
    get_messages = sql.readSQL(f"SELECT * FROM chats WHERE ((author_id = '{user_id}' AND recipient_id = '{recipient_id}') OR (author_id = '{recipient_id}' AND recipient_id = '{user_id}')) ORDER BY created_at DESC")
    
    # If unread messages are found, mark them as read
    sql.writeSQL(f"UPDATE chats SET is_read = {True} WHERE author_id = '{recipient_id}' AND recipient_id = '{user_id}' AND is_read = {False}")
    
    for message in get_messages:
        messageIDs_new.append(f"{message['id']}:{int(message['is_read'])}")
        
        # Decrypt the message
        try:
            decrypted_message = str(eh.decrypt_message(message["message_content"]))
        except:
            decrypted_message = "Decryption Error!"

        if message["author_id"] == int(user_id):
            messages_list.append({"sender": "You", "content": decrypted_message, "is_read": message["is_read"], "id": message["id"]})
        else:
            messages_list.append({"sender": recipient_id, "content": decrypted_message, "is_read": message["is_read"], "id": message["id"]})
            
    if set(messageIDs_old) != set(messageIDs_new):
        return jsonify(messages=messages_list, messageIDs=messageIDs_new)
    else:
        return jsonify(messages=[], messageIDs=messageIDs_new)

@chat_route.route("/get_message_detailed", methods=["GET"])
def get_message_detailed():
    """ Route to get a message in detail

    Returns:
        str: The message as JSON
    """
    
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    message_id = str(request.args.get("messageID"))
    
    get_message = sql.readSQL(f"SELECT users.username, chats.author_id, chats.recipient_id, chats.message_content, chats.is_read, chats.id, chats.created_at FROM chats JOIN users ON chats.author_id = users.id WHERE chats.id = '{message_id}'")
    
    if get_message == []:
        return redirect("/")
    
    if get_message[0]["author_id"] != session["user_id"] and get_message[0]["recipient_id"] != session["user_id"]:
        return redirect("/")
    
    # Decrypt the message
    try:
        decrypted_message = str(eh.decrypt_message(get_message[0]["message_content"]))
    except:
        decrypted_message = "Decryption Error!"
    
    message = {"author": get_message[0]["username"], "content": decrypted_message, "is_read": get_message[0]["is_read"], "id": get_message[0]["id"], "timestamp": get_message[0]["created_at"]}
    
    return jsonify(message)

@chat_route.route("/delete_message/<message_id>", methods=["GET"])
def delete_message(message_id):
    """ Route to delete a message

    Args:
        message_id (str): The ID of the message to delete

    Returns:
        str: Redirect to home page
    """
    
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    message_id = str(message_id)
    
    get_message = sql.readSQL(f"SELECT * FROM chats WHERE id = '{message_id}'")
    
    if get_message == []:
        return redirect("/")
    
    if get_message[0]["author_id"] != session["user_id"]:
        return redirect("/")
    
    sql.writeSQL(f"DELETE FROM chats WHERE id = '{message_id}'")
    
    return redirect(f"/chat/{get_message[0]['recipient_id']}")

@chat_route.route("/chat/<recipient_id>", methods=["GET", "POST"])
def chat_with(recipient_id):
    """ Route to chat with a user

    Args:
        recipient (str): the user ID of the recipient

    Returns:
        HTML: Rendered HTML page
    """

    if "user_id" not in session:
        return redirect("/")
    
    recipient = recipient_id

    sql = SQLHelper.SQLHelper()
    user_id = str(session["user_id"])
    messages_list = []

    # Check if the recipient exists
    search_recipient = sql.readSQL(f"SELECT * FROM users WHERE id = '{recipient}'")
    if search_recipient == []:
        return redirect("/chat")
    
    # Get the user from the database
    user = sql.readSQL(f"SELECT is_verified, profile_picture FROM users WHERE id = '{user_id}'")
    if user == []:
        return redirect("/chat")
    
    blocked = sql.readSQL(f"SELECT * FROM blocked_users WHERE user_id = '{session['user_id']}' AND blocked_user_id = '{recipient}' OR user_id = '{recipient}' AND blocked_user_id = '{session['user_id']}'")
    if blocked != []:
        if blocked[0]["user_id"] == session["user_id"]:
            blocked = "other"
        else:
            blocked = "self"
    else:
        blocked = "none"
    
    # Post is used to send a message
    if request.method == 'POST':
        
        if blocked != "none":
            return jsonify({"error": "You are blocked from sending messages to this user."}), 400
        
        if 'file' in request.files:

            file = request.files['file']
            
            file_extension = file.filename.split(".")[-1]
            
            for _ in range(50):
                if _ == 49: file, filename = None, None
                filename = hex(random.getrandbits(128))[2:] + "_" + str(session["user_id"]) + "_" + str(recipient) + "." + file_extension
                if not os.path.exists(os.path.join(gruettedrive_path, 'chat_images', filename)):
                    file.save(os.path.join(gruettedrive_path, 'chat_images', filename))
                    encypted_message = str(eh.encrypt_message(f"[](/chat-file/{filename})\n{request.form['message']}"))
                    sql.writeSQL(f"INSERT INTO chats (author_id, recipient_id, message_content, is_read) VALUES ('{user_id}', '{recipient}', '{encypted_message}', {False})")
                    message_id = sql.readSQL(f"SELECT id FROM chats WHERE author_id = '{user_id}' AND recipient_id = '{recipient}' AND message_content = '{encypted_message}'")[0]["id"]
                    sql.writeSQL(f"INSERT INTO chat_images (filename, author_id, recipient_id, chat_message_id) VALUES ('{filename}', '{user_id}', '{recipient}', '{message_id}')")
                    break
            
        # Check if the message is empty or too long
        elif request.form['message'] == '':
            print(f"Invalid message: {request.form['message']}")
            
            return jsonify({"error": "Invalid message"}), 400

        # If the message is valid, encrypt it and send it to the database 
        elif request.form['message'] != '':
            encypted_message = str(eh.encrypt_message(request.form['message']))
            sql.writeSQL(f"INSERT INTO chats (author_id, recipient_id, message_content, is_read) VALUES ('{user_id}', '{recipient}', '{encypted_message}', {False})")
            
        return jsonify({"success": "Message sent!"}), 200

    else: # GET request
        get_messages = sql.readSQL(f"SELECT * FROM chats WHERE author_id = '{user_id}' AND recipient_id = '{recipient}' OR author_id = '{recipient}' AND recipient_id = '{user_id}' ORDER BY created_at DESC")

        for message in get_messages:
            # Decrypt the message
            try:
                decrypted_message = str(eh.decrypt_message(message["message_content"]))
            except:
                decrypted_message = "Decryption Error!"

            # Check if the message was sent by the user or the recipient and add it to the list
            if message["author_id"] == user_id:
                messages_list.append(["You", decrypted_message])
            else:
                messages_list.append([recipient, decrypted_message])
                
        # Render the template
        return render_template('chat.html', user_id=user_id, recipient=search_recipient[0]["username"], messages=messages_list, verified=search_recipient[0]["is_verified"], pfp=search_recipient[0]["profile_picture"], blocked=blocked, menu=th.user(session), recipient_id=recipient)
    
@chat_route.route("/chat-file/<path:filename>", methods=["GET"])
def chat_file(filename):
    if "user_id" not in session:
        return abort(401)
    sql = SQLHelper.SQLHelper()
    user_id = session["user_id"]
    file = sql.readSQL(f"SELECT * FROM chat_images WHERE filename = '{filename}' AND author_id = '{user_id}' OR filename = '{filename}' AND recipient_id = '{user_id}'")
    if file == []:
        return abort(404)
    else:
        try:
            return send_file(f"{gruettedrive_path}/chat_images/{filename}")
        except Exception as e:
            print(e)
            return abort(404)
        
@chat_route.route("/myai", methods=["POST", "GET"])
def myai():
    from pythonHelper import openai_https
    ai = openai_https.OpenAIWrapper()
    sql = SQLHelper.SQLHelper()
    
    chat_history = session.get("chat_history", [])
    
    if request.method == "POST":
        message = request.form.get("message")
        file = request.files.get("file")
        filename = None
        
        if file and "user_id" in session:
            
            file_extension = file.filename.split(".")[-1]
            
            for _ in range(50):
                if _ == 49: file, filename = None, None
                filename = hex(random.getrandbits(128))[2:] + "_" + str(session["user_id"]) + "." + file_extension
                if not os.path.exists(os.path.join(gruettedrive_path, 'myai', filename)):
                    file.save(os.path.join(gruettedrive_path, 'myai', filename))
                    break
            
        if message == "#!# Requesting Welcome Message #!#":
            chat_history.append({"role": "user", "content": "Hi, please give me a welcome to GrütteChat message."})
        elif message == "#!# Requesting Welcome Message DE #!#":
            chat_history.append({"role": "user", "content": "Hallo, bitte gib mir eine nette Willkommensnachricht für GrütteChat. Antworte nur noch auf Deutsch."})
        else:
            chat_history.append({"role": "user", "content": message})

        if "user_id" in session:
            user = sql.readSQL(f"SELECT username, ai_personality, has_premium, ai_model FROM users WHERE id = '{session['user_id']}'")
            
            if not user:
                return redirect("/logout")
            else:
                selected_ai_personality = user[0]["ai_personality"]
                has_premium = bool(user[0]["has_premium"])
                ai_model = user[0]["ai_model"]
                username = user[0]["username"]
                
        else:
            selected_ai_personality = session.get("ai_personality", "Default")
            has_premium = False
            ai_model = "gpt-4o-mini"
            username = "Guest user"
            
        
        try:
            if file and has_premium:
                chat_history = ai.get_openai_response(chat_history, username=username, ai_personality=selected_ai_personality, has_premium=has_premium, ai_model=ai_model, url=f"https://www.gruettecloud.com/myai-file/{filename}")
                if chat_history[-1]["content"] == "I'm having some trouble processing your request. Please try again later.":
                    os.remove(os.path.join(gruettedrive_path, 'myai', filename))
                else:
                    chat_history[-2]["image"] = f"/myai-file/{filename}"
                
            elif file:
                os.remove(os.path.join(gruettedrive_path, 'myai', filename))
                
            else:
                chat_history = ai.get_openai_response(chat_history, username=username, ai_personality=selected_ai_personality, has_premium=has_premium, ai_model=ai_model)
        except Exception as e:
            logging.error(e)
            if filename is not None: os.remove(os.path.join(gruettedrive_path, 'GruetteCloud', filename))
            chat_history.append({"role": "assistant", "content": "I am having trouble connecting... Please try again later.", "image": None})

        session["chat_history"] = chat_history
        chat_response = [{"role": message["role"], "content": message["content"], "image": message.get("image")} for message in chat_history]
        
        print(chat_response)
                
        return jsonify({"chat_history": chat_response})

    else:
        
        if "user_id" in session:
            user = sql.readSQL(f"SELECT ai_personality, has_premium, ai_model FROM users WHERE id = '{session['user_id']}'")[0]
        else:
            selected_ai_personality = session.get("ai_personality", "Default")
            user = {"ai_personality": selected_ai_personality, "has_premium": False, "ai_model": "gpt-4o-mini"}
            
        return render_template("myai.html", chat_history=chat_history[::-1], selected_personality=user["ai_personality"], ai_model=user["ai_model"], has_premium=user["has_premium"])

@chat_route.route("/myai-file/<path:filename>", methods=["GET"])
def myai_file(filename):
    try:
        return send_file(f"{gruettedrive_path}/myai/{filename}")
    except Exception as e:
        print(e)
        return abort(404)

@chat_route.route("/restart-myai", methods=["GET"])
def restart_myai():
    session["chat_history"] = []
    return redirect("/myai")

    """
    path = os.path.join(gruettedrive_path, 'myai', 'a010fe1b1268f3d634053a8eed655b73_1.png')

    time = os.path.getctime(path)

    # Convert the time to a readable format

    from datetime import datetime

    date = datetime.fromtimestamp(time)

    print(date)
    """
    
@chat_route.route('/chat/delete/<recipient_id>')
def delete_chat(recipient_id): 
    """ Delete chat route

    Args:
        recipient_id (str): The user ID of the chat to delete

    Returns:
        str: Redirect to home page
    """    
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"DELETE FROM chats WHERE author_id = '{user_id}' AND recipient_id = '{recipient_id}' OR author_id = '{recipient_id}' AND recipient_id = '{user_id}'")
    return redirect(f'/chat')


@chat_route.route("/profile/<user_id>")
def profile(user_id):
    """ Route to view a user's profile

    Args:
        user_id (str): The user ID of the user to view

    Returns:
        HTML: Rendered HTML page
    """
    
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    is_blocked = sql.readSQL(f"SELECT * FROM blocked_users WHERE user_id = '{session['user_id']}' AND blocked_user_id = '{user_id}' OR user_id = '{user_id}' AND blocked_user_id = '{session['user_id']}'")
    if is_blocked != []:
        return redirect(f"/chat/{user_id}")
    
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{user_id}'")
    if user == []:
        return redirect('/chat')
    
    edit = False
    if user_id == session["user_id"]:
        edit = True

    joined_on = user[0]["created_at"].strftime("%d.%m.%Y")
    return render_template("profile.html", menu=th.user(session), profile_user_id=user[0]["id"], verified=user[0]["is_verified"], pfp=f'{user[0]["profile_picture"]}.png', premium=user[0]["has_premium"], joined_on=joined_on, admin=user[0]["is_admin"], edit=edit, username=user[0]["username"])

@chat_route.route("/block/<user_id>")
def block(user_id):
    """ Route to block a user

    Args:
        user_id (str): The user ID of the user to block

    Returns:
        str: Redirect to home page
    """
    if "user_id" not in session:
        return redirect("/")

    if (user_id == session["user_id"]):
        return redirect("/chat")

    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"INSERT INTO blocked_users (user_id, blocked_user_id) VALUES ('{session['user_id']}', '{user_id}')")
    return redirect(f"/chat/{user_id}")

@chat_route.route("/unblock/<user_id>")
def unblock(user_id):
    """ Route to unblock a user

    Args:
        user_id (str): The user ID of the user to unblock

    Returns:
        str: Redirect to home page
    """
    if "user_id" not in session:
        return redirect("/")
    
    if (user_id == session["user_id"]):
        return redirect("/chat")
    
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"DELETE FROM blocked_users WHERE user_id = '{session['user_id']}' AND blocked_user_id = '{user_id}'")
    return redirect(f"/chat/{user_id}")