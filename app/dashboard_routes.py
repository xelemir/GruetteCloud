from flask import render_template, request, redirect, session, Blueprint, send_file, jsonify
from PIL import Image, ImageDraw, ImageOps
import os
import re
import pyotp

from pythonHelper import EncryptionHelper, SQLHelper, MailHelper, IconHelper, TemplateHelper
from config import templates_path, admin_users, gruetteStorage_path, logfiles_path, local_ip, render_path
    

dashboard_route = Blueprint("Dashboard", "Dashboard", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()
icon = IconHelper.IconHelper()
th = TemplateHelper.TemplateHelper()


# Helper function to convert file size to human-readable format
def get_formatted_file_size(size):
    """ Gets the formatted file size in KB, MB, GB or TB of a given file size in bytes.

    Args:
        size (int): The file size in bytes.

    Returns:
        str: The formatted file size in KB, MB, GB or TB.
    """    
    # 1 kilobyte (KB) = 1024 bytes
    # 1 megabyte (MB) = 1024 kilobytes
    # 1 gigabyte (GB) = 1024 megabytes
    # 1 terabyte (TB) = 1024 gigabytes

    power = 2 ** 10  # 1024
    n = 0
    power_labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

    while size > power:
        size /= power
        n += 1

    return f"{size:.2f} {power_labels[n]}"

@dashboard_route.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    """ Route to render the admins' dashboard page

    Returns:
        HTML: Rendered HTML page
    """

    if 'username' not in session:
        return redirect(f'/')
    elif session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()
    
    status = str(request.args.get('error'))
    if status == "None":
        status = None
    elif status == "otp":
        status = "Invalid OTP, please try again."
    elif status == "no_recipient":
        status = "No recipient specified."
    elif status == "invalid_recipient":
        status = "Invalid recipient specified."
    elif status == "sent":
        status = "Email(s) sent."
    elif status == "no_otp":
        status = "No auth secret found. Make sure you have set up 2FA enabled."
    
    platform_message = sql.readSQL(f"SELECT subject, color FROM gruttechat_platform_messages")
    if platform_message == []:
        platform_message = None
    else:
        platform_message = {"subject": platform_message[0]["subject"], "color": platform_message[0]["color"]}
    
    used_space_unformatted = sum(os.path.getsize(os.path.join(gruetteStorage_path, item)) for item in os.listdir(gruetteStorage_path))
    used_space = get_formatted_file_size(used_space_unformatted)
    used_space_percent = (used_space_unformatted / (8 * 1073741824)) * 100  # 8 GB

    all_users = sql.readSQL(f"SELECT username, email, has_premium FROM gruttechat_users")
        
    log_lines = []
    filtered_log_lines = []
    try:
        with open(f"{logfiles_path}access.log", 'r') as file:
            log_lines = file.read().splitlines()
        log_lines.reverse()

        for entry in log_lines:
            if str(local_ip) not in entry:
                if "python-requests" in entry:
                    continue
                elif "172.25." in entry:
                    continue
                date_regex = re.search(r'\[([^\]]+)\]', entry)
                ip_regex = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', entry)
                if date_regex is not None:
                    filtered_log_lines.append({"date": date_regex.group(1), "ip": ip_regex.group(0), "entry": entry.replace(f"[{date_regex.group(1)}]", "").replace(ip_regex.group(0), "")})
    except:
        pass
    
    return render_template('dashboard.html', menu=th.user(session), username=session['username'], used_space=used_space, used_space_percent=used_space_percent, platform_message=platform_message, all_users=all_users, events=filtered_log_lines, status=status)

@dashboard_route.route('/dashboard/createstatusmessage', methods=['POST'])
def create_status_message():
    """ Post route to create a new status message, which will be displayed on the app

    Returns:
        HTML: Redirect to the dashboard page
    """

    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')
    
    sql = SQLHelper.SQLHelper()

    subject = str(request.form["subject"])
    content = str(request.form["content"])
    color = str(request.form["color"])

    sql.writeSQL(f"DELETE FROM gruttechat_platform_messages")
    sql.writeSQL(f"INSERT INTO gruttechat_platform_messages (subject, content, color) VALUES ('{subject}', '{content}', '{color}')")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/deletestatusmessage')
def delete_status_message():
    """ Route to delete the current status message

    Returns:
        HTML: Redirect to the dashboard page
    """

    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"DELETE FROM gruttechat_platform_messages")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/deleteuser/<username>')
def delete_user(username):
    """ Route to delete a user from the database

    Args:
        username (str): The username of the user to delete

    Returns:
        HTML: Redirect to the dashboard page
    """

    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"DELETE FROM gruttechat_users WHERE username = '{username}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/giftplus/<username>')
def gift_plus(username):
    """ Route to gift a user GrütteCloud PLUS instantly and for free

    Args:
        username (str): The username of the user to gift GrütteCloud PLUS to

    Returns:
       HTML: Redirect to the dashboard page
    """

    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {True} WHERE username = '{username}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/revokeplus/<username>')
def revoke_plus(username):
    """ Route to revoke a user's GrütteCloud PLUS subscription, even if they paid for it

    Args:
        username (str): The username of the user to revoke GrütteCloud PLUS from

    Returns:
        HTML: Redirect to the dashboard page
    """

    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')

    sql = SQLHelper.SQLHelper()

    sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {False} WHERE username = '{username}'")

    return redirect(f'/dashboard')

@dashboard_route.route('/dashboard/sendemail', methods=['POST'])
def send_mail():
    """ Route to send an email to a specific or all users. Requires 2FA.

    Returns:
        HTML: Redirect to the dashboard page
    """
    
    if 'username' not in session or session['username'] not in admin_users:
        return redirect(f'/')
    
    email = MailHelper.MailHelper()
    sql = SQLHelper.SQLHelper()
    
    recipient_username = str(request.form["username"])
    subject = str(request.form["subject"])
    content = str(request.form["content"])
    otp = str(request.form["otp"])
    send_to_all = False
    if "sendtoall" in request.form:
        send_to_all = True
    
    # Get auth secret from db as users here must be admins
    user = sql.readSQL(f"SELECT 2fa_secret_key FROM gruttechat_users WHERE username = '{session['username']}'")
    if user == []:
        return redirect(f'/dashboard')
    try:
        totp = pyotp.TOTP(user[0]["2fa_secret_key"])
    except:
        return redirect(f'/dashboard?error=no_otp')

    # Validate the OTP
    if not totp.verify(otp):
        return redirect(f'/dashboard?error=otp')
    
    if recipient_username == "" and not send_to_all:
        return redirect(f'/dashboard?error=no_recipient')
    
    if not send_to_all:
    
        recipient = sql.readSQL(f"SELECT email, verification_code FROM gruttechat_users WHERE username = '{recipient_username}'")
    
        if recipient == []:
            return redirect(f'/dashboard?error=invalid_recipient')
            
        email.send_email(recipient[0]["email"], recipient_username, subject, content, token=recipient[0]["verification_code"])
        return redirect(f'/dashboard?error=sent')
    
    else:
        for user in sql.readSQL(f"SELECT username, email, receive_emails FROM gruttechat_users"):
            if bool(user["receive_emails"]):
                email.send_email(user["email"], user["username"], subject, content, token=user["verification_code"])
                
        return redirect(f'/dashboard?error=sent')
    
@dashboard_route.route("/create_render", methods=["GET", "POST"])
def createRender():
    if "username" not in session:
        return redirect("/")

    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")[0]
    
    renders_in_use_light = os.listdir(os.path.join(render_path, "light"))
    renders_in_use_dark = os.listdir(os.path.join(render_path, "dark"))
    
    if not bool(user["is_admin"]):
        return redirect("/")
    
    elif request.method == "GET":
        return render_template("createRender.html", menu=th.user(session), render_created=False, renders_in_use_light=renders_in_use_light, renders_in_use_dark=renders_in_use_dark)
    
    else:
        device_selection = request.form['device']
        screenshot_image = request.files["file"]
        darkMode = request.form['theme']
        
        screenshot_image.save(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "screenshot.png"))
        
        # Load the screenshot image
        screenshot_image = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "screenshot.png"))

        # Load the device frame
        device = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", f"{device_selection}.png"))

        # Load the navbar image
        if darkMode == "true":
            navbar_image = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "ChromeDark.png"))
        else:
            navbar_image = Image.open(os.path.join(gruetteStorage_path, "GruetteCloudRenders", "ChromeLight.png"))
        
        
        # Check the dimensions of the images
        width1, height1 = device.size
        width2, height2 = screenshot_image.size

        # Calculate the maximum dimensions
        max_width = max(width1, width2)
        max_height = max(height1, height2)
        
        if "iPhone" in device_selection:
            rad = 100
            # Create a circle mask for rounded corners
            circle = Image.new('L', (rad * 2, rad * 2), 0)
            draw = ImageDraw.Draw(circle)
            draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
            alpha = Image.new('L', screenshot_image.size, 255)

            # Apply rounded corners to the screenshot image
            alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
            alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, height2 - rad))
            alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (width2 - rad, 0))
            alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (width2 - rad, height2 - rad))
            screenshot_image.putalpha(alpha)

        # Create a new image with a transparent background
        result_image = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))

        # Calculate the position to center the screenshot
        x_offset2 = (max_width - width2) // 2
        y_offset2 = (max_height - height2) // 2

        # Paste the screenshot onto the new image
        result_image.paste(screenshot_image, (x_offset2, y_offset2))

        # Check if the device is an iPhone (to add the navbar)
        if "iPhone" in device_selection:
            
            # Paste the navbar image on top of the screenshot (adjust position as needed)
            result_image.paste(navbar_image, (x_offset2, y_offset2), navbar_image)

        # Paste the device frame onto the new image
        result_image.paste(device, (0, 0), device)

        # Save the final result
        result_image.save(os.path.join(render_path, "render.png"))

        
        return render_template("createRender.html", menu=th.user(session), render_created=True, renders_in_use_light=renders_in_use_light, renders_in_use_dark=renders_in_use_dark)