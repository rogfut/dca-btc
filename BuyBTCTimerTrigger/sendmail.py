import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(from_email, to_emails, subject, html_content):
    try:
        # sg = SendGridAPIClient('key')
        sg = SendGridAPIClient(os.environ['SENDGRID_KEY'])
        response = sg.send(Mail(
            from_email,
            to_emails,
            subject,
            html_content
        ))
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)