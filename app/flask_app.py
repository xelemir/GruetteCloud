from flask import Flask, render_template, request, session, redirect, jsonify, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import hashlib

from pythonHelper import EncryptionHelper, SQLHelper

from loginSignUp_routes import loginSignUp_route
from utilities_routes import utilities_route
from chat_routes import chat_route
from premium_routes import premium_route
from gruetteStorage_routes import gruetteStorage_route
from dashboard_routes import dashboard_route

from config import url_prefix, admin_users, secret_key

app = Flask("GrütteCloud")
app.secret_key = secret_key
app.permanent_session_lifetime = 1209600 # 2 weeks
app.register_blueprint(loginSignUp_route)
app.register_blueprint(utilities_route)
#app.register_blueprint(chat_route)
app.register_blueprint(premium_route)
app.register_blueprint(gruetteStorage_route)
app.register_blueprint(dashboard_route)

socketio = SocketIO(app)

eh = EncryptionHelper.EncryptionHelper()

@app.route("/")
def index():
    if "username" in session:
        return redirect(f"{url_prefix}/home")
    else:
        return redirect(f"{url_prefix}/login")

@app.route("/home", methods=["GET"])
def chat(error=None):
    if 'username' not in session:
        return redirect(f'{url_prefix}/')

    username = str(session['username']).lower()
    active_chats = []
    sql = SQLHelper.SQLHelper()

    # Fetch active chats from the database
    active_chats_database = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{username}' OR username_receive = '{username}'")
                
    # Add all active chats to a list
    for chat in active_chats_database:
        if chat["username_send"].lower() == username:
            verified = False
            if chat["username_receive"].lower() in admin_users:
                verified = True
            if chat["username_receive"].lower() not in [x["username"].lower() for x in active_chats]:
                active_chats.append({"username": chat["username_receive"].lower(), "is_verified": verified})
        else:
            verified = False
            if chat["username_send"].lower() in admin_users:
                verified = True
            if chat["username_send"].lower() not in [x["username"].lower() for x in active_chats]:
                active_chats.append({"username": chat["username_send"].lower(), "is_verified": verified})
    
    # Get user's premium status
    user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{username}'")
    
    if user == []:
        # Safety check
        return redirect(f'{url_prefix}/logout')
    
    platform_message = sql.readSQL(f"SELECT created_at, content, subject, color FROM gruttechat_platform_messages")
    
    if platform_message == []:
        platform_message = None
    else:
        platform_message = {"created_at": platform_message[0]["created_at"], "content": platform_message[0]["content"], "subject": platform_message[0]["subject"], "color": platform_message[0]["color"]}
    
    if username in admin_users:
        verified = True
    else:
        verified = False
    
    # Render the home page
    return render_template('home.html', username=username, active_chats=active_chats, error=error, has_premium=user[0]["has_premium"], url_prefix=url_prefix, status_message=platform_message, verified=verified)



@app.route('/chat/<recipient>')
def open_chat(recipient):
    if 'username' not in session:
        return redirect(f'{url_prefix}/')
    
    username = str(session['username']).lower()
    recipient = str(recipient).lower()
    
    sql = SQLHelper.SQLHelper()
    
    if recipient and recipient != username and len(recipient) <= 20:
        
        # Check input validity
        user_exists = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{recipient}'")
        if user_exists == []:
            return redirect(f'{url_prefix}/home')
    
        room = generate_hashed_room_name(username, recipient)
        return redirect(f'{url_prefix}/chat/r/{room}?recipient={recipient}')
    
    return redirect(f'{url_prefix}/home')

@socketio.on('join')
def on_join(data):
    username = session.get('username')
    if username:
        room = data['room']
        join_room(room)
        emit('user_join', {'username': username}, room=room)

def get_messages_from_database(room):
    sql = SQLHelper.SQLHelper()
    
    sql_query = f"SELECT * FROM gruttechat_chats WHERE chat_id = '{room}'"
    messages = sql.readSQL(sql_query)
    return messages[::-1]

@app.route('/chat/r/<room>')
def chat_room(room):
    if 'username' not in session:
        return redirect(f'{url_prefix}/')
    
    username = str(session['username']).lower()
    recipient = str(request.args.get('recipient')).lower()
    
    if not recipient:
        recipient = "Couldn't get username"
    
    # Retrieve messages from the database for the given room
    messages = get_messages_from_database(room)
    return render_template('chat.html', url_prefix=url_prefix, room=room, messages=messages, username=username, recipient=recipient)

@socketio.on('send_private_message')
def handle_private_message(data):
    sql = SQLHelper.SQLHelper()
        
    username = session.get('username')
    if username:
        message = data['message']
        room = data['room']
        emit('receive_private_message', {'username': username, 'message': message}, room=room)

        # Store the message in the database
        sql_query = f"INSERT INTO gruttechat_chats (chat_id, author, content) VALUES ('{room}', '{username.lower()}', '{message}')"
        sql.writeSQL(sql_query)

def generate_hashed_room_name(username1, username2):
    # Sort the usernames and concatenate them
    sorted_usernames = sorted([username1, username2])
    concatenated = ''.join(sorted_usernames)

    # Hash the concatenated string
    hashed = hashlib.sha256(concatenated.encode()).hexdigest()
    return hashed



if __name__ == '__main__':
    app.run(debug=True)