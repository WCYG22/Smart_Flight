"""
Email Notification Service (F013)
Sends itinerary summaries via email
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import os
from .itinerary_manager import export_itinerary_html


def send_itinerary_email(recipient_email: str, itinerary: Dict, subject: str = None) -> Dict:
    """
    Send itinerary summary via email (F013).
    
    Returns:
        {"success": bool, "message": str}
    """
    
    try:
        # Get email credentials from environment
        sender_email = os.getenv("SMTP_EMAIL", "smartflight@example.com")
        sender_password = os.getenv("SMTP_PASSWORD", "")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        # If no credentials, return mock success (for development)
        if not sender_password:
            return {
                "success": True,
                "message": f"Email would be sent to {recipient_email} (SMTP not configured)",
                "mock": True
            }
        
        # Create email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject or "Your SmartFlight Itinerary"
        msg["From"] = sender_email
        msg["To"] = recipient_email
        
        # Generate HTML content
        html_content = export_itinerary_html(itinerary)
        
        # Attach HTML
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        return {
            "success": True,
            "message": f"Email sent successfully to {recipient_email}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}"
        }
