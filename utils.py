# utils.py
from email.message import EmailMessage
import smtplib


def send_email(to_address, subject, content):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "gulcancomert9@gmail.com"
    msg['To'] = "aygulgulay81@gmail.com"

    msg.set_content(content)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        # senin çalıştırabildiğin özel şifre
        smtp.login("gulcancomert9@gmail.com", "gfuc rieo fgvg ptgd")
        smtp.send_message(msg)
