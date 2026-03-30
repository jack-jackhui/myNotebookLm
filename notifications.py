"""Notification module for podcast generation error reporting."""

import os
import logging
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
import requests

logger = logging.getLogger(__name__)

# Load from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", EMAIL_HOST_USER)


def send_telegram_notification(message: str, is_error: bool = False) -> bool:
    """
    Send a notification via Telegram.
    
    Args:
        message: The message to send
        is_error: If True, prefix with error emoji
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured, skipping notification")
        return False
    
    try:
        prefix = "🚨 ERROR" if is_error else "✅"
        formatted_message = f"{prefix}\n\n{message}"
        
        # Truncate if too long for Telegram (4096 char limit)
        if len(formatted_message) > 4000:
            formatted_message = formatted_message[:3997] + "..."
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": formatted_message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        logger.info("Telegram notification sent successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False


def send_email_notification(subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send a notification via email.
    
    Args:
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not all([EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD]):
        logger.warning("Email credentials not configured, skipping notification")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_HOST_USER
        msg["To"] = NOTIFICATION_EMAIL
        
        # Add plain text
        msg.attach(MIMEText(body, "plain"))
        
        # Add HTML if provided
        if html_body:
            msg.attach(MIMEText(html_body, "html"))
        
        # Connect and send
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(EMAIL_HOST_USER, NOTIFICATION_EMAIL, msg.as_string())
        
        logger.info(f"Email notification sent to {NOTIFICATION_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False


def notify_error(
    error_message: str,
    exception: Optional[Exception] = None,
    context: str = "Podcast Generation"
) -> None:
    """
    Send error notifications via all configured channels.
    
    Args:
        error_message: Description of the error
        exception: Optional exception object for stack trace
        context: Context where error occurred
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Build stack trace if exception provided
    stack_trace = ""
    if exception:
        stack_trace = traceback.format_exc()
    
    # Telegram message (concise)
    telegram_msg = f"""<b>MyNotebookLM {context} Failed</b>

<b>Time:</b> {timestamp}
<b>Error:</b> {error_message}

{f"<pre>{stack_trace[:1000]}</pre>" if stack_trace else ""}

Check email for full details."""

    # Email message (detailed)
    email_subject = f"[MyNotebookLM] {context} Failed - {timestamp}"
    email_body = f"""MyNotebookLM Podcast Generation Error Report
{'='*50}

Timestamp: {timestamp}
Context: {context}
Error: {error_message}

{'='*50}
Stack Trace:
{'='*50}
{stack_trace if stack_trace else 'No stack trace available'}

{'='*50}
This is an automated notification from MyNotebookLM.
"""

    # Send both notifications
    send_telegram_notification(telegram_msg, is_error=True)
    send_email_notification(email_subject, email_body)


def notify_success(message: str, context: str = "Podcast Generation") -> None:
    """
    Send success notification via Telegram only (avoid email spam).
    
    Args:
        message: Success message
        context: Context of the success
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    telegram_msg = f"""<b>MyNotebookLM {context} Complete</b>

<b>Time:</b> {timestamp}
<b>Status:</b> Success ✅

{message}"""

    send_telegram_notification(telegram_msg, is_error=False)


if __name__ == "__main__":
    # Test notifications
    print("Testing Telegram notification...")
    send_telegram_notification("Test notification from MyNotebookLM", is_error=False)
    
    print("Testing error notification...")
    try:
        raise ValueError("Test error for notification system")
    except Exception as e:
        notify_error("This is a test error", exception=e, context="Test")
    
    print("Done!")
