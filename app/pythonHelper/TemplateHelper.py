import pythonHelper.SQLHelper as SQLHelper

class TemplateHelper:
    def __init__(self):
        pass
    
    def user(self, session):
        if "user_id" not in session:
            return
        
        sql = SQLHelper.SQLHelper()
        user = sql.readSQL(f"SELECT username, profile_picture, is_admin, has_premium, advanced_darkmode FROM users WHERE id = '{session['user_id']}'")
        if user == []:
            return
        
        return {"username": user[0]["username"], "pfp": user[0]["profile_picture"], "admin": bool(user[0]["is_admin"]), "premium": bool(user[0]["has_premium"]), "advanced_darkmode": bool(user[0]["advanced_darkmode"])}
