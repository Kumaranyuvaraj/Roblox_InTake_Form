from django.core.management.base import BaseCommand
from roblex_app.models import EmailTemplate


class Command(BaseCommand):
    help = 'Create or update email templates for NextKeySign document signing workflow'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'eligible_no_parent',
                'template_type': 'notification',
                'subject': 'Good News! Your Roblox Case is Eligible - Complete Your Documents',
                'body': '''Good news! Based on your responses, your case is eligible for the Roblox minor gamer claim.

Since the gamer is between 18 and 20 years old, no parental signature is required. You can now proceed to complete the intake and retainer forms.

👉 Please click the link below to digitally sign your retainer agreement and complete the process:
{{submitter.link}}

Document: {{template.name}}
From: {{account.name}}

Thank you for your cooperation, [User First Name]. If you need any help during the process, we're here to support you.

Best regards,  
The Legal Team'''
            },
            {
                'name': 'eligible_with_parent',
                'template_type': 'notification',
                'subject': 'Your Roblox Case is Eligible - Parental Signature Required',
                'body': '''Good news! Based on your responses, your case is eligible for the Roblox minor gamer claim.

Since the gamer is under 18 years old, we need a parental signature on the retainer agreement. Please ensure that a parent or legal guardian completes the signing process.

👉 Please click the link below to digitally sign the retainer agreement. A parent or guardian must complete this signature:
{{submitter.link}}

Document: {{template.name}}
From: {{account.name}}

Thank you for your cooperation, [User First Name]. If you need any help during the process, we're here to support you.

Best regards,  
The Legal Team'''
            },
            {
                'name': 'florida_disclosure',
                'template_type': 'disclosure',
                'subject': 'Florida Disclosure Required - Important Legal Notice',
                'body': '''Dear [User First Name],

As a Florida resident, we are required by law to provide you with specific disclosure information before proceeding with your case.

👉 Please click the link below to review and digitally sign the Florida disclosure document:
{{submitter.link}}

Document: {{template.name}}
From: {{account.name}}

This disclosure contains important information about your rights and our legal obligations under Florida law. Please read it carefully before signing.

After completing this disclosure, you will receive a separate email with your retainer agreement to finalize your case enrollment.

If you have any questions about the disclosure or need assistance, please don't hesitate to contact our office.

Best regards,  
The Legal Team'''
            },
            {
                'name': 'rejected',
                'template_type': 'rejection',
                'subject': 'Update on Your Roblox Case Inquiry',
                'body': '''Thank you for reaching out to us regarding your Roblox case inquiry.

After reviewing your responses, we have determined that your case does not meet our current criteria for representation at this time.

We appreciate you taking the time to provide the information, and we wish you the best in resolving your matter.

If you have any questions or if your circumstances change, please feel free to reach out to us again.

Best regards,  
The Legal Team'''
            }
        ]

        for template_data in templates:
            template, created = EmailTemplate.objects.update_or_create(
                name=template_data['name'],
                defaults={
                    'template_type': template_data['template_type'],
                    'subject': template_data['subject'],
                    'body': template_data['body'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created email template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Updated email template: {template.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully set up all NextKeySign email templates!')
        )
