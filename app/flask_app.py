import hashlib
from flask import Flask, render_template, request, session, redirect, jsonify, send_from_directory, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room


from pythonHelper import EncryptionHelper, SQLHelper, TemplateHelper
from config import secret_key

from loginSignUp_routes import loginSignUp_route
from utilities_routes import utilities_route
from chat_routes import chat_route
from premium_routes import premium_route
from gruetteStorage_routes import gruetteStorage_route
from dashboard_routes import dashboard_route
from tool_routes import tool_route


app = Flask("GrütteCloud")
app.secret_key = secret_key
app.permanent_session_lifetime = 1209600 # 2 weeks
app.register_blueprint(loginSignUp_route)
app.register_blueprint(utilities_route)
app.register_blueprint(chat_route)
app.register_blueprint(premium_route)
app.register_blueprint(gruetteStorage_route)
app.register_blueprint(dashboard_route)
app.register_blueprint(tool_route)
socketio = SocketIO(app)

eh = EncryptionHelper.EncryptionHelper()
th = TemplateHelper.TemplateHelper()


@app.route("/")
def index():
    if "username" in session:
        if request.args.get('target') is not None:
            return redirect(f"/{request.args.get('target')}")
        else:
            return redirect("/chat")
    elif request.args.get('target') is not None:
        return redirect(url_for("LoginSignUp.login", target=request.args.get('target')))
    else:
        error = request.args.get("error")
        if error == "username_or_password_empty": error = "Please enter your username and password."
        elif error == "invalid_credentials": error = "Invalid username or password."
        elif error == "passwords_not_matching": error = "Passwords do not match."
        elif error == "forbidden_characters": error = "Your username contains forbidden characters."
        elif error == "username_less_40": error = "Your username must be less than 40 characters."
        elif error == "forbidden_words": error = "Your username contains forbidden words."
        elif error == "password_between_8_40": error = "Your password must be between 8 and 40 characters."
        elif error == "invalid_email": error = "Please enter a valid email address."
        elif error == "username_already_exists": error = "This username is already taken."

        return render_template("discover.html", menu=th.user(session), error=error, traceback=request.args.get("traceback"))
    
@app.errorhandler(404)
def error404(error):
    return render_template("404.html", menu=th.user(session))

@app.errorhandler(500)
def error500(error):
    return render_template("500.html", menu=th.user(session))

@app.route("/home")
def home():
    return redirect("/")

@app.route("/chat", methods=["GET", "POST"])
def chat(error=None):
    if 'username' not in session:
        return redirect(f'/')

    username = str(session['username']).lower()
    active_chats = []
    sql = SQLHelper.SQLHelper()

    if request.method == 'POST':
        # Post is used to create a new chat
        recipient = str(request.form['recipient'])

        # Check if recipient username is valid
        if recipient is None or recipient == username or len(recipient) > 50:
            return redirect(f'/chat')

        # Check if recipient exists
        user_exists = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{recipient}'")

        if user_exists == []:
            # User does not exist
            return redirect(f'/chat')

        else:
            # User exists
            return redirect(f'/chat/{recipient}')

    # Fetch active chats from the database
    active_chats_database = sql.readSQL(f"SELECT * FROM gruttechat_messages WHERE username_send = '{username}' OR username_receive = '{username}'")
                
    # Add all active chats to a list
    for chat in active_chats_database:
        if chat["username_send"].lower() == username:
            if chat["username_receive"].lower() not in [x["username"].lower() for x in active_chats]:
                user_db = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{chat['username_receive']}'")
                if user_db != []:
                    active_chats.append({"username": chat["username_receive"].lower(), "pfp": f"{user_db[0]['profile_picture']}.png", "is_verified": user_db[0]["is_verified"]})
                else:
                    active_chats.append({"username": chat["username_receive"].lower()})
        else:
            if chat["username_send"].lower() not in [x["username"].lower() for x in active_chats]:
                user_db = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{chat['username_send']}'")
                if user_db != []:
                    active_chats.append({"username": chat["username_send"].lower(), "pfp": f"{user_db[0]['profile_picture']}.png", "is_verified": user_db[0]["is_verified"]})
                else:
                    active_chats.append({"username": chat["username_send"].lower()})
    
    # Get user's premium status
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    
    if user == []:
        # Safety check
        return redirect(f'/logout')
    
    platform_message = sql.readSQL(f"SELECT created_at, content, subject, color FROM gruttechat_platform_messages")
    
    if platform_message == []:
        platform_message = None
    else:
        platform_message = {"created_at": platform_message[0]["created_at"], "content": platform_message[0]["content"], "subject": platform_message[0]["subject"], "color": platform_message[0]["color"]}
    
    if active_chats == []:
        suggest_jan = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = 'jan'")
        suggest_random = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username != '{username}' AND username != 'jan' ORDER BY RAND() LIMIT 3")
        #suggest_random = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username != '{username}' ORDER BY RAND() LIMIT 3")
        suggested = [{"username": suggest_jan[0]["username"], "pfp": f"{suggest_jan[0]['profile_picture']}.png", "is_verified": suggest_jan[0]["is_verified"]}]
        for suggest_user in suggest_random:
            suggested.append({"username": suggest_user["username"], "pfp": f"{suggest_user['profile_picture']}.png", "is_verified": suggest_user["is_verified"]})
    else:
        suggested = None
    
    # Render the home page
    return render_template('chathome.html', menu=th.user(session), username=username, active_chats=active_chats, error=error, has_premium=user[0]["has_premium"], status_message=platform_message, verified=user[0]["is_verified"], is_admin=user[0]["is_admin"], suggested=suggested, pfp=f"{user[0]['profile_picture']}.png")

# NEW SOCKETIO CHAT, NOT YET WORKING ON SERVER
@app.route('/openchat', methods=['POST'])
def openchat():
    if 'username' not in session:
        return redirect('/')
    
    recipient = request.form['recipient']
    if recipient and recipient != session['username']:
        room = generate_hashed_room_name(session['username'], recipient)
        return redirect(url_for('private_chat', room=room, recipient=recipient))
    return redirect('/chat')

def get_messages_from_database(room):
    sql = SQLHelper.SQLHelper()
    sql_query = f"SELECT * FROM gruttechat_chats WHERE chat_id = '{room}'"
    messages = sql.readSQL(sql_query)
    return messages

@app.route('/private_chat/<room>')
def private_chat(room):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    # TODO check if user is allowed to access this room

    recipient = request.args.get('recipient')
    if not recipient:
        recipient = "Couldn't get username"
    
    # Retrieve messages from the database for the given room
    messages = get_messages_from_database(room)
    for message in messages:
        if message['author'] == session['username']:
            message['author'] = 'You'

    messages = messages[::-1]
    return render_template('socketio_chat.html', username=username, room=room, messages=messages, recipient=recipient)

@socketio.on('join')
def on_join(data):
    username = session.get('username')
    if username:
        room = data['room']
        join_room(room)
        emit('user_join', {'username': username}, room=room)

@socketio.on('send_private_message')
def handle_private_message(data):
    sql = SQLHelper.SQLHelper()

    username = session.get('username')
    if username:
        message = data['message']
        room = data['room']
        emit('receive_private_message', {'username': username, 'message': message}, room=room)

        # Store the message in the database
        sql_query = f"INSERT INTO gruttechat_chats (chat_id, author, content) VALUES ('{room}', '{username}', '{message}')"
        sql.writeSQL(sql_query)

def generate_hashed_room_name(username1, username2):
    # Sort the usernames and concatenate them
    sorted_usernames = sorted([username1, username2])
    concatenated = ''.join(sorted_usernames)

    # Hash the concatenated string
    hashed = hashlib.sha256(concatenated.encode()).hexdigest()
    return hashed
    # END OF NEW SOCKETIO CHAT


if __name__ == '__main__':
    app.run(debug=True)