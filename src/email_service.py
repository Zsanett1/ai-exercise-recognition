import smtplib
from email.message import EmailMessage
import streamlit as st

def send_verification_email(to_email, username, verification_link):
    message = EmailMessage()
    message["Subject"] = "Verify your AI Home Personal Trainer account"
    message["From"] = f"{st.secrets['BREVO_SENDER_NAME']} <{st.secrets['BREVO_SENDER_EMAIL']}>"
    message["To"] = to_email
    message.set_content(
        f"""Hello {username}, 
        Thank you for creating an AI Home Personal Assistent account.
        Please verify your email address by opening this link:
        {verification_link}
        This verification link is valid for 24 hours.
        If you did not create this account, you can ignore this email.
        AI Home Personal Assistant"""
    )
    message.add_alternative(
        f"""
        <html>
            <body>
                <h2>Verify your email address</h2>
                <p>Hello {username},</p>
                <p>Thank you for creating an AI Home Personal Trainer account.</p>
                <p>Please verify your email address by clicking the button below:</p>
                <p>
                    <a href="{verification_link}"
                       style="background-color:#14B8A6;color:white;padding:10px 16px;
                              text-decoration:none;border-radius:6px;font-weight:bold;">
                        Verify my email
                    </a>
                </p>
                <p>This verification link is valid for 24 hours.</p>
                <p>If you did not create this account, you can ignore this email.</p>
            </body>
        </html>
        """,
        subtype="html"
    )

    with smtplib.SMTP(st.secrets["BREVO_SMTP_SERVER"], int(st.secrets["BREVO_SMTP_PORT"])) as server:
        server.starttls()
        server.login(st.secrets["BREVO_SMTP_LOGIN"], st.secrets["BREVO_SMTP_PASSWORD"])
        server.send_message(message)
