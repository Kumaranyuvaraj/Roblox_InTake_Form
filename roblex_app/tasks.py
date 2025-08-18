"""
Celery tasks for background processing in roblex_app
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_landing_page_lead_email(lead_id):
    """
    Send follow-up email to a landing page lead using EmailTemplate
    """
    try:
        from roblex_app.models import LandingPageLead, LandingPageLeadEmail, EmailTemplate
        
        # Get the lead
        lead = LandingPageLead.objects.get(id=lead_id)
        
        # Find appropriate email template
        # First try to find a template specifically for the lead source
        template_name = f"landing_page_{lead.lead_source}_followup"
        try:
            email_template = EmailTemplate.objects.get(name=template_name, is_active=True)
        except EmailTemplate.DoesNotExist:
            # Fall back to generic landing page template
            try:
                email_template = EmailTemplate.objects.get(name="landing_page_followup", is_active=True)
            except EmailTemplate.DoesNotExist:
                # Create a default template if none exists
                email_template = EmailTemplate.objects.create(
                    name="landing_page_followup",
                    template_type="followup",
                    subject="Thank you for your interest in our legal services",
                    body="""
Dear [NAME],

Thank you for reaching out to us through our website. We received your inquiry and one of our legal professionals will be in touch with you soon.

In the meantime, if you have any urgent questions, please don't hesitate to call us.

Best regards,
The Legal Team
                    """.strip(),
                    is_active=True
                )
        
        # Prepare email content
        subject = email_template.subject
        body = email_template.body
        
        # Replace placeholders
        body = body.replace('[NAME]', lead.name)
        body = body.replace('[EMAIL]', lead.email)
        body = body.replace('[PHONE]', lead.phone or 'Not provided')
        body = body.replace('[STATE]', lead.state_location or 'Not provided')
        body = body.replace('[USER FIRST NAME]', lead.name.split()[0] if lead.name else 'there')
        
        # Create email tracking record
        lead_email = LandingPageLeadEmail.objects.create(
            lead=lead,
            email_type=f"followup_{lead.lead_source}",
            recipient_email=lead.email,
            subject=subject,
            body=body,
            status='pending'
        )
        
        # Send the email
        try:
            send_mail(
                subject=subject,
                message=strip_tags(body),
                html_message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[lead.email],
                fail_silently=False
            )
            
            # Update email status
            lead_email.status = 'sent'
            lead_email.sent_at = timezone.now()
            lead_email.save()
            
            logger.info(f"Follow-up email sent successfully to lead {lead_id}")
            return f"Email sent successfully to {lead.email}"
            
        except Exception as email_error:
            # Update email status with error
            lead_email.status = 'failed'
            lead_email.error_message = str(email_error)
            lead_email.save()
            
            logger.error(f"Failed to send email to lead {lead_id}: {email_error}")
            raise email_error
            
    except Exception as e:
        logger.error(f"Error in send_landing_page_lead_email task for lead {lead_id}: {e}")
        raise


@shared_task
def auto_follow_up_new_leads():
    """
    Automatically send follow-up emails to new leads that haven't been emailed yet
    This can be run as a periodic task
    """
    try:
        from roblex_app.models import LandingPageLead
        from django.utils import timezone
        from datetime import timedelta
        
        # Find leads that are:
        # 1. Created more than 5 minutes ago (to avoid immediate auto-email)
        # 2. Haven't been emailed yet
        # 3. Are in 'new' status
        cutoff_time = timezone.now() - timedelta(minutes=5)
        
        new_leads = LandingPageLead.objects.filter(
            created_at__lt=cutoff_time,
            status='new'
        ).exclude(
            email_notifications__status='sent'
        )
        
        count = 0
        for lead in new_leads:
            try:
                send_landing_page_lead_email.delay(lead.id)
                count += 1
            except Exception as e:
                logger.error(f"Failed to queue auto follow-up for lead {lead.id}: {e}")
        
        logger.info(f"Queued auto follow-up emails for {count} new leads")
        return f"Queued auto follow-up emails for {count} new leads"
        
    except Exception as e:
        logger.error(f"Error in auto_follow_up_new_leads task: {e}")
        raise


@shared_task
def send_law_firm_notification_email(lead_id):
    """
    Send new lead notification email to law firm in background using EmailTemplate
    """
    try:
        from roblex_app.models import LandingPageLead, EmailLog, EmailTemplate
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        import smtplib
        
        # Get the lead
        lead = LandingPageLead.objects.get(id=lead_id)
        
        if not lead.law_firm or not lead.law_firm.contact_email:
            logger.warning(f"No law firm or contact email for lead {lead_id}")
            return "No law firm contact email available"
        
        # Get or create law firm notification template
        try:
            email_template = EmailTemplate.objects.get(name="landing_page_law_firm_notification", is_active=True)
        except EmailTemplate.DoesNotExist:
            # Create default template if it doesn't exist
            email_template = EmailTemplate.objects.create(
                name="landing_page_law_firm_notification",
                template_type="notification",
                subject="New Landing Page Lead: [NAME]",
                body="""New landing page lead submitted:

Name: [NAME]
Email: [EMAIL]
Phone: [PHONE]
State/Location: [STATE]
Lead Source: [LEAD_SOURCE]
Description: [DESCRIPTION]

Submitted: [SUBMITTED_DATE]
IP Address: [CLIENT_IP]

Please check your admin panel to view and manage this lead.""",
                is_active=True
            )
        
        # Prepare email content with placeholders
        subject = email_template.subject
        body = email_template.body
        
        # Replace placeholders
        subject = subject.replace('[NAME]', lead.name)
        body = body.replace('[NAME]', lead.name)
        body = body.replace('[EMAIL]', lead.email)
        body = body.replace('[PHONE]', lead.phone or 'Not provided')
        body = body.replace('[STATE]', lead.state_location or 'Not provided')
        body = body.replace('[LEAD_SOURCE]', lead.get_lead_source_display())
        body = body.replace('[DESCRIPTION]', lead.description or 'No description provided')
        body = body.replace('[SUBMITTED_DATE]', lead.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        body = body.replace('[CLIENT_IP]', lead.client_ip or 'Unknown')
        body = body.replace('[LEAD_ID]', str(lead.id))
        body = body.replace('[USER_AGENT]', lead.user_agent or 'Unknown')
        body = body.replace('[REFERRER]', lead.referrer or 'Direct')
        
        # Use existing email infrastructure
        email_log = EmailLog.objects.create(
            from_email=lead.law_firm.contact_email,
            to_email=lead.law_firm.contact_email,
            subject=subject,
            body=body,
            status='pending'
        )
        
        # Try to send email using SMTP
        try:
            msg = MIMEMultipart()
            msg['From'] = lead.law_firm.contact_email
            msg['To'] = lead.law_firm.contact_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Use default SMTP for now (can be enhanced with Brevo later)
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            email_log.status = 'sent'
            email_log.save()
            
            logger.info(f"Law firm notification sent successfully for lead {lead_id}")
            return f"Law firm notification sent to {lead.law_firm.contact_email}"
            
        except Exception as email_error:
            email_log.status = 'failed'
            email_log.error_message = str(email_error)
            email_log.save()
            
            logger.error(f"Failed to send law firm notification for lead {lead_id}: {email_error}")
            raise email_error
            
    except Exception as e:
        logger.error(f"Error in send_law_firm_notification_email task for lead {lead_id}: {e}")
        raise
