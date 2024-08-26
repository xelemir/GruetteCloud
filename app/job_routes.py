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
        
    errors = []
    
    myai_path = os.path.join("/home/jan/wwwroot/gruettecloud/gruetteDrive/", 'myai')

    files = os.listdir(myai_path)

    for file in files:
        # Delete files older than 14 days
        try:
            path = os.path.join(myai_path, file)
            time_created = os.path.getctime(path)
            date = datetime.fromtimestamp(time_created)
            if (datetime.now() - date).days > 14:
                os.remove(path)
                
        except Exception as e:
            errors.append({"file": file, "error": str(e)})
            print(e)
    
    mail = MailHelper.MailHelper()
    sql = SQLHelper.SQLHelper()
    
    admin = sql.readSQL(f"SELECT first_name, email FROM users WHERE username = 'jan'")[0]
    
    html = render_template("emails/report.html", errors=errors, username=admin["first_name"], job_name="Deletion of old MyAI files", date=datetime.now().strftime("%d.%m.%Y"), time=datetime.now().strftime("%H:%M:%S"))
    
    mail.send_email_no_template(admin["email"], "GrütteCloud Daily Report", html)
    
    
    return jsonify({"status": "success"}), 200