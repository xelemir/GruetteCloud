from flask import render_template, request, redirect, session, Blueprint, Flask, url_for
import random
import pyotp
from werkzeug.security import generate_password_hash, check_password_hash

from pythonHelper import SQLHelper, MailHelper, TemplateHelper
from config import templates_path
    
loginSignUp_route = Blueprint("LoginSignUp", "LoginSignUp", template_folder=templates_path)

th = TemplateHelper.TemplateHelper()

@loginSignUp_route.route('/login', methods=['POST', 'GET'])
def login():
    """ Post route to login. If 2fa is enabled, redirect to 2fa page and set session variable username_2fa instead of username
        as username is used to entirly log the user in.

    Returns:
        HTML: Rendered HTML page
    """

    if "signup" in request.form:
        return redirect(f'/signup')
    elif request.method == "GET":
        # Deprecated, simply used as people might have the old url saved
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    username = str(request.form['username']).lower()
    password = str(request.form['password'])
    
    # Check if input is valid
    if username == '' or password == '':
        return redirect("/?error=username_or_password_empty&traceback=login")
    
    # Search for user in database
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    
    # If user exists, check if password is correct
    if user != []:
        # If username and password are correct
        if user[0]["username"].lower() == username and check_password_hash(user[0]["password"], password):
            
            # Check if the user has verified their account
            if bool(user[0]["is_email_verified"]) == False:
                return redirect(f'/verify/{username}')
            
            # Check if 2FA is enabled
            if bool(user[0]["is_2fa_enabled"]) == True:
                session['username_2fa'] = username
                return redirect(url_for("LoginSignUp.two_fa", target=request.args.get('target')))
            
            # Log the user in
            else:
                session['username'] = username
                session.permanent = True
                return redirect(url_for("index", target=request.args.get('target')))

        # If password is or username is incorrect
        else:
            return redirect("/?error=invalid_credentials&traceback=login")
        
    # If user does not exist
    else:
        return redirect("/?error=invalid_credentials&traceback=login")
    
@loginSignUp_route.route('/2fa', methods=['GET', 'POST'])
def two_fa():
    """ Route to render the 2fa page if 2fa is enabled

    Returns:
        HTML: Rendered HTML page
    """

    if "username" in session or "username_2fa" not in session:
        return redirect(f'/')
    if request.method == "GET":
        return render_template('2fa.html', username=session['username_2fa'])
    if request.method == "POST":
        sql = SQLHelper.SQLHelper()
        
        entered_code = str(request.form['code0']) + str(request.form['code1']) + str(request.form['code2']) + str(request.form['code3']) + str(request.form['code4']) + str(request.form['code5'])
        username = session['username_2fa']
    
        user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
        user_secret_key = user[0]["2fa_secret_key"]
        
        totp = pyotp.TOTP(user_secret_key)

        # Validate the OTP
        if totp.verify(entered_code):
            session.pop('username_2fa', None)
            session['username'] = username
            session.permanent = True
            return redirect(url_for("index", target=request.args.get('target')))
        
        else:
            return render_template('2fa.html', error="Invalid code", username=username)

@loginSignUp_route.route('/signup', methods=['GET', 'POST'])
def signup():
    """ Post route to signup and create a new user.

    Returns:
        HTML: Rendered HTML page
    """
    
    if 'username' in session:
        return redirect(f'/')
    
    # If Method is POST
    if request.method == 'POST':
        
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
        elif [char for char in username if char in ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '{', '}', '[', ']', '|', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/']] != []:
            return redirect("/?error=forbidden_characters")
        elif len(username) >= 40:
            return redirect("/?error=username_less_40")
        elif [blocked_phrase for blocked_phrase in ['gruette', 'grütte', 'grutte', 'admin', 'support', 'delete', 'administrator', 'moderator', 'mod', 'gruettecloudrenders', 'gruettecloud', 'grüttecloud', 'gruettechat', 'grüttechat'] if blocked_phrase in username] != []:
            return redirect("/?error=forbidden_words")
        elif len(password) > 40 or len(password) < 8:
            return redirect("/?error=password_between_8_40")
        elif '@' not in email or '.' not in email:
            return redirect("?error=invalid_email")
        
        # Check if the username already exists
        search_username = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
        if search_username != []:
            return redirect("/?error=username_already_exists")
        
        # Else create new user
        else:
            hashed_password = generate_password_hash(password)
            verification_code = str(random.randint(100000, 999999))

            # Insert the user into the database
            sql.writeSQL(f"INSERT INTO gruttechat_users (username, password, email, verification_code, is_email_verified, has_premium, ai_personality, is_2fa_enabled, 2fa_secret_key, profile_picture, default_app, phone, first_name, last_name) VALUES ('{username}', '{hashed_password}', '{email}', '{verification_code}', {False}, {False}, 'Default', {False}, 0, '{random.choice(['blue', 'green', 'purple', 'red', 'yellow'])}', 'chat', '{phone}', '{first_name}', '{last_name}')")
            
            # Send the email
            mail.send_verification_email(email, username, verification_code)
            
            # Redirect to verification page
            return redirect(f"/verify/{username}")

    # If Method is GET, render the signup page, deprecated, simply used as people might have the old url saved TODO remove
    return redirect("/")

@loginSignUp_route.route("/username_available/<username>")
def username_available(username):
    """ Route to check if a username is available

    Args:
        username (str): The username to check

    Returns:
        str: True if the username is available, False if not
    """

    sql = SQLHelper.SQLHelper()
    search_username = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
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
    
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()

    if username.startswith("email: "):
        email = username.replace("email: ", "")
        search_username = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE email = '{email}'")
    elif username.startswith("phone: "):
        phone = username.replace("phone: ", "")
        search_username = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE phone = '{phone}'")
    elif username.startswith("name: "):
        name = username.replace("name: ", "")
        search_username = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE first_name LIKE '%{name}%' OR last_name LIKE '%{name}%'")
    else:
        search_username = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username LIKE '%{username}%'")
    
    # Dict because WSGI cries otherwise
    return {"users": [{"username": user["username"], "profile_picture": user["profile_picture"], "is_verified": user["is_verified"]} for user in search_username][:5]}

@loginSignUp_route.route('/verify/<username>' , methods=['GET', 'POST'])
def verify(username):
    """ Route to verify the user's email. If the user is already verified, redirect to home page.

    Args:
        username (str): The username of the user to verify

    Returns:
        HTML: Rendered HTML page
    """

    if "username" in session or username is None:
        return redirect('/')
    
    error = None
    username = str(username).lower()
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(username)}'")
    
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
                sql.writeSQL(f"UPDATE gruttechat_users SET is_email_verified = {True} WHERE username = '{str(username)}'")
                session['username'] = username
                session.permanent = True
                return redirect(f'/')
            
            # If the code is incorrect, display an error
            else:
                error = "The code you entered is incorrect"
    
    # Render the verification page
    return render_template('verify.html', username=username, error=error, email=email, already_verified=already_verified)

@loginSignUp_route.route('/verify/<username>/<code>')
def verify_code(username, code):
    """ Route to auto verify the user's email via the token in the url.
        TODO: Merge this route with the verify route and use request.args.get('code') instead of code as an argument

    Args:
        username (str): The username of the user to verify
        code (str): The verification code

    Returns:
        HTML: Rendered HTML page
    """    
    if "username" in session or username is None:
        return redirect(f'/')
    
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(username)}'")
    
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
        
        # Check if the code is correct, if so, verify the user and log them in
        if code == verification_code:
            sql.writeSQL(f"UPDATE gruttechat_users SET is_email_verified = {True} WHERE username = '{str(username)}'")
            session['username'] = username
            session.permanent = True
            return redirect(f'/')
        
        # If the code is incorrect, display an error
        else:
            error = "The code you entered is incorrect"
    
    # Render the verification page
    return render_template('verify.html', username=username, error=error, email=email, already_verified=already_verified)