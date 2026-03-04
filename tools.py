import imaplib
import email
from email.policy import default
import os
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")

def connect_imap():
    """Helper function to establish an authenticated IMAP connection."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    return mail

@tool
def get_unread_email_headers(limit: int = 5) -> list[dict]:
    """Fetches the headers (ID, sender, subject, date) of unread emails."""
    try:
        mail = connect_imap()
        mail.select("inbox")
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK" or not messages[0]:
            return []
        email_ids = messages[0].split()[-limit:]
        headers = []

        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if status == "OK":
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1], policy=default)
                        headers.append({
                            "id": e_id.decode(),
                            "from": msg.get("From", ""),
                            "subject": msg.get("Subject", ""),
                            "date": msg.get("Date", "")
                        })
        mail.logout()
        return headers
    except Exception as e:
        return [{"error": str(e)}]

@tool
def get_email_content(email_id: str) -> str:
    """Fetches the plain text body of a specific email using its ID."""
    try:
        mail = connect_imap()
        mail.select("inbox")
        status, msg_data = mail.fetch(email_id.encode(), "(RFC822)")
        
        if status != "OK":
            return "Error fetching email."

        body = ""
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1], policy=default)
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            charset = part.get_content_charset() or 'utf-8'
                            body = part.get_payload(decode=True).decode(charset, errors='replace')
                            break
                else:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = msg.get_payload(decode=True).decode(charset, errors='replace')
                
        mail.logout()
        return body.strip() if body else "No plain text content found."
    except Exception as e:
        return f"Error: {str(e)}"