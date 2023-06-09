from flask import Flask, render_template, request, session, redirect, jsonify

from pythonHelper import EncryptionHelper, SQLHelper

from loginSignUp_routes import loginSignUp_route
from utilities_routes import utilities_route
from chat_routes import chat_route
from premium_routes import premium_route


app = Flask("GrütteChat")
app.secret_key = 'supersecretkey'
app.register_blueprint(loginSignUp_route)
app.register_blueprint(utilities_route)
app.register_blueprint(chat_route)
app.register_blueprint(premium_route)

eh = EncryptionHelper.EncryptionHelper()

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/chat')
    elif 'username' in request.cookies:
        session['username'] = request.cookies['username']
        return redirect('/chat')
    else:
        return render_template("login.html")

@app.route('/chat', methods=['GET', 'POST'])
def chat(error=None):
    if 'username' not in session:
        return redirect('/')

    username = str(session['username'])
    active_chats = []
    sql = SQLHelper.SQLHelper()

    if request.method == 'POST':
        # Post is used to create a new chat
        recipient = str(request.form['recipient'])

        # Check if recipient username is valid
        if recipient is None or recipient == username or len(recipient) > 20:
            return redirect('/chat')

        # Check if recipient exists
        user_exists = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{recipient}'")

        if user_exists == []:
            # User does not exist
            return redirect('/chat')

        else:
            # User exists
            return redirect(f'/chat/{recipient}')

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
    
    # Render the home page
    return render_template('home.html', username=username, active_chats=set(active_chats), error=error, has_premium=user[0]["has_premium"])

if __name__ == '__main__':
    app.run(debug=True)