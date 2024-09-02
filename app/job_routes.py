import os
from datetime import datetime
from flask import abort, jsonify, render_template, request, redirect, send_file, session, Blueprint, url_for

from pythonHelper import TemplateHelper, MailHelper, SQLHelper
from config import templates_path, job_secret, gruettedrive_path


job_route = Blueprint("Jobs", "Jobs", template_folder=templates_path)
th = TemplateHelper.TemplateHelper()

@job_route.route("/run-jobs", methods=["POST"])
def run_job():    
    # Check if secret is correct
    if request.headers.get("secret") != job_secret:
        return jsonify({"status": "error", "message": "Invalid secret"}), 401
       
    # Delete old MyAI files 
    myai_path = os.path.join("/home/jan/www/drive/", 'myai')
    myai_files = os.listdir(myai_path)
    myai_error = False
    
    for file in myai_files:
        # Delete files older than 14 days
        try:
            path = os.path.join(myai_path, file)
            time_created = os.path.getctime(path)
            date = datetime.fromtimestamp(time_created)
            if (datetime.now() - date).days > 14:
                os.remove(path)
                
        except Exception as e:
            myai_error = e
            print(e)
            
    # Clear log files daily
    log_error = False

    try:
        with open(os.path.join("/var/log/apache2", "error.log"), "w") as file:
            file.write("")
        with open(os.path.join("/var/log/apache2", "access.log"), "w") as file:
            file.write("")
            
    except Exception as e:
        log_error = e
        print(e)
    
    # Send email to admin
        
    mail = MailHelper.MailHelper()
    sql = SQLHelper.SQLHelper()
    
    admin = sql.readSQL(f"SELECT first_name, email FROM users WHERE username = 'jan'")[0]
    
    html = render_template("emails/report.html", myai_error=myai_error, log_error=log_error, username=admin["first_name"], job_name="Daily Data Purge and Optimization Task", date=datetime.now().strftime("%d.%m.%Y"), time=datetime.now().strftime("%H:%M:%S"))
    
    mail.send_email_no_template(admin["email"], "GrütteCloud Daily Report", html)
    
    
    return jsonify({"status": "success"}), 200