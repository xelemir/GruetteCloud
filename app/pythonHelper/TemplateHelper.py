import pythonHelper.SQLHelper as SQLHelper

class TemplateHelper:
    def __init__(self):
        pass
    
    def user(self, session):
        if "username" not in session:
            return
        
        sql = SQLHelper.SQLHelper()
        user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{session['username']}'")
        if user == []:
            return
        
        return {"username": user[0]["username"], "pfp": user[0]["profile_picture"], "admin": bool(user[0]["is_admin"]), "premium": bool(user[0]["has_premium"])}
