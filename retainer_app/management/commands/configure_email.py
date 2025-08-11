from django.core.management.base import BaseCommand
from django.core.management import CommandError
from retainer_app.models import LawFirm
from retainer_app.email_service import send_test_email


class Command(BaseCommand):
    help = 'Configure and test email settings for law firms'

    def add_arguments(self, parser):
        parser.add_argument(
            '--law-firm',
            type=str,
            help='Law firm name to configure',
        )
        parser.add_argument(
            '--email-host',
            type=str,
            default='smtp.gmail.com',
            help='SMTP server hostname',
        )
        parser.add_argument(
            '--email-port',
            type=int,
            default=587,
            help='SMTP server port',
        )
        parser.add_argument(
            '--email-user',
            type=str,
            help='SMTP username/email',
        )
        parser.add_argument(
            '--email-password',
            type=str,
            help='SMTP password/app password',
        )
        parser.add_argument(
            '--from-name',
            type=str,
            help='Display name for outgoing emails',
        )
        parser.add_argument(
            '--from-email',
            type=str,
            help='From email address',
        )
        parser.add_argument(
            '--test-email',
            type=str,
            help='Send test email to this address',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all law firms and their email configurations',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_law_firms()
            return

        law_firm_name = options.get('law_firm')
        if not law_firm_name:
            raise CommandError('Please specify --law-firm name')

        try:
            law_firm = LawFirm.objects.get(name=law_firm_name)
        except LawFirm.DoesNotExist:
            raise CommandError(f'Law firm "{law_firm_name}" not found')

        # Update email configuration if provided
        updated = False
        if options.get('email_host'):
            law_firm.email_host = options['email_host']
            updated = True

        if options.get('email_port'):
            law_firm.email_port = options['email_port']
            updated = True

        if options.get('email_user'):
            law_firm.email_host_user = options['email_user']
            updated = True

        if options.get('email_password'):
            law_firm.email_host_password = options['email_password']
            updated = True

        if options.get('from_name'):
            law_firm.email_from_name = options['from_name']
            updated = True

        if options.get('from_email'):
            law_firm.email_from_email = options['from_email']
            updated = True

        if updated:
            law_firm.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated email configuration for {law_firm.name}')
            )

        # Display current configuration
        self.display_law_firm_config(law_firm)

        # Send test email if requested
        if options.get('test_email'):
            self.send_test_email(law_firm, options['test_email'])

    def list_law_firms(self):
        """List all law firms and their email configurations"""
        law_firms = LawFirm.objects.all()
        
        self.stdout.write(self.style.HTTP_INFO('\nLaw Firm Email Configurations:'))
        self.stdout.write('=' * 60)
        
        for law_firm in law_firms:
            self.display_law_firm_config(law_firm)
            self.stdout.write('')

    def display_law_firm_config(self, law_firm):
        """Display email configuration for a law firm"""
        self.stdout.write(f'\nLaw Firm: {law_firm.name}')
        self.stdout.write(f'Email Host: {law_firm.email_host}')
        self.stdout.write(f'Email Port: {law_firm.email_port}')
        self.stdout.write(f'Email User: {law_firm.email_host_user}')
        self.stdout.write(f'From Name: {law_firm.email_from_name}')
        self.stdout.write(f'From Email: {law_firm.email_from_email or law_firm.contact_email}')
        
        if law_firm.has_email_config():
            self.stdout.write(
                self.style.SUCCESS('✓ Email configuration is complete')
            )
        else:
            self.stdout.write(
                self.style.ERROR('✗ Email configuration is incomplete')
            )
            missing = []
            if not law_firm.email_host:
                missing.append('email_host')
            if not law_firm.email_host_user:
                missing.append('email_host_user')
            if not law_firm.email_host_password:
                missing.append('email_host_password')
            
            self.stdout.write(f'Missing: {", ".join(missing)}')

    def send_test_email(self, law_firm, test_email):
        """Send test email"""
        self.stdout.write(f'\nSending test email to {test_email}...')
        
        try:
            success, message = send_test_email(law_firm, test_email)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {message}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ {message}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error sending test email: {str(e)}')
            )
