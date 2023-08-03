from flask import render_template, request, redirect, session, jsonify, Blueprint
import logging

from pythonHelper import EncryptionHelper, OpenAIWrapper, SQLHelper
from config import url_prefix, templates_path, admin_users


chat_route = Blueprint("Chat", "Chat", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()

@chat_route.route("/get_messages", methods=["GET"])
def get_messages():
    """ Route to load messages into the chat

    Returns:
        str: The messages list as JSON
    """
     
    if "username" not in session:
        return redirect(f"/")
    
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
    return render_template('chat.html', username=username, recipient=recipient, messages=messages_list, verified=search_recipient[0]["is_verified"])

@chat_route.route("/ai/<method>", methods=["POST", "GET"])
def send(method):
    """ AI Chat route

    Args:
        method (str): The method to be executed

    Returns:
        str: The rendered template or a redirect
    """
    
    if "username" not in session:
        return redirect(f"/")

    ai = OpenAIWrapper.OpenAIWrapper()
    sql = SQLHelper.SQLHelper()
    
    # Get chat history from session
    chat_history = session.get("chat_history", [])

    # Check if the method is back, clear chat history and redirect to home
    if method == "back":
        session.pop("chat_history", None)
        return redirect(f"/chat")
    
    # Check if the method is restart, clear chat history and redirect to AI chat
    elif method == "restart":
        session.pop("chat_history", None)
        return redirect(f"/ai/chat")

    # Check if new message is sent, then append it to chat history, get AI response, and refresh page
    elif "send" in request.form and request.form["message"] != "":
        chat_history.append({"role": "user", "content": request.form["message"]})
        
        # Get user selected AI personality from database
        user = sql.readSQL(f"SELECT ai_personality, has_premium FROM gruttechat_users WHERE username = '{session['username']}'")
        if user == []:
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
        session.pop("chat_history", None)
        session["chat_history"] = chat_history
        print(chat_history)
        
        return redirect(f"/ai/chat")
    
    # Reverse chat history to show most recent messages first and render template
    return render_template("aichat.html", chat_history=chat_history[::-1])