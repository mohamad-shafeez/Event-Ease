"""
EventEase — Email Sender Utility
Handles sending transactional emails via SMTP.
Gracefully degrades if MAIL_ENABLED is False or misconfigured.
"""
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

from config import Config

def send_email(to_email, subject, html_content, attachment_path=None):
    """Base function to send email via SMTP."""
    if not Config.MAIL_ENABLED:
        try:
            print(f"[MAIL] Mock send to {to_email}: {subject}")
        except UnicodeEncodeError:
            clean_subject = subject.encode('ascii', 'ignore').decode('ascii')
            print(f"[MAIL] Mock send to {to_email}: {clean_subject}")
        return False
        
    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = Config.MAIL_FROM
        msg['To'] = to_email

        # Attach HTML body
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        msg_alternative.attach(MIMEText(html_content, 'html'))

        # Attach inline image if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(attachment_path))
            image.add_header('Content-ID', '<qr_ticket>')
            msg.attach(image)

        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
        server.starttls()
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        try:
            print(f"[MAIL ERROR] Failed to send email to {to_email}: {e}")
        except UnicodeEncodeError:
            print(f"[MAIL ERROR] Failed to send email to {to_email} (Error string contained emojis)")
        traceback.print_exc()
        return False

def send_ticket_confirmation(to_email, user_name, event_title, event_date, venue, ticket_code, qr_path):
    """Sends a ticket confirmation with QR code."""
    subject = "Your EventEase Ticket Confirmed! 🎟️"
    
    # Very simple HTML styling mimicking the ticket
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background: #f4f4f5; padding: 20px; color: #1e1f2e;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
          <div style="background: #6C63FF; color: #fff; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Ticket Confirmed!</h1>
          </div>
          <div style="padding: 30px;">
            <p>Hi {user_name},</p>
            <p>You're all set for <strong>{event_title}</strong>.</p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
              <tr><td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Date:</strong> {event_date}</td></tr>
              <tr><td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Venue:</strong> {venue}</td></tr>
              <tr><td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Ticket Code:</strong> {ticket_code}</td></tr>
            </table>
            <div style="text-align: center; margin-top: 30px;">
              <p style="color: #6B7280; font-size: 14px;">Present this QR code at the entrance:</p>
              <img src="cid:qr_ticket" alt="QR Code" style="width: 200px; height: 200px; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px;">
            </div>
          </div>
          <div style="background: #f9fafb; padding: 15px; text-align: center; color: #6B7280; font-size: 12px;">
            &copy; 2026 EventEase
          </div>
        </div>
      </body>
    </html>
    """
    return send_email(to_email, subject, html, qr_path)

def send_event_created(to_email, creator_name, event_title, event_date):
    """Sends event creation confirmation to creator."""
    subject = "Your Event is Live on EventEase! 🎉"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1e1f2e;">
        <h2>Hi {creator_name},</h2>
        <p>Congratulations! Your event <strong>{event_title}</strong> is now officially created and published.</p>
        <p>It is scheduled for: <strong>{event_date}</strong>.</p>
        <p>You can manage your event, view attendees, and check analytics from your Creator Dashboard.</p>
        <br>
        <p>Cheers,<br>The EventEase Team</p>
      </body>
    </html>
    """
    return send_email(to_email, subject, html)

def send_registration_reminder(to_email, user_name, event_title, event_date, venue, ticket_code):
    """Sends a reminder email. Currently unused but defined for future background task."""
    subject = f"Reminder: {event_title} is Tomorrow! ⏰"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1e1f2e;">
        <h2>Hi {user_name},</h2>
        <p>Just a quick reminder that <strong>{event_title}</strong> is happening tomorrow at {event_date}.</p>
        <p>Venue: {venue}</p>
        <p>Ticket Code: {ticket_code}</p>
        <p>Don't forget your ticket!</p>
      </body>
    </html>
    """
    return send_email(to_email, subject, html)

def send_password_reset_email(to_email, user_name, reset_url):
    """Sends a password reset link to the user."""
    subject = "Reset Your EventEase Password 🔒"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background: #f4f4f5; padding: 20px; color: #1e1f2e;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
          <div style="background: #6C63FF; color: #fff; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Password Reset</h1>
          </div>
          <div style="padding: 30px; text-align: center;">
            <p>Hi {{user_name}},</p>
            <p>We received a request to reset your password. Click the button below to choose a new one:</p>
            <div style="margin: 30px 0;">
                <a href="{{reset_url}}" style="background: #6C63FF; color: #fff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; display: inline-block;">Reset Password</a>
            </div>
            <p style="color: #6B7280; font-size: 14px;">This link will expire in 1 hour. If you didn't request this, you can safely ignore this email.</p>
          </div>
          <div style="background: #f9fafb; padding: 15px; text-align: center; color: #6B7280; font-size: 12px;">
            &copy; 2026 EventEase
          </div>
        </div>
      </body>
    </html>
    """
    return send_email(to_email, subject, html)
