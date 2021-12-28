import os, sys
from os import environ, path
from dotenv import load_dotenv
# from flask_mail import Mail, Message
from flask import render_template
from services.Users import mail
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


from_email = environ.get('FROM_EMAIL')
sendgrid_api_key = environ.get('SENDGRID_API_KEY')


#Send Email
def send_email(to, name, subject, confirm_url):
    message = Mail(
        from_email=from_email,
        to_emails=to,
        subject="Account Activation - OpenARC",
        html_content=render_template('Email/account_activation.html',email=to, username=name, confirm_url=confirm_url, subject=subject)
    )
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        code, body, headers = response.status_code, response.body, response.headers
        print(f"Response Code: {code} ")
        print(f"Response Body: {body} ")
        print(f"Response Headers: {headers} ")
        print("Message Sent!")
    except Exception as e:
        print("Error: {0}".format(e))
    return str(response.status_code)


#Send Password Reset Email
def send_password_reset_email(to, name, subject, reset_url):
    message = Mail(
        from_email=from_email,
        to_emails=to,
        subject="Forgot Password - OpenARC",
        html_content=render_template('Email/forgot_password.html', username=name, reset_url=reset_url, subject=subject)
    )
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        code, body, headers = response.status_code, response.body, response.headers
        print(f"Response Code: {code} ")
        print(f"Response Body: {body} ")
        print(f"Response Headers: {headers} ")
        print("Message Sent!")
    except Exception as e:
        print("Error: {0}".format(e))
    return str(response.status_code)