from django.core.management.base import BaseCommand
from roblex_app.models import DocumentTemplate, LawFirm


class Command(BaseCommand):
    help = 'Create DocumentTemplate records for global and law firm-specific templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--law-firm',
            type=str,
            help='Set up templates for a specific law firm (subdomain)'
        )
        parser.add_argument(
            '--global-only',
            action='store_true',
            help='Set up only global templates'
        )

    def handle(self, *args, **options):
        # Global templates (fallback when no law firm-specific template exists)
        global_templates = [
            {
                'name': 'retainer_minor',
                'docuseal_template_id': 3,  # Replace with actual DocuSeal template ID
                'description': 'Global: Retainer agreement for minors (under 18) requiring parental signature',
            },
            {
                'name': 'retainer_adult',
                'docuseal_template_id': 3,  # Replace with actual DocuSeal template ID
                'description': 'Global: Retainer agreement for adults (18-20 years old)',
            },
            {
                'name': 'florida_disclosure',
                'docuseal_template_id': 7,  # Template ID provided by user
                'description': 'Global: Florida Disclosure Document for zipcodes 32003-34997',
            }
        ]

        # Set up global templates
        self.stdout.write('Setting up global templates...')
        for template_data in global_templates:
            template, created = DocumentTemplate.objects.update_or_create(
                name=template_data['name'],
                law_firm=None,  # Global template
                defaults={
                    'docuseal_template_id': template_data['docuseal_template_id'],
                    'description': template_data['description'],
                    'is_active': True
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} global template: {template.name}')
            )

        if options['global_only']:
            self.stdout.write(self.style.SUCCESS('Global templates setup complete!'))
            return

        # Set up law firm-specific templates
        law_firm_subdomain = options.get('law_firm')
        if law_firm_subdomain:
            law_firms = [LawFirm.objects.get(subdomain=law_firm_subdomain)]
        else:
            law_firms = LawFirm.objects.filter(is_active=True).exclude(subdomain='default')

        for law_firm in law_firms:
            self.stdout.write(f'\nSetting up templates for {law_firm.name}...')
            
            # Example law firm-specific templates (with different template IDs)
            law_firm_templates = [
                {
                    'name': 'retainer_minor',
                    'docuseal_template_id': 100 + law_firm.id,  # Example: unique ID per law firm
                    'description': f'{law_firm.name}: Retainer agreement for minors with custom branding',
                },
                {
                    'name': 'retainer_adult',
                    'docuseal_template_id': 200 + law_firm.id,  # Example: unique ID per law firm
                    'description': f'{law_firm.name}: Retainer agreement for adults with custom branding',
                },
                {
                    'name': 'florida_disclosure',
                    'docuseal_template_id': 300 + law_firm.id,  # Example: unique ID per law firm
                    'description': f'{law_firm.name}: Florida Disclosure Document for zipcodes 32003-34997',
                }
                # Note: Not all law firms may need custom versions of all templates
            ]

            for template_data in law_firm_templates:
                template, created = DocumentTemplate.objects.update_or_create(
                    name=template_data['name'],
                    law_firm=law_firm,
                    defaults={
                        'docuseal_template_id': template_data['docuseal_template_id'],
                        'description': template_data['description'],
                        'is_active': True
                    }
                )
                
                action = 'Created' if created else 'Updated'
                self.stdout.write(
                    self.style.SUCCESS(f'  {action}: {template.name} (ID: {template.docuseal_template_id})')
                )

        self.stdout.write('\n' + self.style.SUCCESS('All document templates setup complete!'))
        
        # Show summary
        self.stdout.write('\nTemplate Summary:')
        global_count = DocumentTemplate.objects.filter(law_firm__isnull=True).count()
        firm_count = DocumentTemplate.objects.filter(law_firm__isnull=False).count()
        self.stdout.write(f'  Global templates: {global_count}')
        self.stdout.write(f'  Law firm-specific templates: {firm_count}')
        
        self.stdout.write('\n' + self.style.WARNING(
            'Note: Update docuseal_template_id values with your actual DocuSeal template IDs.'
        ))
