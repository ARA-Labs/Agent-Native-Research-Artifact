#!/usr/bin/env python3
"""Send an email to amberjcjj@gmail.com via Gmail SMTP."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

SENDER = "amberjcjj@gmail.com"
RECIPIENT = "amberjcjj@gmail.com"

def send_email(subject: str, body: str):
    password = os.environ.get("EMAIL_PASSWORD")

    if not password:
        raise ValueError("EMAIL_PASSWORD not found in .env")

    msg = MIMEMultipart()
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, password)
        server.sendmail(SENDER, RECIPIENT, msg.as_string())

    print(f"Email sent to {RECIPIENT}")
    print(f"Subject: {subject}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send an email.")
    parser.add_argument("--subject", default="Hello from ARA", help="Email subject")
    parser.add_argument("--body", default="This is an automated message.", help="Email body")
    args = parser.parse_args()

    send_email(args.subject, args.body)
