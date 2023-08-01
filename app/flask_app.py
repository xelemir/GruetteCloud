from flask import Flask, render_template, request, session, redirect, jsonify

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
app.register_blueprint(chat_route)
app.register_blueprint(premium_route)
app.register_blueprint(gruetteStorage_route)
app.register_blueprint(dashboard_route)

eh = EncryptionHelper.EncryptionHelper()

@app.route("/")
def index():
    if "username" in session:
        return redirect(f"{url_prefix}/chat")
    else:
        return redirect(f"{url_prefix}/login")
    
@app.route("/home")
def home():
    if "username" not in session:
        return redirect(f"{url_prefix}/")
    
    username = str(session["username"]).lower()
    sql = SQLHelper.SQLHelper()
    
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    platform_message = sql.readSQL(f"SELECT created_at, content, subject, color FROM gruttechat_platform_messages")
    if user == []:
        # Security measure
        return redirect(f"{url_prefix}/logout")
    
    is_verified = False
    if username in admin_users:
        is_verified = True
        
    if platform_message == []:
        #platform_message = None
        platform_message = {"created_at": "Today", "content": "Content", "subject": "Subject", "color": "yellow"}

    else:
        platform_message = {"created_at": platform_message[0]["created_at"], "content": platform_message[0]["content"], "subject": platform_message[0]["subject"], "color": platform_message[0]["color"]}
    
    return render_template("home2.html", url_prefix=url_prefix, has_premium=bool(user[0]["has_premium"]), is_verified=is_verified, username=username, status_message=platform_message)

@app.route("/chat", methods=["GET", "POST"])
def chat(error=None):
    if 'username' not in session:
        return redirect(f'{url_prefix}/')

    username = str(session['username']).lower()
    active_chats = []
    sql = SQLHelper.SQLHelper()

    if request.method == 'POST':
        # Post is used to create a new chat
        recipient = str(request.form['recipient'])

        # Check if recipient username is valid
        if recipient is None or recipient == username or len(recipient) > 20:
            return redirect(f'{url_prefix}/chat')

        # Check if recipient exists
        user_exists = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{recipient}'")

        if user_exists == []:
            # User does not exist
            return redirect(f'{url_prefix}/chat')

        else:
            # User exists
            return redirect(f'{url_prefix}/chat/{recipient}')

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
    return render_template('home.html', username=username, active_chats=active_chats, error=error, has_premium=user[0]["has_premium"], url_prefix = url_prefix, status_message=platform_message, verified=verified)

if __name__ == '__main__':
    app.run(debug=True)