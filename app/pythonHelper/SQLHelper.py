import MySQLdb
import logging
import socket

from config import gcpConfig, jamailliaConfig, macBookProConfig, londonConfig

class SQLHelper: 
    
    connection = None
    
    def __init__(self):
        try:
            host_local = socket.gethostname()
            if host_local in ["gruttechat-webserver", "dauntless-1"]:
                connection = MySQLdb.Connection(**gcpConfig)
            elif "mac" in host_local.lower() or "mbp" in host_local.lower() or "uni-stuttgart" in host_local.lower():
                connection = MySQLdb.Connection(**macBookProConfig)
            elif "london" in host_local.lower():
                connection = MySQLdb.Connection(**londonConfig)
            else:
                connection = MySQLdb.Connection(**jamailliaConfig)
            self.connection = connection    
            
            
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
            self.connection.query(query)
            self.connection.commit()
            if return_is_successful: return True
        except Exception as e:
            logging.error(f"The error '{e}' occurred")
            if return_is_successful: return False


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
            self.connection.query(query)
            result = self.connection.store_result()
            rows = result.fetch_row(maxrows=0, how=1)
            if return_is_successful: return [row for row in rows], True
            else: return [row for row in rows]
            
        except Exception as e:
            logging.error(f"The error '{e}' occurred")
            if return_is_successful: return [], False
            else: return []

    
if __name__ == "__main__":
    sql = SQLHelper()
    print(sql.readSQL("SELECT * FROM users"))
    #sql.writeSQL("INSERT INTO chat (userSend, userReceive, message) VALUES ('user1', 'user2', 'Test')")
    #sql.writeSQL(f"INSERT INTO gruttechat_users (username, password, email, is_email_verified, has_premium, ai_personality) VALUES ('user2', 'password', 'email', {True}, {False}, 'ai_personality')")
    #sql.writeSQL(f"INSERT INTO gruttechat_messages (username_send, username_receive, message_content) VALUES ('user1', 'user2', 'Test')")
    #response = sql.readSQL("SELECT * FROM gruttechat_users WHERE username = 'user1'")
    #print(response[0]["username"])
