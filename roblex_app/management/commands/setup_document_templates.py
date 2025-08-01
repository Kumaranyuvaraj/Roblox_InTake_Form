from django.core.management.base import BaseCommand
from roblex_app.models import DocumentTemplate


class Command(BaseCommand):
    help = 'Create sample DocumentTemplate records for testing DocuSeal integration'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'retainer_minor',
                'docuseal_template_id': 3,  # Replace with actual DocuSeal template ID
                'description': 'Retainer agreement for minors (under 18) requiring parental signature',
            },
            {
                'name': 'retainer_adult',
                'docuseal_template_id': 3,  # Replace with actual DocuSeal template ID
                'description': 'Retainer agreement for adults (18-20 years old)',
            },
            {
                'name': 'intake_supplemental',
                'docuseal_template_id': 1000003,  # Replace with actual DocuSeal template ID
                'description': 'Supplemental intake documentation',
            }
        ]

        for template_data in templates:
            template, created = DocumentTemplate.objects.update_or_create(
                name=template_data['name'],
                defaults={
                    'docuseal_template_id': template_data['docuseal_template_id'],
                    'description': template_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created document template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Updated document template: {template.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully set up all DocumentTemplate records!')
        )
        
        self.stdout.write(
            self.style.WARNING('Note: Please update the docuseal_template_id values with your actual DocuSeal template IDs.')
        )
