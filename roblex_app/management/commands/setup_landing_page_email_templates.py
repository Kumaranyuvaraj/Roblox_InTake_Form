"""
Management command to set up default email templates for landing page leads
"""
from django.core.management.base import BaseCommand
from roblex_app.models import EmailTemplate
from retainer_app.models import LawFirm


class Command(BaseCommand):
    help = 'Set up default email templates for landing page leads'

    def handle(self, *args, **options):
        self.stdout.write('Setting up landing page email templates...')
        
        # Template definitions
        templates = [
            {
                'name': 'landing_page_followup',
                'template_type': 'followup',
                'subject': 'Thank you for your interest in our legal services',
                'body': '''Dear [NAME],

Thank you for reaching out to us through our website. We received your inquiry and one of our legal professionals will be in touch with you soon.

Your submission details:
- Name: [NAME]
- Email: [EMAIL]
- Phone: [PHONE]
- Location: [STATE]

Our team will contact you within 1-2 business days to discuss your case further.

If you have any urgent questions, please don't hesitate to contact us.

Best regards,
The Legal Team'''
            },
            {
                'name': 'landing_page_parents_followup',
                'template_type': 'followup',
                'subject': 'We understand your concerns about your child and Roblox',
                'body': '''Dear [NAME],

Thank you for reaching out to us regarding your concerns about your child and their experience with Roblox. As a parent, we understand how important it is to protect your child and their safety and well-being online.

Your submission details:
- Name: [NAME]
- Email: [EMAIL]
- Phone: [PHONE]
- Location: [STATE]

We specialize in cases involving:
• Online safety violations
• Age-inappropriate content exposure
• Predatory behavior on gaming platforms
• Terms of service violations affecting minors

Our experienced legal team will review your case and contact you within 24-48 hours to discuss the next steps.

If you have any urgent questions or need immediate assistance, please do not hesitate to contact us.

Best regards,
The Legal Team

P.S. Please feel free to reply to this email with any additional information that might be helpful for your case.'''
            },
            {
                'name': 'landing_page_kids_followup',
                'template_type': 'followup',
                'subject': 'We are here to help with your Roblox concerns',
                'body': '''Dear [NAME],

Thank you for reaching out to us about your Roblox experience. We want you to know that your concerns are important to us, and we are here to help.

Your submission details:
- Name: [NAME]
- Email: [EMAIL]
- Phone: [PHONE]
- Location: [STATE]

We understand that gaming should be fun and safe for everyone. Our legal team specializes in helping young people who have had negative experiences on gaming platforms like Roblox.

We will review your case and have someone from our team contact you within 24-48 hours to discuss how we can help.

If you have any questions or if your parents would like to speak with us directly, please do not hesitate to contact us.

Best regards,
The Legal Team

Remember: Your safety and well-being are our top priority.'''
            },
            {
                'name': 'landing_page_reminder',
                'template_type': 'reminder',
                'subject': 'Following up on your legal inquiry',
                'body': '''Dear [NAME],

We wanted to follow up on the inquiry you submitted through our website recently. 

If you haven't heard from our team yet, please know that we are reviewing your case and will be in touch soon. Sometimes our response may take a bit longer due to the volume of cases we receive.

In the meantime, if you have any additional information or urgent questions, please feel free to reply to this email or contact us directly.

Thank you for your patience, and we look forward to speaking with you soon.

Best regards,
The Legal Team'''
            },
            {
                'name': 'landing_page_law_firm_notification',
                'template_type': 'notification',
                'subject': 'New Landing Page Lead: [NAME]',
                'body': '''New landing page lead submitted:

Name: [NAME]
Email: [EMAIL]
Phone: [PHONE]
State/Location: [STATE]
Lead Source: [LEAD_SOURCE]
Description: [DESCRIPTION]

Submitted: [SUBMITTED_DATE]
IP Address: [CLIENT_IP]

Please check your admin panel to view and manage this lead.

Lead Details:
- Lead ID: [LEAD_ID]
- User Agent: [USER_AGENT]
- Referrer: [REFERRER]

This is an automated notification. Please do not reply to this email.'''
            },
            {
                'name': 'landing_page_consultation_scheduled',
                'template_type': 'confirmation',
                'subject': 'Your consultation has been scheduled',
                'body': '''Dear [NAME],

Great news! We have scheduled your consultation to discuss your case.

Consultation Details:
- Date: [CONSULTATION_DATE]
- Time: [CONSULTATION_TIME]
- Duration: Approximately 30 minutes
- Format: [CONSULTATION_FORMAT] (Phone/Video/In-person)

What to expect:
• Review of your case details
• Discussion of potential legal options
• Explanation of our process
• Q&A session for any questions you may have

What to prepare:
• Any relevant documentation
• List of questions you'd like to ask
• Timeline of events (if applicable)

If you need to reschedule or have any questions before our consultation, please contact us as soon as possible.

We look forward to speaking with you and helping with your case.

Best regards,
The Legal Team'''
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            # Check if template already exists (using roblex_app dynamic EmailTemplate)
            existing_template = EmailTemplate.objects.filter(
                name=template_data['name']
            ).first()
            
            if existing_template:
                # Update existing template
                existing_template.template_type = template_data['template_type']
                existing_template.subject = template_data['subject']
                existing_template.body = template_data['body']
                existing_template.is_active = True
                existing_template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated template: {template_data["name"]}')
                )
            else:
                # Create new template
                EmailTemplate.objects.create(
                    name=template_data['name'],
                    template_type=template_data['template_type'],
                    subject=template_data['subject'],
                    body=template_data['body'],
                    is_active=True
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template_data["name"]}')
                )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Email Template Setup Complete!')
        self.stdout.write(f'Created: {created_count} templates')
        self.stdout.write(f'Updated: {updated_count} templates')
        self.stdout.write('='*50)
        
        # Show available templates
        self.stdout.write('\nAvailable Landing Page Email Templates:')
        templates = EmailTemplate.objects.filter(
            name__startswith='landing_page_'
        ).order_by('name')
        
        for template in templates:
            self.stdout.write(f'  • {template.name} ({template.template_type})')
        
        self.stdout.write('\nTo use these templates in admin actions or API calls,')
        self.stdout.write('reference them by name (e.g., "landing_page_parents_followup")')
