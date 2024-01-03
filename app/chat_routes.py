import os
import random
from flask import render_template, request, redirect, session, jsonify, Blueprint, url_for
import logging
from werkzeug.utils import secure_filename

from pythonHelper import EncryptionHelper, OpenAIWrapper, SQLHelper, TemplateHelper
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
    
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    username = str(request.args.get("username")).lower()
    recipient = str(request.args.get("recipient")).lower()
    
    messageIDs_old_string = request.args.get("messageIDs")    
    messageIDs_old = messageIDs_old_string.split(',')
    messageIDs_old = [number for number in messageIDs_old]
    
    messages_list = []
    messageIDs_new = []
    
    if username != session["username"]:
        return redirect("/")
    
    # Fetch all messages from the database
    get_messages = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE ((username_send = '{username}' AND username_receive = '{recipient}') OR (username_send = '{recipient}' AND username_receive = '{username}')) ORDER BY created_at DESC")
    
    # If unread messages are found, mark them as read
    sql.writeSQL(f"UPDATE gruttechat_messages SET is_read = {True} WHERE username_send = '{recipient}' AND username_receive = '{username}' AND is_read = {False}")
    
    for message in get_messages:
        messageIDs_new.append(f"{message['id']}:{int(message['is_read'])}")
        
        # Decrypt the message
        try:
            decrypted_message = str(eh.decrypt_message(message["message_content"]))
        except:
            decrypted_message = "Decryption Error!"

        if message["username_send"] == username:
            messages_list.append({"sender": "You", "content": decrypted_message, "is_read": message["is_read"], "id": message["id"]})
        else:
            messages_list.append({"sender": recipient, "content": decrypted_message, "is_read": message["is_read"], "id": message["id"]})
            
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
    
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    message_id = str(request.args.get("messageID"))
    
    get_message = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE id = '{message_id}'")
    
    if get_message == []:
        return redirect("/")
    
    if get_message[0]["username_send"] != session["username"] and get_message[0]["username_receive"] != session["username"]:
        return redirect("/")
    
    # Decrypt the message
    try:
        decrypted_message = str(eh.decrypt_message(get_message[0]["message_content"]))
    except:
        decrypted_message = "Decryption Error!"
    
    message = {"author": get_message[0]["username_send"], "content": decrypted_message, "is_read": get_message[0]["is_read"], "id": get_message[0]["id"], "timestamp": get_message[0]["created_at"]}
    
    return jsonify(message)

@chat_route.route("/delete_message/<message_id>", methods=["GET"])
def delete_message(message_id):
    """ Route to delete a message

    Args:
        message_id (str): The ID of the message to delete

    Returns:
        str: Redirect to home page
    """
    
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    message_id = str(message_id)
    
    get_message = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE id = '{message_id}'")
    
    if get_message == []:
        return redirect("/")
    
    if get_message[0]["username_send"] != session["username"]:
        return redirect("/")
    
    sql.writeSQL(f"DELETE FROM gruttechat_messages WHERE id = '{message_id}'")
    
    return redirect(f"/chat/{get_message[0]['username_receive']}")

@chat_route.route("/chat/<recipient>", methods=["GET", "POST"])
def chat_with(recipient):
    """ Route to chat with a user

    Args:
        recipient (str): the username of the recipient

    Returns:
        HTML: Rendered HTML page
    """

    if "username" not in session:
        return redirect("/")
    
    recipient = str(recipient).lower()

    sql = SQLHelper.SQLHelper()
    username = str(session["username"])
    messages_list = []

    # Check if the recipient exists
    search_recipient = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(recipient)}'")
    if search_recipient == []:
        return redirect("/chat")
    
    # Get the user from the database
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    if user == []:
        return redirect("/chat")
    
    blocked = sql.readSQL(f"SELECT * FROM gruttechat_blocked_users WHERE username = '{session['username']}' AND username_blocked = '{recipient}' OR username = '{recipient}' AND username_blocked = '{session['username']}'")
    if blocked != []:
        if blocked[0]["username"] == session["username"]:
            blocked = "other"
        else:
            blocked = "self"
    else:
        blocked = "none"
    
    # Post is used to send a message
    if request.method == 'POST':
        
        if blocked != "none":
            return redirect(f'/chat/{recipient}')
        
        if 'file' in request.files and request.files['file'].filename != '':

            file = request.files['file']
            
            filename = secure_filename(file.filename)

            file.save(os.path.join(gruettedrive_path, 'GruetteCloud', filename))
            
            encypted_message = str(eh.encrypt_message(f"https://www.gruettecloud.com/open/GruetteCloud{filename}/chat"))
            sql.writeSQL(f"INSERT INTO gruttechat_messages (username_send, username_receive, message_content, is_read) VALUES ('{username}', '{str(recipient)}', '{encypted_message}' , {False})")
            return redirect(f'/chat/{recipient}')
            
        # Check if the message is empty or too long
        if request.form['message'] == '' or len(request.form['message']) > 1000:
            print(f"Invalid message: {request.form['message']}")
            
            return redirect(f'/chat/{recipient}')

        # If the message is valid, encrypt it and send it to the database 
        else:
            encypted_message = str(eh.encrypt_message(request.form['message']))
            sql.writeSQL(f"INSERT INTO gruttechat_messages (username_send, username_receive, message_content, is_read) VALUES ('{username}', '{str(recipient)}', '{encypted_message}', {False})")
            return redirect(f'/chat/{recipient}')

    # Get is used to load the chat
    get_messages = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{username}' AND username_receive = '{recipient}' OR username_send = '{recipient}' AND username_receive = '{username}' ORDER BY created_at DESC")

    for message in get_messages:
        # Decrypt the message
        try:
            decrypted_message = str(eh.decrypt_message(message["message_content"]))
        except:
            decrypted_message = "Decryption Error!"

        # Check if the message was sent by the user or the recipient and add it to the list
        if message["username_send"] == username:
            messages_list.append(["You", decrypted_message])
        else:
            messages_list.append([recipient, decrypted_message])
            
    # Render the template
    return render_template('chat.html', username=username, recipient=recipient, messages=messages_list, verified=search_recipient[0]["is_verified"], pfp=search_recipient[0]["profile_picture"], blocked=blocked, menu=th.user(session))

@chat_route.route("/ai/<action>", methods=["POST", "GET"])
def ai_chat(action):
    """ Route to chat with the AI

    Returns:
        HTML: Rendered HTML page
    """

    # Ensure the user is authenticated
    if "username" not in session:
        return redirect("/")
    
    if action == "restart":
        session["chat_history"] = []
        return redirect("/ai/chat")

    elif action == "chat":
        # Get AI instance and SQL helper
        ai = OpenAIWrapper.OpenAIWrapper()
        sql = SQLHelper.SQLHelper()

        # Get or initialize the chat history from the session
        chat_history = session.get("chat_history", [])

        if request.method == "POST":
            message = request.form.get("message")
            
            if message == "#!# Requesting Welcome Message #!#":
                chat_history.append({"role": "user", "content": "Hi, please give me a welcome to GrütteChat message."})
            else:
                # Append the user's message to chat history
                chat_history.append({"role": "user", "content": message})
    

            # Retrieve user's selected AI personality and premium status
            user = sql.readSQL(f"SELECT ai_personality, has_premium FROM gruttechat_users WHERE username = '{session['username']}'")

            if not user:
                selected_ai_personality = "Default"
                has_premium = False
            else:
                selected_ai_personality = user[0]["ai_personality"]
                has_premium = bool(user[0]["has_premium"])

            try:

                # Get AI response and append it to chat history
                chat_history = ai.get_openai_response(chat_history, username=session["username"], ai_personality=selected_ai_personality, has_premium=has_premium)

            except Exception as e:
                logging.error(e)
                chat_history.append({"role": "assistant", "content": "I am having trouble connecting... Please try again later."})

            # Save chat history to session
            session["chat_history"] = chat_history

            # Prepare the chat response as JSON
            chat_response = [{"role": message["role"], "content": message["content"]} for message in chat_history]

            return jsonify({"chat_history": chat_response})

        # Reverse chat history to show most recent messages first and render template
        return render_template("aichat.html", chat_history=chat_history[::-1])
    
@chat_route.route('/chat/delete/<recipient>')
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


@chat_route.route("/profile/<username>")
def profile(username):
    """ Route to view a user's profile

    Args:
        username (str): The username of the user

    Returns:
        HTML: Rendered HTML page
    """
    
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    is_blocked = sql.readSQL(f"SELECT * FROM gruttechat_blocked_users WHERE username = '{session['username']}' AND username_blocked = '{username}' OR username = '{username}' AND username_blocked = '{session['username']}'")
    if is_blocked != []:
        return redirect(f"/chat/{username}")
    
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    if user == []:
        return redirect(f'/chat')
    
    edit = False
    if username == str(session["username"]):
        edit = True

    joined_on = user[0]["created_at"].strftime("%d.%m.%Y")
    return render_template("profile.html", menu=th.user(session), username=username, verified=user[0]["is_verified"], pfp=f'{user[0]["profile_picture"]}.png', premium=user[0]["has_premium"], joined_on=joined_on, admin=user[0]["is_admin"], edit=edit)

@chat_route.route("/block/<username>")
def block(username):
    """ Route to block a user

    Args:
        username (str): The username of the user to block

    Returns:
        str: Redirect to home page
    """
    if "username" not in session:
        return redirect("/")

    if (username == session["username"]):
        return redirect("/chat")

    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"INSERT INTO gruttechat_blocked_users (username, username_blocked) VALUES ('{session['username']}', '{username}')")
    return redirect(f"/chat/{username}")

@chat_route.route("/unblock/<username>")
def unblock(username):
    """ Route to unblock a user

    Args:
        username (str): The username of the user to unblock

    Returns:
        str: Redirect to home page
    """
    if "username" not in session:
        return redirect("/")
    
    if (username == session["username"]):
        return redirect("/chat")
    
    sql = SQLHelper.SQLHelper()
    sql.writeSQL(f"DELETE FROM gruttechat_blocked_users WHERE username = '{session['username']}' AND username_blocked = '{username}'")
    return redirect(f"/chat/{username}")