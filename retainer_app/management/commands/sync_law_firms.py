from django.core.management.base import BaseCommand
from retainer_app.models import LawFirm as RetainerLawFirm, LawFirmUser as RetainerLawFirmUser
from roblex_app.models import LawFirm as RoblexLawFirm, LawFirmUser as RoblexLawFirmUser
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Sync law firm data from roblex_app to retainer_app'

    def handle(self, *args, **options):
        self.stdout.write('Syncing law firm data from roblex_app to retainer_app...')
        
        # Sync law firms
        for roblex_firm in RoblexLawFirm.objects.all():
            retainer_firm, created = RetainerLawFirm.objects.get_or_create(
                name=roblex_firm.name,
                defaults={
                    'subdomain': roblex_firm.subdomain,
                    'contact_email': roblex_firm.contact_email,
                    'phone_number': roblex_firm.phone_number or '',
                    'address': roblex_firm.address or '',
                    'is_active': roblex_firm.is_active,
                }
            )
            if created:
                self.stdout.write(f'Created retainer law firm: {retainer_firm.name}')
            else:
                self.stdout.write(f'Law firm already exists: {retainer_firm.name}')
        
        # Sync law firm users
        for roblex_user in RoblexLawFirmUser.objects.all():
            if not roblex_user.law_firm:
                self.stdout.write(f'Skipping user {roblex_user.user.username} - no law firm assigned')
                continue
                
            try:
                retainer_firm = RetainerLawFirm.objects.get(name=roblex_user.law_firm.name)
                retainer_user, created = RetainerLawFirmUser.objects.get_or_create(
                    user=roblex_user.user,
                    defaults={
                        'law_firm': retainer_firm,
                        'role': roblex_user.role,
                        'is_active': roblex_user.is_active,
                    }
                )
                if created:
                    self.stdout.write(f'Created retainer law firm user: {roblex_user.user.username} -> {retainer_firm.name}')
                else:
                    self.stdout.write(f'Law firm user already exists: {roblex_user.user.username}')
            except RetainerLawFirm.DoesNotExist:
                self.stdout.write(f'Warning: Could not find retainer law firm for {roblex_user.law_firm.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully synced law firm data!')
        )
        
        # Display summary
        self.stdout.write('\n=== SUMMARY ===')
        self.stdout.write(f'Retainer Law Firms: {RetainerLawFirm.objects.count()}')
        self.stdout.write(f'Retainer Law Firm Users: {RetainerLawFirmUser.objects.count()}')
        self.stdout.write(f'Roblex Law Firms: {RoblexLawFirm.objects.count()}')
        self.stdout.write(f'Roblex Law Firm Users: {RoblexLawFirmUser.objects.count()}')
