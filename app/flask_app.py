from flask import Flask, abort, render_template, request, session, redirect, jsonify, send_from_directory, url_for
import logging
from threading import Thread
from flask_cors import CORS
from datetime import datetime

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

    
#@app.before_request
def maintenanceMode():
    if "user_id" not in session: return render_template('errors/maintenance.html'), 503
    sql = SQLHelper.SQLHelper()
    is_admin = bool(sql.readSQL(f"SELECT * FROM gruttechat_users WHERE id = '{session['user_id']}'")[0]["is_admin"])
    if is_admin: return
    else: return render_template('errors/maintenance.html'), 503

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
        elif error == "recaptcha_failed": error = "reCAPTCHA failed. Please try again."

        return render_template("discover.html", menu=th.user(session), error=error, traceback=request.args.get("traceback"))
    
@app.errorhandler(404)
def error404(error):
    return render_template("errors/404.html", menu=th.user(session)), 404

def errorToTicket(error, user_id=None):
    sql = SQLHelper.SQLHelper()
    if user_id:
        sql.writeSQL(f"INSERT INTO tickets (name, username, message, status) VALUES ('Error: 500', '{user_id}', '{error}', 'opened')")
    else:
        sql.writeSQL(f"INSERT INTO tickets (name, message, status) VALUES ('Error: 500', '{error}', 'opened')")

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
        
        return render_template('guest_views/chat.html', menu=th.user(session))

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

    # Fetch active chats and related user information in one query using SQL JOINs
    active_chats_query = f"""
        SELECT
            u.id AS user_id,
            u.username,
            u.profile_picture AS pfp,
            u.is_verified,
            IFNULL(b.blocked_user_id IS NOT NULL, 0) AS blocked,
            COUNT(DISTINCT unread.id) AS unread_messages,
            MAX(c.created_at) AS last_message_time,
            MAX(c.message_content) AS last_message
        FROM 
            chats c
        JOIN 
            users u ON (c.author_id = u.id AND c.recipient_id = '{int(user_id)}') OR (c.recipient_id = u.id AND c.author_id = '{int(user_id)}')
        LEFT JOIN 
            blocked_users b ON (b.user_id = u.id AND b.blocked_user_id = '{int(user_id)}') OR (b.user_id = '{int(user_id)}' AND b.blocked_user_id = u.id)
        LEFT JOIN 
            chats unread ON unread.author_id = u.id 
                    AND unread.recipient_id = '{int(user_id)}' 
                    AND unread.is_read = 0 

        WHERE 
            (c.author_id = '{int(user_id)}' AND c.recipient_id = u.id)
            OR (c.recipient_id = '{int(user_id)}' AND c.author_id = u.id)
        GROUP BY 
            u.id, u.username, u.profile_picture, u.is_verified, blocked
        ORDER BY 
            last_message_time DESC
    """

    # Execute the SQL query to get all active chats
    active_chats_database = sql.readSQL(active_chats_query)
    
    def last_message_time_ago(last_message_time):
        """ Helper function to format the last message time """
        time_now = datetime.now()
        time_difference = time_now - last_message_time
        if time_difference.days > 0:
            return f"{time_difference.days}d ago"
        elif time_difference.seconds // 3600 > 0:
            return f"{time_difference.seconds // 3600}h ago"
        elif time_difference.seconds // 60 > 0:
            return f"{time_difference.seconds // 60}m ago"
        else:
            return "Just now"

    # Prepare the active chats list
    active_chats = [
        {
            "user_id": chat["user_id"],
            "username": chat["username"],
            "pfp": chat["pfp"],
            "is_verified": chat["is_verified"],
            "blocked": bool(chat["blocked"]),
            "unread_messages": chat["unread_messages"],
            "last_message_time": last_message_time_ago(chat["last_message_time"]),
            "last_message": str(eh.decrypt_message(chat["last_message"])),
        }
        for chat in active_chats_database
    ]

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
    return render_template('messages.html', user=th.user(session), active_chats=active_chats, error=error, has_premium=user[0]["has_premium"], status_message=platform_message, verified=user[0]["is_verified"], is_admin=user[0]["is_admin"], suggested=suggested, pfp=f"{user[0]['profile_picture']}.png", selected_personality=user[0]["ai_personality"])





@app.route("/static-gruette-styles.css", methods=["GET"])
def static_css():
    return send_from_directory("static", "gruette-styles.css")

@app.route("/test", methods=["GET", "POST"])
def test():
    return render_template('content-components.html', user=th.user(session), chat=[])


if __name__ == '__main__':
    app.run(debug=True)