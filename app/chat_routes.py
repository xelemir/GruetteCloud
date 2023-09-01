import os
import random
from flask import render_template, request, redirect, session, jsonify, Blueprint, url_for
import logging
from werkzeug.utils import secure_filename
from PIL import Image

from pythonHelper import EncryptionHelper, OpenAIWrapper, SQLHelper, TemplateHelper
from config import templates_path, pfp_path, gruetteStorage_path


chat_route = Blueprint("Chat", "Chat", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()
th = TemplateHelper.TemplateHelper()

@chat_route.route("/get_messages", methods=["GET"])
def get_messages():
    """ Route to load messages into the chat

    Returns:
        str: The messages list as JSON
    """
     
    sql = SQLHelper.SQLHelper()
    username = str(request.args.get("username")).lower()
    recipient = str(request.args.get("recipient")).lower()
    total_message_count = int(request.args.get("totalMessageCount"))  # Get the total message count
    messages_list = []

    if username != session["username"]:
        return redirect("/")
    
    # Fetch all messages from the database
    get_messages = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE ((username_send = '{username}' AND username_receive = '{recipient}') OR (username_send = '{recipient}' AND username_receive = '{username}')) ORDER BY created_at DESC")
    
    for message in get_messages:
        # Decrypt the message
        try:
            decrypted_message = str(eh.decrypt_message(message["message_content"]))
        except:
            decrypted_message = "Decryption Error!"

        if message["username_send"] == username:
            messages_list.append({"sender": "You", "content": decrypted_message})
        else:
            messages_list.append({"sender": recipient, "content": decrypted_message})

    if len(messages_list) > total_message_count:
        return jsonify(messages=messages_list, totalMessageCount=len(messages_list))
    else:
        return jsonify(messages=[], totalMessageCount=len(messages_list))  # No new messages

@chat_route.route('/chat/<recipient>', methods=['GET', 'POST'])
def chat_with(recipient):
    """ Route to chat with a user

    Args:
        recipient (str): the username of the recipient

    Returns:
        str: The rendered template or a redirect
    """

    if "username" not in session:
        return redirect(f"/")
    
    recipient = str(recipient).lower()

    sql = SQLHelper.SQLHelper()
    username = str(session['username'])
    messages_list = []

    # Check if the recipient exists
    search_recipient = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(recipient)}'")
    if search_recipient == []:
        return redirect(f'/chat')
    
    # Get the user from the database
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    if user == []:
        return redirect(f'/chat')
    
    # Post is used to send a message
    if request.method == 'POST':
        
        if 'file' in request.files and request.files['file'].filename != '':

            file = request.files['file']
            
            filename = secure_filename(file.filename)

            file.save(os.path.join(gruetteStorage_path, 'GruetteCloud', filename))
            
            encypted_message = str(eh.encrypt_message(f"https://www.gruettecloud.com/open/GruetteCloud{filename}/chat"))
            sql.writeSQL(f"INSERT INTO gruttechat_messages (username_send, username_receive, message_content) VALUES ('{username}', '{str(recipient)}', '{encypted_message}')")
            return redirect(f'/chat/{recipient}')
            
        # Check if the message is empty or too long
        if request.form['message'] == '' or len(request.form['message']) > 1000:
            print(f"Invalid message: {request.form['message']}")
            
            return redirect(f'/chat/{recipient}')

        # If the message is valid, encrypt it and send it to the database 
        else:
            encypted_message = str(eh.encrypt_message(request.form['message']))
            sql.writeSQL(f"INSERT INTO gruttechat_messages (username_send, username_receive, message_content) VALUES ('{username}', '{str(recipient)}', '{encypted_message}')")
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
    return render_template('chat.html', username=username, recipient=recipient, messages=messages_list, verified=search_recipient[0]["is_verified"], pfp=search_recipient[0]["profile_picture"])

from flask import render_template, request, redirect, session, jsonify

@chat_route.route("/ai/<method>", methods=["POST", "GET"])
def ai_chat(method):
    """ AI Chat route

    Returns:
        str: The rendered template or a JSON response
    """

    # Ensure the user is authenticated
    if "username" not in session:
        return redirect("/")
    
    if method == "restart":
        session["chat_history"] = []
        return redirect("/ai/chat")
    
    elif method == "back":
        session["chat_history"] = []
        return redirect("/chat")

    elif method == "chat":
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


@chat_route.route("/account")
def account():
    return redirect("/settings")
    

@chat_route.route("/profile/<username>")
def profile(username):
    if "username" not in session:
        return redirect(f"/")
    
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    if user == []:
        return redirect(f'/chat')
    
    edit = False
    if username == str(session["username"]):
        edit = True

    joined_on = user[0]["created_at"].strftime("%d.%m.%Y")
    return render_template("profile.html", menu=th.user(session), username=username, verified=user[0]["is_verified"], pfp=f'{user[0]["profile_picture"]}.png', premium=user[0]["has_premium"], joined_on=joined_on, admin=user[0]["is_admin"], edit=edit)


@chat_route.route("/change_pfp", methods=["POST"])
def change_pfp():
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    username = str(session["username"])

    if "profilePicture" not in request.files:
        return redirect(f"/profile/{username}")
    
    file = request.files["profilePicture"]
    filename = file.filename
    file_extension = filename.split(".")[-1]
    
    id_not_found = False
    while not id_not_found:
        potential_id = str(random.randint(10000000, 99999999))
        if not os.path.exists(os.path.join(pfp_path, f"{potential_id}.png")):
            filename = potential_id
            sql.writeSQL(f"UPDATE gruttechat_users SET profile_picture = '{filename}' WHERE username = '{str(session['username'])}'")
            id_not_found = True
            
    file.save(os.path.join(pfp_path, f"{filename}.{file_extension}"))
    
    try:
        # Open the input image
        with Image.open(os.path.join(pfp_path, f"{filename}.{file_extension}")) as img:
            # Determine the cropping region
            aspect_ratio = img.width / img.height
            if aspect_ratio > 1:
                # Landscape or square image, crop the center
                crop_start = (img.width - img.height) // 2
                img = img.crop((crop_start, 0, crop_start + img.height, img.height))
            elif aspect_ratio < 1:
                # Portrait image, crop top and bottom
                crop_start = (img.height - img.width) // 2
                img = img.crop((0, crop_start, img.width, crop_start + img.width))

            # Resize the cropped image to the target size
            img = img.resize((540, 540), Image.ANTIALIAS)

            # Ensure the output image is in JPG format
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save the converted image
            img.save(os.path.join(pfp_path, f"{filename}.png"), "png")
            # Remove the original image
            if file_extension != "png":
                img.close()
                os.remove(os.path.join(pfp_path, f"{filename}.{file_extension}"))
            
    except Exception as e:
        logging.error(e)
        return redirect(f"/settings")
                
    return redirect(f"/settings")

@chat_route.route("/remove_pfp")
def remove_pfp():
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    username = str(session["username"])
    
    sql.writeSQL(f"UPDATE gruttechat_users SET profile_picture = '{random.choice(['blue', 'green', 'purple', 'red', 'yellow'])}' WHERE username = '{str(session['username'])}'")
    return redirect(f"/settings")