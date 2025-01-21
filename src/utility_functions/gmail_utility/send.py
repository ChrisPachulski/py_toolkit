import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError
import janitor
from dotenv import load_dotenv

from .common import _get_env_path
from . import auth
from .file_handling import create_attachments


def gmail_send_message(data, receivers, file_titles, subject, content):
    """
    Send an email via Gmail API with optional attachments (files or DataFrames).

    Parameters:
        data (list|str|pd.DataFrame): Single or list of items to attach:
                                      either file paths (str) or DataFrames.
        receivers (str): Comma-separated string of email addresses.
        file_titles (list|str): Attachment names (including file extensions).
        subject (str): The email subject.
        content (str): The email body.

    Returns:
        dict or None: The API response dict if successful, or None if error.

    Example usage:
        >>> from gmail_utility.send import gmail_send_message
        >>> gmail_send_message(
        ...     data="/path/to/file.csv",
        ...     receivers="someone@example.com",
        ...     file_titles="report.csv",
        ...     subject="Daily Report",
        ...     content="Here is your daily report."
        ... )
    """
    load_dotenv(dotenv_path=_get_env_path())
    
    SENDER_EMAIL=os.getenv("GOOGLE_EMAIL_SENDER")
    
    try:
        service = auth.build_gmail_service()
        
        message = MIMEMultipart()
        message["To"] = receivers
        message["From"] = SENDER_EMAIL
        message["Subject"] = subject

        # Attach main body as plain text
        body = MIMEText(content, "plain")
        message.attach(body)

        # Create and attach any files/data
        try:
            attachments = create_attachments(data, file_titles)
            for part in attachments:
                message.attach(part)
        except ValueError as ve:
            print(f"Attachment creation error: {ve}")
            return None

        # Encode the entire message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}

        # Send the email
        send_message = service.users().messages().send(
            userId="me", body=create_message
        ).execute()

        print(f"Message Id: {send_message['id']}")
        return send_message

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


