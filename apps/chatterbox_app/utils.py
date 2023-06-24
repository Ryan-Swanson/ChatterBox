# chatterbox_app/utils.py
from email import message_from_bytes
from email.utils import parsedate_to_datetime
import smtplib
import imaplib
import pytz


def get_body(msg):
    text_body = None
    html_body = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and text_body is None:
                text_body = part.get_payload(decode=True).decode(
                    'utf-8', errors='replace')
            elif content_type == "text/html" and html_body is None:
                html_body = part.get_payload(decode=True).decode(
                    'utf-8', errors='replace')

            if text_body and html_body:
                break
    else:
        text_body = msg.get_payload(decode=True).decode(
            'utf-8', errors='replace')

    return html_body if html_body else text_body


def parse_email_date(email):
    date_str = email['Date']
    dt = parsedate_to_datetime(date_str)
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt


def fetch_emails(user, start_index, end_index):
    smtp_email = user.profile.smtp_email
    smtp_password = user.profile.smtp_password
    imap_server = connect_imap_server(smtp_email, smtp_password)
    imap_server.select('INBOX')

    _, uids = imap_server.search(None, 'ALL')
    email_ids = uids[0].split()
    email_ids_to_load = email_ids[start_index:end_index]
    emails = []

    for email_id in email_ids_to_load:
        _, data = imap_server.fetch(email_id.decode(), '(RFC822)')
        raw_email = data[0][1]
        email = message_from_bytes(raw_email)
        emails.append((email_id.decode(), email))

    imap_server.close()
    imap_server.logout()

    return emails


def connect_imap_server(smtp_email, smtp_password):
    imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_server.login(smtp_email, smtp_password)
    return imap_server


def connect_smtp_server(smtp_email, smtp_password):
    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_server.starttls()
    smtp_server.login(smtp_email, smtp_password)
    return smtp_server
