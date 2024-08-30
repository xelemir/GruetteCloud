from flask import Flask, abort, render_template, request, session, redirect, jsonify, send_from_directory, url_for
import logging
from threading import Thread
from flask_cors import CORS

from pythonHelper import EncryptionHelper, SQLHelper, TemplateHelper
from config import secret_key

from loginSignUp_routes import loginSignUp_route
from settings_routes import settings_route
from chat_routes import chat_route
from premium_routes import premium_route
from drive_routes import drive_route
from dashboard_routes import dashboard_route
from tool_routes import tool_route
from expense_tracker_routes import expense_tracker_route
from job_routes import job_route


app = Flask("GrütteCloud")
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = secret_key
app.permanent_session_lifetime = 1209600*2 # 4 weeks
app.register_blueprint(loginSignUp_route)
app.register_blueprint(settings_route)
app.register_blueprint(chat_route)
app.register_blueprint(premium_route)
app.register_blueprint(drive_route)
app.register_blueprint(dashboard_route)
app.register_blueprint(tool_route)
app.register_blueprint(expense_tracker_route)
app.register_blueprint(job_route)

eh = EncryptionHelper.EncryptionHelper()
th = TemplateHelper.TemplateHelper()


"""@app.before_request
def maintenanceMode():
    if "username" not in session: return render_template('errors/maintenance.html'), 503
    sql = SQLHelper.SQLHelper()
    is_admin = bool(sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")[0]["is_admin"])
    if is_admin: return
    else: return render_template('errors/maintenance.html'), 503"""

@app.route("/")
def index():
    if "user_id" in session:
        sql = SQLHelper.SQLHelper()
        try:
            default_app = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")[0]["default_app"]
        except IndexError:
            logging.error(f"Index error for default app of user {session['user_id']}")
            default_app = "chat"
        return redirect(f"/{default_app}")
    
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
        elif error == "too_many_login_attempts": error = "Too many login attempts. Contact support or use a different device."

        return render_template("discover.html", menu=th.user(session), error=error, traceback=request.args.get("traceback"))
    
@app.errorhandler(404)
def error404(error):
    return render_template("errors/404.html", menu=th.user(session)), 404

def errorToTicket(error, user_id=None):
    sql = SQLHelper.SQLHelper()
    if user_id:
        sql.writeSQL(f"INSERT INTO tickets (username, message, status) VALUES ('{user_id}', '{error}', 'opened')")
    else:
        sql.writeSQL(f"INSERT INTO tickets (message, status) VALUES ('{error}', 'opened')")

@app.route("/404")
def error404page():
    return abort(404)

@app.errorhandler(401)
def error401(error):
    return render_template("errors/401.html", menu=th.user(session)), 401

@app.errorhandler(500)
def error500(error):
    # Return 500 page to user instantly and create a ticket in the background
    if "user_id" in session:
        user_id = session["user_id"]
    else:
        user_id = None

    Thread(target=errorToTicket, args=(f"{str(error)} Route: {str(request.path)}", user_id)).start()
    return render_template("errors/500.html", menu=th.user(session)), 500

@app.route("/500")
def error500page():
    return abort(500)

@app.route("/401")
def error401page():
    return abort(401)

@app.route("/maintenance")
def maintenance():
    return render_template("errors/maintenance.html", menu=th.user(session))

@app.route("/chat", methods=["GET", "POST"])
def chat(error=None):
    """ Route to render the chat home page

    Args:
        error (str, optional): Error message to display. Defaults to None.

    Returns:
        HTML: Rendered HTML page
    """    
    if 'user_id' not in session:
        return redirect('/')

    user_id = str(session['user_id'])
    active_chats = []
    sql = SQLHelper.SQLHelper()

    if request.method == "POST":
        # Post is used to create a new chat
        recipient_id = str(request.form['recipient_id'])

        # Check if recipient user_id valid
        if recipient_id is None or recipient_id == user_id or len(recipient_id) > 10:
            return redirect('/chat')

        # Check if recipient exists
        user_exists = sql.readSQL(f"SELECT * FROM users WHERE id = '{int(recipient_id)}'")

        if user_exists == []:
            # User does not exist
            return redirect("/chat")

        else:
            # User exists
            return redirect(f'/chat/{recipient_id}')

    # Fetch active chats from the database
    active_chats_database = sql.readSQL(f"SELECT * FROM chats WHERE author_id = '{int(user_id)}' OR recipient_id = '{int(user_id)}'")
                
    # Add all active chats to a list
    for chat in active_chats_database:
        if chat["author_id"] == int(user_id):
            if chat["recipient_id"] not in [x["user_id"] for x in active_chats]:
                unread_messages = len(sql.readSQL(f"SELECT * FROM chats WHERE author_id = '{chat['recipient_id']}' AND recipient_id = '{user_id}' AND is_read = '{False}'"))
                user_db = sql.readSQL(f"SELECT * FROM users WHERE id = '{chat['recipient_id']}'")
                blocked = bool(sql.readSQL(f"SELECT * FROM blocked_users WHERE user_id = '{chat['recipient_id']}' AND blocked_user_id = '{user_id}' OR user_id = '{user_id}' AND blocked_user_id = '{chat['recipient_id']}'"))
                if user_db != []:
                    active_chats.append({"user_id": chat["recipient_id"], "username": user_db[0]["username"], "pfp": user_db[0]["profile_picture"], "is_verified": user_db[0]["is_verified"], "blocked": blocked, "unread_messages": unread_messages})
        else:
            if chat["author_id"] not in [x["user_id"] for x in active_chats]:
                unread_messages = len(sql.readSQL(f"SELECT * FROM chats WHERE author_id = '{chat['author_id']}' AND recipient_id = '{user_id}' AND is_read = '{False}'"))
                user_db = sql.readSQL(f"SELECT * FROM users WHERE id = '{chat['author_id']}'")
                blocked = bool(sql.readSQL(f"SELECT * FROM blocked_users WHERE user_id = '{chat['author_id']}' AND blocked_user_id = '{user_id}' OR user_id = '{user_id}' AND blocked_user_id = '{chat['author_id']}'"))
                if user_db != []:    
                    active_chats.append({"user_id": chat["author_id"], "username": user_db[0]["username"], "pfp": user_db[0]["profile_picture"], "is_verified": user_db[0]["is_verified"], "blocked": blocked, "unread_messages": unread_messages})
    
    # Get user's premium status
    user = sql.readSQL(f"SELECT * FROM users WHERE id = '{user_id}'")
    
    if user == []:
        # Safety check
        return redirect('/logout')
    
    platform_message = sql.readSQL(f"SELECT * FROM platform_notifications")
    
    if platform_message == []:
        platform_message = None
    else:
        platform_message = {"created_at": platform_message[0]["created_at"], "content": platform_message[0]["content"], "subject": platform_message[0]["subject"], "color": platform_message[0]["color"], "link": platform_message[0]["link"], "decorator": platform_message[0]["decorator"]}
    
    if active_chats == []:
        suggest_jan = sql.readSQL(f"SELECT * FROM users WHERE username = 'jan'")
        suggest_random = sql.readSQL(f"SELECT * FROM users WHERE id != '{user_id}' AND username != 'jan' ORDER BY RAND() LIMIT 2")
        suggested = [{"user_id": suggest_jan[0]["id"], "username": suggest_jan[0]["username"], "pfp": f"{suggest_jan[0]['profile_picture']}.png", "is_verified": suggest_jan[0]["is_verified"]}]
        for suggest_user in suggest_random:
            suggested.append({"user_id": suggest_user["id"], "username": suggest_user["username"], "pfp": f"{suggest_user['profile_picture']}.png", "is_verified": suggest_user["is_verified"]})
    else:
        suggested = None
    
    # Render the home page
    return render_template('chathome.html', menu=th.user(session), active_chats=active_chats, error=error, has_premium=user[0]["has_premium"], status_message=platform_message, verified=user[0]["is_verified"], is_admin=user[0]["is_admin"], suggested=suggested, pfp=f"{user[0]['profile_picture']}.png", selected_personality=user[0]["ai_personality"])

if __name__ == '__main__':
    app.run(debug=True)