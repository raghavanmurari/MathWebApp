import smtplib
import random
import string
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database.user_dao import find_user, update_user
from utils.security import hash_password
from utils.security import hash_password, validate_password

# # SMTP Configuration
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# SMTP_EMAIL = "mathwebapp7@gmail.com"
# SMTP_PASSWORD = "aoof ryvs oymz mpai"  # Updated App Password

import os

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "mathwebapp7@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "aoof ryvs oymz mpai")

# print("DEBUG: Using email settings:")
# print(f"SMTP_SERVER: {SMTP_SERVER}")
# print(f"SMTP_PORT: {SMTP_PORT}")
# print(f"SMTP_EMAIL: {SMTP_EMAIL}")
# print("SMTP_PASSWORD: [REDACTED]")

# Temporary storage for reset codes (valid for 10 mins)
reset_codes = {}

def generate_reset_code():
    """Generate a 6-digit numeric reset code."""
    return ''.join(random.choices(string.digits, k=6))

def send_email(to_email, reset_code):
    """Send password reset email securely using SMTP."""
    # print(f"DEBUG: Attempting to send email to {to_email}")
    
    subject = "Your Password Reset Code - Math Web App"
    body = f"""
    Hello,

    You have requested to reset your password. 
    Your reset code is: {reset_code}

    This code will expire in 10 minutes. 
    If you did not request this, please ignore this email.

    Regards,
    Math Web App Team
    """

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # print("DEBUG: Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        # print("DEBUG: Starting TLS...")
        server.starttls()
        # print("DEBUG: Attempting login...")
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        # print("DEBUG: Sending email...")
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        # print("DEBUG: Closing server connection...")
        server.quit()

        # print("DEBUG: Email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError as e:
        # print(f"ERROR: SMTP Authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        # print(f"ERROR: SMTP error occurred: {e}")
        return False
    except Exception as e:
        # print(f"ERROR: An unexpected error occurred: {e}")
        return False

def save_reset_code(email):
    """Save reset code and send it via email."""
    # print(f"DEBUG: Starting reset code process for {email}")
    user = find_user(email)
    # print(f"DEBUG: Found user: {user is not None}")

    if not user:
        # print("DEBUG: User not found in save_reset_code")
        return None  # Email not found in DB

    reset_code = generate_reset_code()
    # print(f"DEBUG: Generated reset code: {reset_code}")

    reset_codes[email] = {"code": reset_code, "timestamp": time.time()}
    # print(f"DEBUG: Saved reset code in memory")

    # Send the reset code via email
    email_sent = send_email(email, reset_code)
    # print(f"DEBUG: Email sending result: {email_sent}")

    return reset_code if email_sent else None

def verify_reset_code(email, code):
    """Verify if the reset code is correct and not expired."""
    if email not in reset_codes:
        # print(f"DEBUG: No reset code found for {email}")
        return False  # No reset code found

    saved_code_data = reset_codes[email]

    # Check if the code matches
    if saved_code_data["code"] != code:
        # print(f"DEBUG: Invalid reset code for {email}")
        return False  # Invalid code

    # Check if the code is expired (valid for 10 minutes)
    current_time = time.time()
    if (current_time - saved_code_data["timestamp"]) > 600:
        del reset_codes[email]  # Remove expired code
        # print(f"DEBUG: Reset code expired for {email}")
        return False  # Code expired

    # print(f"DEBUG: Valid reset code for {email}")
    return True  # Code is valid

def update_password(email, new_password):
    """Update the user's password in the database after verification."""
    try:
        user = find_user(email)
        if not user:
            # print(f"DEBUG: User not found for password update: {email}")
            return False, "User not found. Cannot reset password."

        # NEW: Validate the new password against the restrictions
        if not validate_password(new_password):
            return False, ("New password does not meet the security requirements. "
                           "It must be at least 8 characters long and include one uppercase letter, "
                           "one lowercase letter, one digit, and one special character.")

        # print("DEBUG: Attempting to hash password")
        hashed_password = hash_password(new_password)
        # print(f"DEBUG: Password successfully hashed: {hashed_password[:20]}...")

        update_data = {
            "password": hashed_password,
            "updated_at": datetime.utcnow()
        }
        
        success = update_user(email, update_data)
        
        if success:
            if email in reset_codes:
                del reset_codes[email]  # Remove reset code after successful update
            # print(f"DEBUG: Password successfully updated for {email}")
            return True, "Password has been successfully reset."
        else:
            # print(f"DEBUG: Password reset failed for {email}")
            return False, "Failed to reset password. Please try again."

    except Exception as e:
        # print(f"ERROR: Failed to update password for {email}: {str(e)}")
        return False, "An error occurred. Please try again."
