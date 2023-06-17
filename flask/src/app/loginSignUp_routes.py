from flask import render_template, request, redirect, session, Blueprint
import random

from pythonHelper import EncryptionHelper, MongoDBHelper, MailHelper
from credentials import url_suffix


if url_suffix == "/gruettechat":
    path_template = "/application/templates"
else:
    path_template = "/application/templates"
    
loginSignUp_route = Blueprint("LoginSignUp", "LoginSignUp", template_folder=path_template)

eh = EncryptionHelper.EncryptionHelper()

@loginSignUp_route.route('/login', methods=['POST', 'GET'])
def login():
    if "signup" in request.form:
        return redirect(f'{url_suffix}/signup')
    elif request.method == "GET":
        return redirect(f'{url_suffix}/')
    
    db = MongoDBHelper.MongoDBHelper()
    username = str(request.form['username'])
    password = str(request.form['password'])
    
    # Check if input is valid
    if username == '' or password == '':
        return render_template('login.html', error='Please enter a username and password', url_suffix = url_suffix)
    
    # Search for user in database
    user = db.read('gruttechat_users', {"username": username})
    
    # If user exists, check if password is correct
    if user != []:
        decrypted_password = eh.decrypt_message(user[0]["password"])
        
        # If username and password are correct
        if user[0]["username"] == username and decrypted_password == password:
            
            # Check if the user has verified their account
            if bool(user[0]["is_verified"]) == False:
                return redirect(f'{url_suffix}/verify/{username}')
            
            # Log the user in
            else:
                session['username'] = username
                response = redirect(f'{url_suffix}/chat')
                response.set_cookie('username', username)
                return response

        # If password is or username is incorrect
        else:
            return render_template('login.html', error='Invalid login credentials', url_suffix = url_suffix)
        
    # If user does not exist
    else:
        return render_template('login.html', error='Invalid login credentials', url_suffix = url_suffix)

@loginSignUp_route.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        return redirect(f'{url_suffix}/chat')

    if request.method == 'POST':
        mail = MailHelper.MailHelper()
        db = MongoDBHelper.MongoDBHelper()
        username = str(request.form['username'])
        email = str(request.form['email'])
        password = str(request.form['password'])
        password_confirm = str(request.form['password2'])

        if password != password_confirm:
            return render_template('signup.html', error='Passwords do not match', url_suffix = url_suffix)
        elif username == '' or password == '':
            return render_template('signup.html', error='Please enter a username and password', url_suffix = url_suffix)
        elif len(username) > 20:
            return render_template('signup.html', error='Username must be less than 20 characters', url_suffix = url_suffix)
        elif len(password) > 40 or len(password) < 8:
            return render_template('signup.html', error='Password must be between 8 and 40 characters', url_suffix = url_suffix)
        elif '@' not in email or '.' not in email:
            return render_template('signup.html', error='Please enter a valid email address', url_suffix = url_suffix)

        search_username = db.read('gruttechat_users', {"username": username})

        if search_username != []:
            return render_template('signup.html', error='Username already exists', url_suffix = url_suffix)
        else:
            encrypted_password = str(eh.encrypt_message(str(password)))        
            verification_code = str(random.randint(100000, 999999))

            db.write('users', 
                     {"username": username, 
                      "password": encrypted_password, 
                      "email": email, 
                      "verification_code": verification_code, 
                      "is_verified": False, 
                      "has_premium": False, 
                      "ai_personality": 'Default', 
                      "premium_chat": False, 
                      "balance": 0})

            #mail.send_email(email, verification_code)
            return redirect(f'{url_suffix}/verify/{username}')

    return render_template('signup.html', url_suffix = url_suffix)

@loginSignUp_route.route('/verify/<username>', methods=['POST', 'GET'])
def verify(username):
    db = MongoDBHelper.MongoDBHelper()

    user = db.read('gruttechat_users', {"username": str(username)})

    if user == []:
        return redirect(f'{url_suffix}/')
    else:
        email = user[0]["email"]
        verification_code = user[0]["verification_code"]
        already_verified = user[0]["is_verified"]

        if request.method == 'POST':
            create_entered_code = str(request.form['code0']) + str(request.form['code1']) + str(request.form['code2']) + str(request.form['code3']) + str(request.form['code4']) + str(request.form['code5'])
            
            if create_entered_code == verification_code:
                db.update("gruttechat_users", 
                          {"$set": {"is_verified": True}},
                          {"username": str(username)})

                session['username'] = username
                response = redirect(f'{url_suffix}/chat')
                response.set_cookie('username', username)
                return response
            else:
                return render_template('verify.html', error='Invalid code', url_suffix = url_suffix, email=email, username=username)