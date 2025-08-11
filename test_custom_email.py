#!/usr/bin/env python
"""
Test script for the custom email service
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/app')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'roblex.settings')
django.setup()

from retainer_app.models import LawFirm, EmailTemplate, RetainerRecipient, ExcelUpload
from retainer_app.email_service import LawFirmEmailService, send_test_email


def test_email_configuration():
    """Test email configuration for law firms"""
    print("=== Email Configuration Test ===\n")
    
    law_firms = LawFirm.objects.all()
    for law_firm in law_firms:
        print(f"Law Firm: {law_firm.name}")
        print(f"Email Host: {law_firm.email_host}")
        print(f"Email User: {law_firm.email_host_user}")
        print(f"Has Config: {law_firm.has_email_config()}")
        print(f"From Name: {law_firm.email_from_name}")
        print(f"From Email: {law_firm.email_from_email or law_firm.contact_email}")
        
        if law_firm.has_email_config():
            print("✓ Email configuration is complete")
        else:
            print("✗ Email configuration is incomplete")
            
        print("-" * 40)


def test_email_template():
    """Test email template personalization"""
    print("\n=== Email Template Test ===\n")
    
    # Get Bullock Legal Group
    try:
        law_firm = LawFirm.objects.get(name='Bullock Legal Group')
        email_template = EmailTemplate.objects.filter(law_firm=law_firm).first()
        
        if not email_template:
            print("No email template found for Bullock Legal Group")
            return
            
        print(f"Template: {email_template.name}")
        print(f"Subject: {email_template.subject}")
        print(f"Body contains [SIGNING_URL]: {'[SIGNING_URL]' in email_template.body}")
        print(f"Body length: {len(email_template.body)} characters")
        
        # Create a mock recipient for testing
        class MockRecipient:
            def __init__(self):
                self.name = "John Doe"
                self.email = "john.doe@example.com"
                self.first_name_injured = "John"
                self.last_name_injured = "Doe"
                self.state = "Florida"
                self.age = 45
                self.external_id = "TEST-001"
        
        mock_recipient = MockRecipient()
        test_signing_url = "https://sign.nextkeystack.com/s/test-signature-link"
        
        # Test personalization
        email_service = LawFirmEmailService(law_firm)
        personalized = email_service._personalize_email_content(
            email_template, mock_recipient, test_signing_url, "TEST-EXT-001"
        )
        
        print(f"\nPersonalized Subject: {personalized['subject']}")
        print(f"Contains signing URL: {test_signing_url in personalized['body']}")
        print(f"Contains recipient name: {mock_recipient.name in personalized['body']}")
        
    except LawFirm.DoesNotExist:
        print("Bullock Legal Group not found")


def test_send_email():
    """Test sending actual email (requires valid SMTP config)"""
    print("\n=== Email Sending Test ===\n")
    
    try:
        law_firm = LawFirm.objects.get(name='Bullock Legal Group')
        
        if not law_firm.has_email_config():
            print("Law firm email configuration is incomplete")
            return
            
        if not law_firm.email_host_password or law_firm.email_host_password == 'your_app_password_here':
            print("Email password not set - skipping actual email test")
            print("To test email sending, set a real app password:")
            print(f"  law_firm.email_host_password = 'your_real_app_password'")
            print(f"  law_firm.save()")
            return
        
        # Send test email
        test_email_addr = "kumaranyuvaraj007@gmail.com"  # Replace with your test email
        success, message = send_test_email(law_firm, test_email_addr)
        
        if success:
            print(f"✓ Test email sent successfully to {test_email_addr}")
            print(f"Message: {message}")
        else:
            print(f"✗ Failed to send test email")
            print(f"Error: {message}")
            
    except LawFirm.DoesNotExist:
        print("Bullock Legal Group not found")
    except Exception as e:
        print(f"Error during email test: {str(e)}")


def main():
    print("Custom Email Service Test")
    print("=" * 50)
    
    test_email_configuration()
    test_email_template()
    test_send_email()
    
    print("\n=== Test Complete ===")
    print("\nTo set up email sending:")
    print("1. Get a Gmail app password from Google Account Settings")
    print("2. Update the law firm email configuration:")
    print("   law_firm.email_host_password = 'your_16_character_app_password'")
    print("   law_firm.save()")
    print("3. Run this test again to verify email sending")


if __name__ == "__main__":
    main()
