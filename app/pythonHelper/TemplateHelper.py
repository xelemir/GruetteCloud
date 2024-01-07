import pythonHelper.SQLHelper as SQLHelper
import subprocess

class TemplateHelper:
    def __init__(self):
        pass
    
    def get_last_commit_id(self):
        try:
            result = subprocess.check_output(['git', 'rev-parse', 'HEAD'])
            last_commit_id = result.decode('utf-8').strip()
            return last_commit_id
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"
    
    def user(self, session):
        if "username" not in session:
            return
        
        sql = SQLHelper.SQLHelper()
        user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")
        if user == []:
            return
        
        return {"username": user[0]["username"], "pfp": user[0]["profile_picture"], "admin": bool(user[0]["is_admin"]), "premium": bool(user[0]["has_premium"]), "version": self.get_last_commit_id()}