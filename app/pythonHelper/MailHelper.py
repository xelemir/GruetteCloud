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
        
    
        
    def send_email(self, recipient_email, username, subject, body, image_url="https://www.gruettecloud.com/static/gruettecloud_logo.png", link=False):
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
                <body style="color: #FFFFFF;">
                    <div style="background-color: #282828; text-align: center; color: #FFFFFF; width: auto; height: auto; border-radius: 20px; padding: 20px;">
                        <img src="{image_url}" alt="GrütteCloud Logo" style="max-width: 200px; margin-top: -20px;">
                        <h1 style="color: #0A84FF; margin-top: -20px;">Hey {username},</h1>
                        <b style="color: #FFFFFF;">
                            {body}
                            {additional_br}
                        </b>
                        <b style="color: #FFFFFF;">Kind regards,<br>Jan from GrütteCloud</b>
                        <br><br><br>
                        <span style="font-size: 0.7em;">
                            If you think this email was sent by mistake, <a href="https://www.gruettecloud.com/v/support" style="color: #FFFFFF;">contact us</a>.<br>
                            <span style="display: inline-flex;">
                                <a href="https://www.gruettecloud.com/v/about" style="color: #FFFFFF;">About Us</a>
                                &nbsp;|&nbsp;
                                <a href="https://www.gruettecloud.com/v/terms" style="color: #FFFFFF;">Terms of Service</a>
                                &nbsp;|&nbsp;
                                <a href="https://www.gruettecloud.com/v/privacy" style="color: #FFFFFF;">Privacy Policy</a>
                            </span>
                        </span>
                    </div>
                </body>
            </html>
        '''
        self.send_email_no_template(recipient_email, subject, html)
        
    def send_verification_email(self, recipient_email, username, verification_code):
        html = f'Thanks for signing up to GrütteCloud!<br>To get started, please enter the following code on the verification page:<h2 style="color: #0A84FF;"><a style="color: #0A84FF; text-decoration: none;" href="http://jan.gruettefien.com/gruettechat/verify/{username}/{verification_code}">{verification_code}</a></h2>'
        self.send_email(recipient_email, username, "Verify your GrütteID", html, link=True)

    def send_support_mail(self, name, username, email, message):
        html = f'''
            <html>
                <body style="color: #FFFFFF;">
                    <div style="background-color: #282828; text-align: center; color: #FFFFFF; width: auto; height: auto; border-radius: 20px; padding: 20px;">
                        <h1 style="color: #0A84FF; margin-top: -20px;">New Support Request</h1>
                        <b>
                            Name: {name}<br>
                            Username: {username}<br>
                            Email: {email}<br>
                            Message: {message}<br><br>
                        </b>
                    </div>
                </body>
            </html>
        '''
        self.send_email_no_template(gmail_mail, "New support ticket", html)

if __name__ == "__main__":
    sophia_img = "https://lh3.googleusercontent.com/hUqSAfoaWi3kIS70C2oauHhkWAIHhSNfFlAHjGDBMzkDDSFFLR_H2UiOly7t6zbMFFFsVEw6kaTo1LmwspE=w330-h220-rw"
    mail = MailHelper()
    mail.send_verification_email("test@gmail.com", "tester2", "468415")
    #mail.send_email("test@gmail.com", "jan", "Test", "HEHEHEHHE DOPPEL D")
    