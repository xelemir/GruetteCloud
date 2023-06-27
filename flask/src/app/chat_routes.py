from flask import render_template, request, redirect, session, jsonify, Blueprint
import logging

from pythonHelper import EncryptionHelper, OpenAIWrapper, MongoDBHelper
from credentials import url_suffix


if url_suffix == "/gruettechat":
    path_template = "/application/templates"
else:
    path_template = "/application/templates"

chat_route = Blueprint("Chat", "Chat", template_folder=path_template)

eh = EncryptionHelper.EncryptionHelper()
db = MongoDBHelper.MongoDBHelper()

@chat_route.route("/get_messages", methods=["GET"])
def get_messages():
     
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    
    username = str(request.args.get("username"))
    recipient = str(request.args.get("recipient"))
    messages_list = []
    
    # Fetch all messages from the database
    get_messages = db.read('messages', {"$or": [{"username_send": username, "username_receive": recipient}, {"username_send": recipient, "username_receive": username}]}, sort=[("created_at", -1)])
    
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
        
    # Return the list as JSON
    return jsonify(messages=messages_list)


@chat_route.route('/chat/<recipient>', methods=['GET', 'POST'])
def chat_with(recipient):
    if "username" not in session:
        return redirect(f"{url_suffix}/")

    username = str(session['username'])
    messages_list = []

    # Check if the recipient exists
    search_recipient = db.read('users', {"username": recipient})
    if not search_recipient:
        return redirect(f'{url_suffix}/chat')
    
    # Get the user from the database
    user = db.read('users', {"username": username})
    if not user:
        return redirect(f'{url_suffix}/chat')
    
    # Premium chat meaning that the user needs GrütteChat PLUS to chat with this user
    premium_chat = bool(search_recipient[0]["premium_chat"])
    if premium_chat and not bool(user[0]["has_premium"]):
        return render_template('home.html', error=f"You need GrütteChat PLUS to chat with {str(recipient)}!", url_suffix = url_suffix)
    
    # Post is used to send a message
    if request.method == 'POST':
        
        # Check if the message is empty or too long
        if request.form['message'] == '' or len(request.form['message']) > 1000:
            print(f"Invalid message: {request.form['message']}")
            
            return redirect(f'{url_suffix}/chat/{recipient}')

        # If the message is valid, encrypt it and send it to the database 
        else:
            encypted_message = str(eh.encrypt_message(request.form['message']))
            db.write('messages', {"username_send": username, "username_receive": recipient, "message_content": encypted_message})
            return redirect(f'{url_suffix}/chat/{recipient}')

    # Get is used to load the chat
    get_messages = db.read('messages', {"$or": [{"username_send": username, "username_receive": recipient}, {"username_send": recipient, "username_receive": username}]}, sort=[("created_at", -1)])
    
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
    return render_template('chat.html', username=username, recipient=recipient, messages=messages_list, premium_chat=premium_chat, url_suffix = url_suffix)

@chat_route.route("/ai/<method>", methods=["POST", "GET"])
def send(method):
    
    if "username" not in session:
        return redirect(f"{url_suffix}/")

    ai = OpenAIWrapper.OpenAIWrapper()

    # Get chat history from session
    chat_history = session.get("chat_history", [])

    # Check if the method is back, clear chat history and redirect to home
    if method == "back":
        session.pop("chat_history", None)
        return redirect(f"{url_suffix}/")
    
    # Check if the method is restart, clear chat history and redirect to AI chat
    elif method == "restart":
        session.pop("chat_history", None)
        return redirect(f"{url_suffix}/ai/chat")

    # Check if new message is sent, then append it to chat history, get AI response, and refresh page
    elif "send" in request.form and request.form["message"] != "":
        chat_history.append({"role": "user", "content": request.form["message"]})
        
        # Get user selected AI personality from database
        user = db.read('users', {"username": session['username']})
        if not user:
            selected_ai_personality = "Default"
            has_premium = False
        else:
            selected_ai_personality = user[0]["ai_personality"]
            has_premium = bool(user[0]["has_premium"])

        # Get AI response (response is appended to chat history internally)
        try:
            chat_history = ai.get_openai_response(chat_history, username=session["username"], ai_personality=selected_ai_personality, has_premium=has_premium)

        # If there is an error, append error message to chat history
        except Exception as e:
            logging.error(e)
            chat_history.append({"role": "assistant", "content": "I am having trouble connecting... Please try again later."})
            
        # Save chat history to session and refresh page
        session["chat_history"] = chat_history
        return redirect(f"{url_suffix}/ai/chat")
    
    # Reverse chat history to show most recent messages first and render template
    chat_history.reverse()
    return render_template("aichat.html", chat_history=chat_history, url_suffix = url_suffix)