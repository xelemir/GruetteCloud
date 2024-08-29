import logging
import socket

import pymysql
from config import jamailliaConfig, macBookProConfig, londonConfig, prodServerConfig

class SQLHelper: 
    
    connection = None
    
    def __init__(self):
        try:
            host_local = socket.gethostname()
            if "gruettecloud" in host_local.lower():
                self.connection = pymysql.connect(**prodServerConfig)
            elif "mac" in host_local.lower() or "mbp" in host_local.lower() or "uni-stuttgart" in host_local.lower():
                self.connection = pymysql.connect(**macBookProConfig)
            elif "london" in host_local.lower():
                self.connection = pymysql.connect(**londonConfig)
            else:
                self.connection = pymysql.connect(**jamailliaConfig)
            
        except Exception as e:
            logging.error(f"The error '{e}' occurred")

    def writeSQL(self, query, return_is_successful=False):
        """ Write to SQL database

        Args:
            query (str): A valid SQL query
            return_is_successful (bool, optional): Return True if the query was successful, False otherwise. Defaults to False.
            
        Returns (optional):
            bool: True if the query was successful, False otherwise
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
            self.connection.commit()
            if return_is_successful: 
                return True
        except Exception as e:
            logging.error(f"The error '{e}' occurred")
            if return_is_successful: 
                return False


    def readSQL(self, query, return_is_successful=False):
        """ Read from SQL database

        Args:
            query (str): A valid SQL query
            return_is_successful (bool, optional): Return True if the query was successful, False otherwise. Defaults to False.

        Returns:
            list: A list of dictionaries containing the rows, empty list if no rows are found
            bool (optional): True if the query was successful, False otherwise
        """        
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                
            if return_is_successful: 
                if rows == (): return [], False
                return list(rows), True
            else:
                if rows == (): return []
                return list(rows)
                
            
        except Exception as e:
            logging.error(f"The error '{e}' occurred")
            if return_is_successful: 
                return [], False
            else: 
                return []


    
if __name__ == "__main__":
    sql = SQLHelper()
    x = sql.readSQL("SELECT * FROM platform_notifications")
    print(x == [])
    #print(sql.readSQL("SELECT * FROM users WHERE id = 1;"))
    #print(sql.writeSQL("UPDATE users SET is_verified = 1 WHERE id = 1", return_is_successful=True))
    #sql.writeSQL("INSERT INTO chat (userSend, userReceive, message) VALUES ('user1', 'user2', 'Test')")
    #sql.writeSQL(f"INSERT INTO gruttechat_users (username, password, email, is_email_verified, has_premium, ai_personality) VALUES ('user2', 'password', 'email', {True}, {False}, 'ai_personality')")
    #sql.writeSQL(f"INSERT INTO gruttechat_messages (username_send, username_receive, message_content) VALUES ('user1', 'user2', 'Test')")
    #response = sql.readSQL("SELECT * FROM gruttechat_users WHERE username = 'user1'")
    #print(response[0]["username"])
