import logging
from flask import render_template, request, redirect, session, Blueprint, Flask, url_for
import random
import pyotp
import requests
from werkzeug.security import generate_password_hash, check_password_hash

from pythonHelper import SQLHelper, MailHelper, TemplateHelper
from config import templates_path, recaptcha_secret_key
    
loginSignUp_route = Blueprint("LoginSignUp", "LoginSignUp", template_folder=templates_path)

th = TemplateHelper.TemplateHelper()

@loginSignUp_route.route("/login", methods=["POST", 'GET'])
def login():
    """ Post route to login. If 2fa is enabled, redirect to 2fa page and set session variable user_id_2fa instead of user_id
        as user_id is used to entirly log the user in.

    Returns:
        HTML: Rendered HTML page
    """
    
    if session.get('login_attempts', 0) >= 5:
        return redirect("/?error=too_many_login_attempts&traceback=login")

    if "signup" in request.form:
        return redirect("/signup")
    elif request.method == "GET":
        # Deprecated, simply used as people might have the old url saved
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    username = str(request.form["username"]).lower()
    password = str(request.form["password"])
    
    # Check if input is valid
    if username == '' or password == '':
        return redirect("/?error=username_or_password_empty&traceback=login")
    
    # Search for user in database
    user = sql.readSQL(f"SELECT * FROM users WHERE username = '{username}'")
    
    # If user exists, check if password is correct
    if user != []:
        # If username and password are correct
        if user[0]["username"].lower() == username and check_password_hash(user[0]["password"], password):
            
            # Check if the user has verified their account
            if bool(user[0]["is_email_verified"]) == False:
                session.pop('login_attempts', None)
                return redirect(f'/verify/{username}')
            
            # Check if 2FA is enabled
            if bool(user[0]["is_2fa_enabled"]) == True:
                session['user_id_2fa'] = user[0]["id"]
                session.pop('login_attempts', None)
                return redirect(url_for("LoginSignUp.two_fa", target=request.args.get('target')))
            
            # Log the user in
            else:
                session.pop('login_attempts', None)
                session['user_id'] = user[0]["id"]
                session.permanent = True
                return redirect(url_for("index", target=request.args.get('target')))

    # If the user does not exist or the password is incorrect
    session['login_attempts'] = session.get('login_attempts', 0) + 1
    return redirect("/?error=invalid_credentials&traceback=login")
    
@loginSignUp_route.route('/2fa', methods=['GET', 'POST'])
def two_fa():
    """ Route to render the 2fa page if 2fa is enabled

    Returns:
        HTML: Rendered HTML page
    """

    if "user_id" in session or "user_id_2fa" not in session:
        return redirect(f'/')
    if request.method == "GET":
        return render_template('2fa.html')
    if request.method == "POST":
        sql = SQLHelper.SQLHelper()
        
        entered_code = str(request.form['code0']) + str(request.form['code1']) + str(request.form['code2']) + str(request.form['code3']) + str(request.form['code4']) + str(request.form['code5'])
    
        user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id_2fa']}'")
        user_secret_key = user[0]["2fa_secret_key"]
                
        totp = pyotp.TOTP(user_secret_key)

        # Validate the OTP
        if totp.verify(entered_code):
            session.pop('user_id_2fa', None)
            session['user_id'] = user[0]["id"]
            session.permanent = True
            return redirect(url_for("index", target=request.args.get('target')))
        
        else:
            return render_template('2fa.html', error="Invalid code")

@loginSignUp_route.route('/signup', methods=['GET', 'POST'])
def signup():
    """ Post route to signup and create a new user.

    Returns:
        HTML: Rendered HTML page
    """
    
    if 'user_id' in session:
        return redirect(f'/')
    
    # If Method is POST
    if request.method == 'POST':
        
        # Check if reCAPTCHA response is valid
        recaptcha_response = request.form.get('g-recaptcha-response')
        
        # Verify the reCAPTCHA response with Google's API
        data = {
            'secret': recaptcha_secret_key,
            'response': recaptcha_response
        }
        
        # Make a POST request to Google reCAPTCHA API
        verify_response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = verify_response.json()

        # Check if reCAPTCHA score is above the threshold
        if result['success'] and result['score'] >= 0.5:
            mail = MailHelper.MailHelper()
            sql = SQLHelper.SQLHelper()
            first_name = str(request.form['first_name'])
            last_name = str(request.form['last_name'])
            if last_name == "": last_name = "0"
            username = str(request.form['username']).lower()
            email = str(request.form['email']).lower()
            phone = str(request.form['phone'])
            if phone == "": phone = "0"
            password = str(request.form['password'])
            password_confirm = str(request.form['password2'])
                    
            # Check if input is valid
            if password != password_confirm:
                return redirect("/?error=passwords_not_matching")
            elif username == '' or password == '':
                return redirect("/?error=username_or_password_empty")
            elif [char for char in username if char in ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '{', '}', '[', ']', '|', '\\', ':', ';', '"', "'", '<', '>', ',', ' ', '?', '/']] != []:
                return redirect("/?error=forbidden_characters")
            elif len(username) >= 40:
                return redirect("/?error=username_less_40")
            elif [blocked_phrase for blocked_phrase in ['gruette', 'grütte', 'grutte', 'admin', 'support', 'delete', 'administrator', 'moderator', 'mod', 'gruettecloudrenders', 'gruettecloud', 'grüttecloud', 'gruettechat', 'grüttechat', 'nelly'] if blocked_phrase in username] != []:
                return redirect("/?error=forbidden_words")
            elif len(password) > 40 or len(password) < 8:
                return redirect("/?error=password_between_8_40")
            elif '@' not in email or '.' not in email:
                return redirect("?error=invalid_email")
            
            # Check if the username already exists
            search_username = sql.readSQL(f"SELECT * FROM users WHERE username = '{username}'")
            if search_username != []:
                return redirect("/?error=username_already_exists")
            
            # Else create new user
            else:
                hashed_password = generate_password_hash(password)
                verification_code = str(random.randint(100000, 999999))

                # Insert the user into the database
                sql.writeSQL(f"INSERT INTO users (username, password, email, verification_code, is_email_verified, has_premium, ai_personality, is_2fa_enabled, 2fa_secret_key, profile_picture, default_app, phone, first_name, last_name, finance_budget, ai_model) VALUES ('{username}', '{hashed_password}', '{email}', '{verification_code}', {False}, {False}, 'Default', {False}, 0, '{random.choice(['blue', 'green', 'purple', 'red', 'yellow'])}', 'chat', '{phone}', '{first_name}', '{last_name}', 350, 'gpt-4o-mini')")
                
                # Send the email
                mail.send_verification_email(email, username, verification_code)
                
                # Redirect to verification page
                return redirect(f"/verify/{username}")

        # If Method is GET, render the signup page, deprecated, simply used as people might have the old url saved TODO remove
        return redirect("/")
    
    # Recaptcha failed
    else:
        return redirect("/?error=recaptcha_failed")
            
        
        

@loginSignUp_route.route("/username_available/<username>")
def username_available(username):
    """ Route to check if a username is available

    Args:
        username (str): The username to check

    Returns:
        str: True if the username is available, False if not
    """

    sql = SQLHelper.SQLHelper()
    search_username = sql.readSQL(f"SELECT * FROM users WHERE username = '{username}'")
    if search_username != []:
        return {"available": False}
    else:
        return {"available": True}
    
@loginSignUp_route.route('/search_username/<username>')
def search_username(username):
    """ Route to search for usernames that start with the input

    Args:
        username (str): The username to search for

    Returns:
        list: List of usernames that start with the input
    """
    
    if "user_id" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()

    if username.startswith("email: "):
        email = username.replace("email: ", "")
        search_username = sql.readSQL(f"SELECT * FROM users WHERE email = '{email}'")
    elif username.startswith("phone: "):
        phone = username.replace("phone: ", "")
        search_username = sql.readSQL(f"SELECT * FROM users WHERE phone = '{phone}'")
    elif username.startswith("name: "):
        name = username.replace("name: ", "")
        search_username = sql.readSQL(f"SELECT * FROM users WHERE first_name LIKE '%{name}%' OR last_name LIKE '%{name}%'")
    else:
        search_username = sql.readSQL(f"SELECT * FROM users WHERE username LIKE '%{username}%'")
    
    # Dict because WSGI cries otherwise
    return {"users": [{"user_id": user["id"], "username": user["username"], "profile_picture": user["profile_picture"], "is_verified": user["is_verified"]} for user in search_username][:5]}

@loginSignUp_route.route('/verify/<username>' , methods=['GET', 'POST'])
def verify(username):
    """ Route to verify the user's email. If the user is already verified, redirect to home page.

    Args:
        username (str): The username of the user to verify

    Returns:
        HTML: Rendered HTML page
    """

    if "user_id" in session or username is None:
        return redirect('/')
    
    error = None
    username = str(username).lower()
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM users WHERE username = '{str(username)}'")
    
    # User does not exist
    if user == []:
        return redirect(f'/')
    
    # User exists
    else:
        # Get email and verification code from database 
        email = user[0]["email"]
        verification_code = user[0]["verification_code"]
        already_verified = user[0]["is_email_verified"]
        
        if bool(already_verified):
            return render_template('verify.html', username=username, email=email, already_verified=already_verified)

        # If post request, check if the verification code is correct
        if request.method == 'POST':
            
            # Create code from input
            create_entered_code = str(request.form['code0']) + str(request.form['code1']) + str(request.form['code2']) + str(request.form['code3']) + str(request.form['code4']) + str(request.form['code5'])
            
            # Check if the code is correct, if so, verify the user and log them in
            if create_entered_code == verification_code:
                sql.writeSQL(f"UPDATE users SET is_email_verified = {True} WHERE username = '{str(username)}'")
                session['user_id'] = user[0]["id"]
                session.permanent = True
                return redirect(f'/')
            
            # If the code is incorrect, display an error
            else:
                error = "The code you entered is incorrect"
    
    # Render the verification page
    return render_template('verify.html', username=username, error=error, email=email, already_verified=already_verified)    


@loginSignUp_route.route('/check_2fa', methods=['GET', 'POST'])
def check_2fa():
    if "user_id" not in session:
        return redirect('/')

    if request.method == "POST":
        sql = SQLHelper.SQLHelper()
        user = sql.readSQL(f"SELECT * FROM users WHERE id = '{session['user_id']}'")
        user_secret_key = user[0]["2fa_secret_key"]
        
        entered_code = request.form['code']
        
        totp = pyotp.TOTP(user_secret_key)

        # Validate the OTP
        if totp.verify(entered_code):
            return render_template('check_2fa.html', success=True)
        
        else:
            return render_template('check_2fa.html', success=False)
        
    return render_template('check_2fa.html')