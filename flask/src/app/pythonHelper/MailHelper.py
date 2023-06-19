import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from credentials import gmail_mail, gmail_app_password

class MailHelper:

    def __init__(self):
        """ Initialize the MailHelper class.
        """        
        self.sender_email = gmail_mail
        self.app_password = gmail_app_password

    def send_email(self, recipient_email, subject, message):
        """ Send an email message using Gmail.

        Args:
            recipient_email (str): The email address of the recipient.
            subject (str): The subject of the email.
            message (str): The message of the email.

        Returns:
            bool: Returns True if the email was sent successfully, False otherwise.
        """        
        # Set up the SMTP server
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587

        # Create a secure connection to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        try:
            # Log in to your Gmail account using the app password
            server.login(self.sender_email, self.app_password)

            # Create a multi-part email message
            email_message = MIMEMultipart()
            email_message['From'] = self.sender_email
            email_message['To'] = recipient_email
            email_message['Subject'] = subject

            # Add the message body as HTML
            email_message.attach(MIMEText(message, 'html'))

            # Set the Content-Type header to specify HTML
            email_message.add_header('Content-Type', 'text/html')

            # Send the email
            server.sendmail(self.sender_email, recipient_email, email_message.as_string())
            server.quit()
            return True

        except smtplib.SMTPAuthenticationError:
            server.quit()
            print('Failed to authenticate with Gmail account.')
            return False
        except smtplib.SMTPException as e:
            server.quit()
            print(f'An error occurred while sending the email: {str(e)}')
            return False
        
    def send_verification_email(self, recipient_email, username, verification_code):
        html = f'''
            <html>
                <head>
                    <style>
                        body {{
                            background-color: #1B1B1B;
                            text-align: center;
                            color: #FFFFFF;
                        }}
                        
                        img {{
                            padding: 20px;
                            width: 100px;
                            height: 100px;
                            padding-bottom: 0px;
                        }}

                        .outer-div {{
                            background-color: #282828;
                            text-align: center;
                            color: #FFFFFF;
                            width: auto;
                            height: auto;
                            border-radius: 10px;
                        }}
                        
                        h1, h2 {{
                            color: #0A84FF;
                        }}
                        
                        a {{
                            color: #0A84FF;
                            text-decoration: none;
                        }}
                    
                    </style>
                </head>
                <body>
                    <div class="outer-div">
                        <div style="text-align: center;">
                            <img src="https://raw.githubusercontent.com/xelemir/xelemir.github.io/master/media/Gr%C3%BCtteChat.png" alt="GrütteChat Logo" style="max-width: 50%; height: auto; margin-left: auto; margin-right: auto;" /><br>
                        </div><br>
                        <h1>Hey {username},</h1>
                        <b>Thanks for signing up to GrütteChat!<br>
                        To get started, please enter the following code on the verification page:
                        <h2><a href="http://jan.gruettefien.com/gruettechat/verify/{username}">{verification_code}</a></h2>
                        Kind regards,<br>The GrütteChat Team<br><br></b>
                    </div>
                </body>
            </html>
        '''
        self.send_email(recipient_email, "Verify your GrütteChat account", html)
        
    def send_new_domain_email(self, recipient_email, username):
        html = f'''
            <html>
                <head>
                    <style>
                        body {{
                            background-color: #1B1B1B;
                            text-align: center;
                            color: #FFFFFF;
                        }}
                        
                        img {{
                            padding:20px;
                            width: 80px;
                            height: 80px;
                            padding-bottom: 0px;
                        }}

                        .outer-div {{
                            background-color: #282828;
                            text-align: center;
                            color: #FFFFFF;
                            width: auto;
                            height: auto;
                            border-radius: 10px;
                        }}
                        
                        h1, h2 {{
                            color: #0A84FF;
                        }}
                        
                        a {{
                            color: #0A84FF;
                            text-decoration: none;
                        }}
                    
                    </style>
                </head>
                <body>
                    <div class="outer-div">
                        <div style="text-align: center;">
                            <img src="https://raw.githubusercontent.com/xelemir/xelemir.github.io/master/media/Gr%C3%BCtteChat.png" alt="GrütteChat Logo" style="max-width: 50%; height: auto; margin-left: auto; margin-right: auto;" /><br>
                        </div><br>
                        <h1>Hey {username},</h1>
                        <b>We have a new URL. Check it out!<br>
                        <h2><a href="https://jan.gruettefien.com/gruettechat">jan.gruettefien.com/gruettechat</a></h2>
                        Thanks for being an early supporter!<br><br>
                        Kind regards,<br>The GrütteChat Team<br><br></b>
                    </div>
                </body>
            </html>
        '''
        self.send_email(recipient_email, "GrütteChat has a new URL", html)

    def send_sophiaxkn_email(self, recipient_email, username):
        html = f'''
            <html>
                <head>
                    <style>
                        body {{
                            background-color: #1B1B1B;
                            text-align: center;
                            color: #FFFFFF;
                        }}
                        
                        img {{
                            padding:20px;
                            height: 80%;
                            padding-bottom: 0px;
                        }}

                        .outer-div {{
                            background-color: #282828;
                            text-align: center;
                            color: #FFFFFF;
                            width: auto;
                            height: auto;
                            border-radius: 10px;
                        }}
                        
                        h1, h2 {{
                            color: #0A84FF;
                        }}
                        
                        a {{
                            color: #0A84FF;
                            text-decoration: none;
                        }}
                    
                    </style>
                </head>
                <body>
                    <div class="outer-div">
                        <div style="text-align: center;">
                            <img src="https://lh3.googleusercontent.com/hUqSAfoaWi3kIS70C2oauHhkWAIHhSNfFlAHjGDBMzkDDSFFLR_H2UiOly7t6zbMFFFsVEw6kaTo1LmwspE=w330-h220-rw" alt="GrütteChat Logo" style="max-width: 80%; height: auto; margin-left: auto; margin-right: auto;" /><br>
                        </div><br>
                        <h1>Hey {username},</h1>
                        <b>Thanks for trusting us with your personal data!<br>
                        It's in good hands :)<br><br>
                        Kind regards,<br>The GrütteChat Team<br><br></b>
                    </div>
                </body>
            </html>
        '''
        self.send_email(recipient_email, "The GrütteChat Team", html)
        
        
    def send_tip_email(self, recipient_email, username_received, username_send, paid_amount):
        html = f'''
            <html>
                <head>
                    <style>
                        body {{
                            background-color: #1B1B1B;
                            text-align: center;
                            color: #FFFFFF;
                        }}
                        
                        img {{
                            padding:20px;
                            width: 80px;
                            height: 80px;
                            padding-bottom: 0px;
                        }}

                        .outer-div {{
                            background-color: #282828;
                            text-align: center;
                            color: #FFFFFF;
                            width: auto;
                            height: auto;
                            border-radius: 10px;
                        }}
                        
                        h1, h2 {{
                            color: #0A84FF;
                        }}
                        
                        a {{
                            color: #0A84FF;
                            text-decoration: none;
                        }}
                    
                    </style>
                </head>
                <body>
                    <div class="outer-div">
                        <div style="text-align: center;">
                            <img src="https://raw.githubusercontent.com/xelemir/xelemir.github.io/master/media/Gr%C3%BCtteChat.png" alt="GrütteChat Logo" style="max-width: 50%; height: auto; margin-left: auto; margin-right: auto;" /><br>
                        </div><br>
                        <h1>Hey {username_received},</h1>
                        <b>{username_send} has sent you a tip of<br>
                        <h2>{paid_amount}€</h2>
                        Kind regards,<br>The GrütteChat Team<br><br></b>
                    </div>
                </body>
            </html>
        '''
        self.send_email(recipient_email, "Tip received", html)

    def send_support_mail(self, name, username, email, message):
        html = f'''
            <html>
                <head>
                    <style>
                        body {{
                            background-color: #1B1B1B;
                            text-align: center;
                            color: #FFFFFF;
                        }}
                        
                        img {{
                            padding: 20px;
                            width: 100px;
                            height: 100px;
                            padding-bottom: 0px;
                        }}

                        .outer-div {{
                            background-color: #282828;
                            text-align: center;
                            color: #FFFFFF;
                            width: auto;
                            height: auto;
                            border-radius: 10px;
                        }}
                        
                        h1, h2 {{
                            color: #0A84FF;
                        }}
                        
                        a {{
                            color: #0A84FF;
                            text-decoration: none;
                        }}
                    
                    </style>
                </head>
                <body>
                    <div class="outer-div">
                        <div style="text-align: center;">
                            <img src="https://raw.githubusercontent.com/xelemir/xelemir.github.io/master/media/Gr%C3%BCtteChat.png" alt="GrütteChat Logo" style="max-width: 50%; height: auto; margin-left: auto; margin-right: auto;" /><br>
                        </div><br>
                        <h1>Support request by {name},</h1>
                        <b>Username: {username}<br>
                        Email: {email}<br>
                        Message: {message}<br><br>
                    </div>
                </body>
            </html>
        '''
        self.send_email(gmail_mail, "New support ticket", html)

if __name__ == "__main__":
    mail = MailHelper()
    #mail.send_verification_email("email@example.com", "user1", "123456")