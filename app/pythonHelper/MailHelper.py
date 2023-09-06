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
        html = f'Thanks for signing up to GrütteCloud!<br>To get started, please enter the following code on the verification page:<h2 style="color: #0A84FF;"><a style="color: #0A84FF; text-decoration: none;" href="https://www.gruettecloud.com/verify/{username}/{verification_code}">{verification_code}</a></h2>'
        self.send_email(recipient_email, username, "Verify your GrütteID", html, token=verification_code, link=True)

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
    We are excited to announce GrütteCloud's newest feature:
    <a style="color: #007AFF; text-decoration: none;" href="https://www.gruettecloud.com/drive">
        <h1 style="color: #007AFF;">GrütteDrive</h1>
    </a>
    Your Cloud-Storage Service by GrütteCloud.<br>Upload and download your files from anywhere.
    <div>
        <img src="https://www.gruettecloud.com/static/renders/light/drive1.png" alt="GrütteDrive Render 1" style="max-width: 350px; margin-top: 40px; margin-bottom: 40px;">
    </div>
    You can even share files via links with non GrütteCloud users.<br>
    And yes, there's a YouTube Downloader, so you can finally download your favourite videos.
    <div>
        <img src="https://www.gruettecloud.com/static/renders/light/drive2.png" alt="GrütteDrive Render 2" style="max-width: 250px; margin-top: 40px; margin-bottom: 40px;">
    </div>
    <a style="color: #007AFF; text-decoration: none;" href="https://www.gruettecloud.com/drive">
        <button style="background-color: #AF52DE; border: none; border-radius: 10px; padding: 20px; color: #F2F2F2; font-size: 1em; margin-bottom: 40px;"><b>Check Out GrütteDrive<b></button>
    </a>
    """
    
    mail.send_email("email@gmail.com", "jan", "Introducing: GrütteDrive - A Cloud-Storage Service by GrütteCloud",  text)
