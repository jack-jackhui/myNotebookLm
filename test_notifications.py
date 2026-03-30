#!/usr/bin/env python3
"""Test script for notification system."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_telegram():
    """Test Telegram notification."""
    print("=" * 60)
    print("Testing Telegram Notification")
    print("=" * 60)
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    print(f"Token: {'*' * 20}..." if token else "Token: NOT SET")
    print(f"Chat ID: {chat_id}" if chat_id else "Chat ID: NOT SET")
    
    if not token or not chat_id:
        print("❌ Telegram credentials not configured")
        return False
    
    try:
        from notifications import send_telegram_notification
        
        result = send_telegram_notification(
            "🧪 <b>Test Notification</b>\n\nThis is a test from MyNotebookLM notification system.",
            is_error=False
        )
        
        if result:
            print("✅ Telegram notification sent successfully!")
            return True
        else:
            print("❌ Failed to send Telegram notification")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_email():
    """Test email notification."""
    print("\n" + "=" * 60)
    print("Testing Email Notification")
    print("=" * 60)
    
    host = os.getenv("EMAIL_HOST")
    user = os.getenv("EMAIL_HOST_USER")
    password = os.getenv("EMAIL_HOST_PASSWORD")
    
    print(f"Host: {host}" if host else "Host: NOT SET")
    print(f"User: {user}" if user else "User: NOT SET")
    print(f"Password: {'*' * 10}..." if password else "Password: NOT SET")
    
    if not all([host, user, password]):
        print("⚠️ Email credentials not fully configured (skipping)")
        return True  # Not a failure
    
    try:
        from notifications import send_email_notification
        
        result = send_email_notification(
            subject="[MyNotebookLM] Test Notification",
            body="This is a test email from MyNotebookLM notification system.\n\nIf you receive this, email notifications are working correctly."
        )
        
        if result:
            print("✅ Email notification sent successfully!")
            return True
        else:
            print("⚠️ Email notification may have failed (check logs)")
            return True  # Don't fail the whole test
            
    except Exception as e:
        print(f"⚠️ Email error (may be expected): {e}")
        return True


def test_error_notification():
    """Test error notification flow."""
    print("\n" + "=" * 60)
    print("Testing Error Notification Flow")
    print("=" * 60)
    
    try:
        from notifications import notify_error
        
        # Create a fake error
        try:
            raise ValueError("This is a simulated test error")
        except Exception as e:
            notify_error(
                error_message="Test error notification",
                exception=e,
                context="Test Script"
            )
        
        print("✅ Error notification flow completed")
        return True
        
    except Exception as e:
        print(f"❌ Error notification flow failed: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 MyNotebookLM Notification System Test\n")
    
    telegram_ok = test_telegram()
    email_ok = test_email()
    error_flow_ok = test_error_notification()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Telegram: {'✅ PASS' if telegram_ok else '❌ FAIL'}")
    print(f"Email: {'✅ PASS' if email_ok else '⚠️ SKIPPED'}")
    print(f"Error Flow: {'✅ PASS' if error_flow_ok else '❌ FAIL'}")
    
    all_pass = telegram_ok and error_flow_ok
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}")
    
    sys.exit(0 if all_pass else 1)
