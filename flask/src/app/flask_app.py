from flask import Flask, render_template, request, session, redirect, jsonify

from pythonHelper import EncryptionHelper, MongoDBHelper

from loginSignUp_routes import loginSignUp_route
from utilities_routes import utilities_route
from chat_routes import chat_route
from premium_routes import premium_route

from credentials import url_suffix

app = Flask("GrütteChat")
app.secret_key = 'supersecretkey'
app.register_blueprint(loginSignUp_route)
app.register_blueprint(utilities_route)
app.register_blueprint(chat_route)
app.register_blueprint(premium_route)

eh = EncryptionHelper.EncryptionHelper()
db = MongoDBHelper.MongoDBHelper()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(f'{url_suffix}/chat')
    elif 'username' in request.cookies:
        session['username'] = request.cookies['username']
        return redirect(f'{url_suffix}/chat')
    else:
        return render_template("login.html", url_suffix=url_suffix)

@app.route('/chat', methods=['GET', 'POST'])
def chat(error=None):
    if 'username' not in session:
        return redirect(f'{url_suffix}/')

    username = str(session['username'])
    active_chats = []

    if request.method == 'POST':
        # Post is used to create a new chat
        recipient = str(request.form['recipient'])

        # Check if recipient username is valid
        if recipient is None or recipient == username or len(recipient) > 20:
            return redirect(f'{url_suffix}/chat')

        # Check if recipient exists
        user_exists = db.read('users', {"username": recipient})

        if user_exists == []:
            # User does not exist
            return redirect(f'{url_suffix}/chat')

        else:
            # User exists
            return redirect(f'{url_suffix}/chat/{recipient}')

    # Fetch active chats from the database
    active_chats_database = db.read('messages', {"$or": [{"username_send": username}, {"username_receive": username}]})
    
    # Add all active chats to a list
    for chat in active_chats_database:
        if chat["username_send"] == username:
            active_chats.append(chat["username_receive"])
        else:
            active_chats.append(chat["username_send"])
    
    # Get user's premium status
    user = db.read('users', {"username": username})
    
    # Render the home page
    return render_template('home.html', username=username, active_chats=set(active_chats), error=error, has_premium=user[0]["has_premium"], url_suffix=url_suffix)

if __name__ == '__main__':
    app.run(debug=True)
