from flask import Flask, render_template, request, session, redirect, jsonify

from pythonHelper import EncryptionHelper, SQLHelper

from loginSignUp_routes import loginSignUp_route
from utilities_routes import utilities_route
from chat_routes import chat_route
from premium_routes import premium_route
from gruetteStorage_routes import gruetteStorage_route
from dashboard_routes import dashboard_route

from config import url_prefix

app = Flask("GrütteChat")
app.secret_key = 'supersecretkey'
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
    elif "username" in request.cookies:
        session["username"] = request.cookies["username"]
        return redirect(f"{url_prefix}/chat")
    else:
        return render_template("login.html", url_prefix = url_prefix)

@app.route("/chat", methods=["GET", "POST"])
def chat(error=None):
    if 'username' not in session:
        return redirect(f'{url_prefix}/')

    username = str(session['username'])
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
        if chat["username_send"] == username:
            active_chats.append(chat["username_receive"])
        else:
            active_chats.append(chat["username_send"])
    
    # Get user's premium status
    user = sql.readSQL(f"SELECT has_premium FROM gruttechat_users WHERE username = '{username}'")
    
    platform_message = sql.readSQL(f"SELECT created_at, content, subject, color FROM gruttechat_platform_messages")
    
    if platform_message == []:
        platform_message = None
    else:
        platform_message = {"created_at": platform_message[0]["created_at"], "content": platform_message[0]["content"], "subject": platform_message[0]["subject"], "color": platform_message[0]["color"]}
    
    # Render the home page
    return render_template('home.html', username=username, active_chats=set(active_chats), error=error, has_premium=user[0]["has_premium"], url_prefix = url_prefix, status_message=platform_message)

if __name__ == '__main__':
    app.run(debug=True)