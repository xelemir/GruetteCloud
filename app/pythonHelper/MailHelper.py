import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import gmail_mail, gmail_app_password

class MailHelper:

    def __init__(self):
        """ Initialize the MailHelper class.
        """        
        self.sender_email = gmail_mail
        self.app_password = gmail_app_password

    def send_email_no_template(self, recipient_email, subject, message):
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
        
    
        
    def send_email(self, recipient_email, username, subject, body, token="None", image_url="https://www.gruettecloud.com/static/gruettecloud_logo.png", link=False):
        
        additional_br = ""
        if not link:
            additional_br = "<br><br>"
        html = f'''
            <html>
                <head>
                    <link rel="preconnect" href="https://fonts.googleapis.com">
                    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap" rel="stylesheet">
                    <style>
                        body {{
                            font-family: 'Nunito', sans-serif;
                            font-size: 1em;
                        }}
                    </style>
                </head>
                <body style="color: #F2F2F2;">
                    <div style="background-color: #F2F2F2; text-align: center; color: #000000; width: auto; height: auto; border-radius: 20px; padding: 20px;">
                        <img src="https://www.gruettecloud.com/static/gruettecloud_logo.png" alt="GrütteCloud Logo" style="max-width: 150px; margin-top: -20px;">
                        <h1 style="color: #007AFF; margin-top: -20px;">Hey {username},</h1>
                        <b style="color: #000000;">
                            {body}
                            {additional_br}
                        </b>
                        <b style="color: #000000;">Kind regards,<br>Jan from GrütteCloud</b>
                        <br><br><br>
                        <span style="font-size: 0.7em;">
                            You are receiving this email because you are subscribed to GrütteCloud communication emails.<br>
                            If you do not want to receive any more emails, you can <a href="https://www.gruettecloud.com/unsubscribe?username={username}&email={recipient_email}&token={token}" style="color: #000000;">unsubscribe here</a>.<br>
                            <span style="display: inline-flex;">
                                <a href="https://www.gruettecloud.com/about" style="color: #000000;">About Us</a>
                                &nbsp;|&nbsp;
                                <a href="https://www.gruettecloud.com/terms" style="color: #000000;">Terms of Service</a>
                                &nbsp;|&nbsp;
                                <a href="https://www.gruettecloud.com/privacy" style="color: #000000;">Privacy Policy</a>
                            </span>
                        </span>
                    </div>
                </body>
            </html>
        '''
        self.send_email_no_template(recipient_email, subject, html)
        
    def send_verification_email(self, recipient_email, username, verification_code):
        html = f'Thanks for signing up to GrütteCloud!<br>To get started, please enter the following code on the verification page:<h2 style="color: #0A84FF;"><a style="color: #0A84FF; text-decoration: none;" href="https://www.gruettecloud.com/verify/{username}">{verification_code}</a></h2>'
        self.send_email(recipient_email, username, "Verify your GrütteCloud Account", html, token=verification_code, link=True)

    def send_support_mail(self, name="None", username="None", email="None", message="None"):
        html = f'''
            <html>
                <head>
                    <link rel="preconnect" href="https://fonts.googleapis.com">
                    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap" rel="stylesheet">
                    <style>
                        body {{
                            font-family: 'Nunito', sans-serif;
                            font-size: 1em;
                        }}
                    </style>
                </head>
                <body style="color: #FFFFFF;">
                    <div style="background-color: #282828; text-align: center; color: #FFFFFF; width: auto; height: auto; border-radius: 20px; padding: 20px;">
                        <img src="https://www.gruettecloud.com/static/gruettecloud_logo.png" alt="GrütteCloud Logo" style="max-width: 150px; margin-top: -20px;">
                        <h1 style="color: #0A84FF; margin-top: -20px;">Request by {name},</h1>
                        <b style="color: #FFFFFF;">
                            Name: {name}<br>
                            Username: {username}<br>
                            Email: {email}<br>
                            Message: {message}
                        </b><br><br>
                        <b style="color: #FFFFFF;">GrütteCloud</b>
                        <br><br><br>
                        <span style="font-size: 0.7em;">
                            <span style="display: inline-flex;">
                                <a href="https://www.gruettecloud.com/about" style="color: #FFFFFF;">About Us</a>
                                &nbsp;|&nbsp;
                                <a href="https://www.gruettecloud.com/terms" style="color: #FFFFFF;">Terms of Service</a>
                                &nbsp;|&nbsp;
                                <a href="https://www.gruettecloud.com/privacy" style="color: #FFFFFF;">Privacy Policy</a>
                            </span>
                        </span>
                    </div>
                </body>
            </html>
        '''
        self.send_email_no_template(gmail_mail, f"Request by {name}", html)

if __name__ == "__main__":
    mail = MailHelper()
    #mail.send_verification_email("test@gmail.com", "tester2", "468415")
    
    
    text = """
    <html>
    <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    </head>
    <body style=" font-family: 'Nunito', sans-serif; font-size: 1em; background-color: #FFFFFF; display: flex; justify-content: center;">  
        <div style="background-color: #F2F2F2; text-align: center; color: #000000; width: 100%; height: auto; border-radius: 25px; padding: 30px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); max-width: 400px;">
            <img src="https://www.gruettecloud.com/static/gruettecloud_logo.png" alt="GrütteCloud Logo" style="max-width: 64px; margin-top: 0px;">
            <p style="color: #000000; font-size: 1.2em; margin-top: 10px; text-align: left;">
                Hi Jan,
            </p>
            <p style="color: #000000; font-size: 1em; margin-top: 10px; text-align: left;">
                the following job has been completed:
            </p>
            <div style="display: flex; flex-direction: row; justify-content: left; align-items: left; margin-top: 30px;">
                <span style="margin-right: 15px; font-size: 1.5em; display: flex; justify-content: center; align-items: center;">&#128204;</span>
                <p style="text-align: left;">Deletion of old MyAI files</p>
            </div>
            <div style="display: flex; flex-direction: row; justify-content: left; align-items: left;">
                <span style="margin-right: 15px; font-size: 1.5em; display: flex; justify-content: center; align-items: center;">&#128197;</span>
                <p style="text-align: left;">26.08.2024</p>
            </div>
            <div style="display: flex; flex-direction: row; justify-content: left; align-items: left;">
                <span style="margin-right: 15px; font-size: 1.5em; display: flex; justify-content: center; align-items: center;">&#9200;</span>
                <p style="text-align: left;">04:00 AM</p>
            </div>
            <div style="display: flex; flex-direction: row; justify-content: left; align-items: left;">
                <span style="margin-right: 15px; font-size: 1.5em; display: flex; justify-content: center; align-items: center;">&#128994;</span>
                <p style="text-align: left;">Status: OK</p>
            </div>
            <span class="material-symbols-outlined">
                home
                </span>
            
            <div style="display: flex; flex-direction: column; justify-content: left; align-items: left;">
                <div style="display: flex; flex-direction: row; justify-content: left; align-items: left;">
                    <span style="margin-right: 15px; font-size: 1.5em; display: flex; justify-content: center; align-items: center;">&#128308;</span>
                    <p style="text-align: left;">Status: Error</p>
                </div>
                <div style="display: flex; flex-direction: row; justify-content: left; align-items: left;">
                    <p style="text-align: left;">
                        a010fe1b1268f3d634053a8eed655b73_1.png
                        a010fe1b1268f3d63z453a8eed655b73_1.png
                        a010fe1b126824d63z453a8eed655b73_1.png
                    </p>
                </div>
            </div>
            <p style="color: #000000; font-size: 1.1em; margin-top: 50px; text-align: left;">
                Kind regards,<br><br>
                GrütteCloud
            </p>
            <p style="color: #000000; font-size: 0.8em; margin-top: 30px; text-align: left;">
                <a href="mailto:info@gruettecloud.com" style="color: #000000;">info@gruettecloud.com</a><br>
                <a href="https://www.gruettecloud.com" style="color: #000000;">www.gruettecloud.com</a><br><br>
                This is an automated message.<br>
                Please do not reply to this email.
            </p>
        </div>
    </body>
</html>
    """
    
    mail.send_email("gruttefien@gmail.com", "Jan", "GrütteCloud Daily Report", text)
