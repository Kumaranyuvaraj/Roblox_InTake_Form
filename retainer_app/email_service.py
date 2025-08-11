import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings
from django.template import Template, Context
from django.utils.html import strip_tags
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)


class LawFirmEmailService:
    """
    Custom email service for sending HTML emails per law firm configuration
    """
    
    def __init__(self, law_firm):
        self.law_firm = law_firm
        self.email_config = law_firm.get_email_config()
        
    def send_retainer_email(self, recipient, email_template, signing_url, external_id=None):
        """
        Send a retainer agreement email to a recipient
        
        Args:
            recipient: RetainerRecipient instance
            email_template: EmailTemplate instance
            signing_url: URL for document signing
            external_id: External ID for tracking
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Validate email configuration
            if not self.law_firm.has_email_config():
                logger.error(f"Law firm {self.law_firm.name} has incomplete email configuration")
                return False
            
            # Personalize email content
            personalized_content = self._personalize_email_content(
                email_template, recipient, signing_url, external_id
            )
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = personalized_content['subject']
            msg['From'] = self._get_from_address()
            msg['To'] = recipient.email
            
            # Create HTML and text versions
            html_content = personalized_content['body']
            text_content = self._html_to_text(html_content)
            
            # Attach both versions
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            success = self._send_email(msg, recipient.email)
            
            if success:
                logger.info(f"Successfully sent retainer email to {recipient.email} for law firm {self.law_firm.name}")
            else:
                logger.error(f"Failed to send retainer email to {recipient.email} for law firm {self.law_firm.name}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending retainer email to {recipient.email}: {str(e)}")
            return False
    
    def _personalize_email_content(self, email_template, recipient, signing_url, external_id=None):
        """
        Personalize email template content with recipient data
        """
        subject = email_template.subject
        body = email_template.body
        
        # Define replacements
        replacements = {
            '[First Name Injured]': recipient.first_name_injured or recipient.name.split()[0],
            '[Last Name Injured]': recipient.last_name_injured or recipient.name.split()[-1],
            '[Name]': recipient.name,
            '[State]': recipient.state,
            '[Age]': str(recipient.age) if recipient.age else 'N/A',
            '[External ID]': external_id or recipient.external_id,
            '[SIGNING_URL]': signing_url,
            '[LAW_FIRM_NAME]': self.law_firm.name,
            '[LAW_FIRM_EMAIL]': self.law_firm.contact_email,
            '[LAW_FIRM_PHONE]': self.law_firm.phone_number,
        }
        
        # Apply replacements
        for placeholder, value in replacements.items():
            subject = subject.replace(placeholder, value)
            body = body.replace(placeholder, value)
        
        return {
            'subject': subject,
            'body': body
        }
    
    def _get_from_address(self):
        """
        Get properly formatted from address
        """
        from_name = self.email_config.get('EMAIL_FROM_NAME', self.law_firm.name)
        from_email = self.email_config.get('DEFAULT_FROM_EMAIL', self.law_firm.contact_email)
        
        if from_name:
            return f"{from_name} <{from_email}>"
        return from_email
    
    def _html_to_text(self, html_content):
        """
        Convert HTML content to plain text for email clients that don't support HTML
        """
        # Strip HTML tags
        text = strip_tags(html_content)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _send_email(self, msg, to_email):
        """
        Send email using SMTP configuration
        """
        try:
            # Create SMTP connection
            if self.email_config['EMAIL_USE_SSL']:
                server = smtplib.SMTP_SSL(
                    self.email_config['EMAIL_HOST'], 
                    self.email_config['EMAIL_PORT']
                )
            else:
                server = smtplib.SMTP(
                    self.email_config['EMAIL_HOST'], 
                    self.email_config['EMAIL_PORT']
                )
                
                if self.email_config['EMAIL_USE_TLS']:
                    server.starttls()
            
            # Login
            server.login(
                self.email_config['EMAIL_HOST_USER'],
                self.email_config['EMAIL_HOST_PASSWORD']
            )
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
            return False
    
    def test_email_connection(self):
        """
        Test the email configuration for this law firm
        """
        try:
            if self.email_config['EMAIL_USE_SSL']:
                server = smtplib.SMTP_SSL(
                    self.email_config['EMAIL_HOST'], 
                    self.email_config['EMAIL_PORT']
                )
            else:
                server = smtplib.SMTP(
                    self.email_config['EMAIL_HOST'], 
                    self.email_config['EMAIL_PORT']
                )
                
                if self.email_config['EMAIL_USE_TLS']:
                    server.starttls()
            
            server.login(
                self.email_config['EMAIL_HOST_USER'],
                self.email_config['EMAIL_HOST_PASSWORD']
            )
            
            server.quit()
            return True, "Email configuration is valid"
            
        except Exception as e:
            return False, f"Email configuration error: {str(e)}"


def send_test_email(law_firm, test_email):
    """
    Send a test email to verify law firm email configuration
    """
    try:
        email_service = LawFirmEmailService(law_firm)
        
        # Create test message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Test Email from {law_firm.name}"
        msg['From'] = email_service._get_from_address()
        msg['To'] = test_email
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Test Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50;">Email Configuration Test</h1>
                <p>This is a test email from <strong>{law_firm.name}</strong>.</p>
                <p>If you receive this email, your email configuration is working correctly!</p>
                <hr style="border: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #666;">
                    Law Firm: {law_firm.name}<br>
                    Contact: {law_firm.contact_email}<br>
                    Phone: {law_firm.phone_number}
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Email Configuration Test
        
        This is a test email from {law_firm.name}.
        If you receive this email, your email configuration is working correctly!
        
        Law Firm: {law_firm.name}
        Contact: {law_firm.contact_email}
        Phone: {law_firm.phone_number}
        """
        
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        success = email_service._send_email(msg, test_email)
        
        if success:
            return True, f"Test email sent successfully to {test_email}"
        else:
            return False, f"Failed to send test email to {test_email}"
            
    except Exception as e:
        return False, f"Error sending test email: {str(e)}"
