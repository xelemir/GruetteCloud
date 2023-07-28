from flask import render_template, request, redirect, session, jsonify, Blueprint, url_for
import logging
import hashlib

from pythonHelper import EncryptionHelper, OpenAIWrapper, SQLHelper
from config import url_prefix, templates_path, admin_users


eh = EncryptionHelper.EncryptionHelper()


chat_route = Blueprint("Chat", "Chat", template_folder=templates_path)


"""@chat_route.route("/get_messages", methods=["GET"])
def get_messages():

     
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    sql = SQLHelper.SQLHelper()
    username = str(request.args.get("username")).lower()
    recipient = str(request.args.get("recipient")).lower()
    messages_list = []
    
    # Fetch all messages from the database
    get_messages = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{username}' AND username_receive = '{recipient}' OR username_send = '{recipient}' AND username_receive = '{username}' ORDER BY created_at DESC")
    
    for message in get_messages:
        # Decrypt the message
        try:
            decrypted_message = str(eh.decrypt_message(message["message_content"]))
        except:
            decrypted_message = "Decryption Error!"

        # Check if the message was sent by the user or the recipient abd add it to the list
        if message["username_send"] == username:
            messages_list.append(["You", decrypted_message])
        else:
            messages_list.append([recipient, decrypted_message])
        
    # Return the list as JSON
    return jsonify(messages=messages_list)


@chat_route.route('/chat/<recipient>', methods=['GET', 'POST'])
def chat_with(recipient):
    

    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    recipient = str(recipient).lower()

    sql = SQLHelper.SQLHelper()
    username = str(session['username'])
    messages_list = []

    # Check if the recipient exists
    search_recipient = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(recipient)}'")
    if search_recipient == []:
        return redirect(f'{url_prefix}/chat')
    
    # Get the user from the database
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    if user == []:
        return redirect(f'{url_prefix}/chat')
    
    # Post is used to send a message
    if request.method == 'POST':
        
        # Check if the message is empty or too long
        if request.form['message'] == '' or len(request.form['message']) > 1000:
            print(f"Invalid message: {request.form['message']}")
            
            return redirect(f'{url_prefix}/chat/{recipient}')

        # If the message is valid, encrypt it and send it to the database 
        else:
            encypted_message = str(eh.encrypt_message(request.form['message']))
            sql.writeSQL(f"INSERT INTO gruttechat_messages (username_send, username_receive, message_content) VALUES ('{username}', '{str(recipient)}', '{encypted_message}')")
            return redirect(f'{url_prefix}/chat/{recipient}')

    # Get is used to load the chat
    get_messages = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{username}' AND username_receive = '{recipient}' OR username_send = '{recipient}' AND username_receive = '{username}' ORDER BY created_at DESC")
    
    for message in get_messages:
        # Decrypt the message
        try:
            decrypted_message = str(eh.decrypt_message(message["message_content"]))
        except:
            decrypted_message = "Decryption Error!"

        # Check if the message was sent by the user or the recipient abd add it to the list
        if message["username_send"] == username:
            messages_list.append(["You", decrypted_message])
        else:
            messages_list.append([recipient, decrypted_message])
            
    if str(recipient) in admin_users:
        verified = True
    else:
        verified = False

    # Render the template
    return render_template('chat.html', username=username, recipient=recipient, messages=messages_list, url_prefix = url_prefix, verified=verified)"""