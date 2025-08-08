from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from roblex_app.models import LawFirm, LawFirmUser


class Command(BaseCommand):
    help = 'Set up law firms for multi-tenant system with admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-users',
            action='store_true',
            help='Create admin users for each law firm',
        )
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reset passwords for existing law firm users',
        )
        parser.add_argument(
            '--create-sample-users',
            action='store_true',
            help='Create sample users with different roles for testing',
        )

    def handle(self, *args, **options):
        """Create the law firms based on subdomains and optionally create admin users"""
        
        law_firms = [
            {
                'name': 'Default Law Firm',
                'subdomain': 'default',
                'contact_email': 'admin@robloxintake.com',
                'phone_number': '+1-555-0000',
                'address': 'Default Law Firm Office Address',
                'admin_user': {
                    'username': 'default_admin',
                    'email': 'admin@robloxintake.com',
                    'first_name': 'Default',
                    'last_name': 'Admin',
                    'password': 'default123'  # Change this in production
                }
            },
            {
                'name': 'Hilliard Law Firm',
                'subdomain': 'hilliard',
                'contact_email': 'contact@hilliardlaw.com',
                'phone_number': '+1-555-0001',
                'address': 'Hilliard Law Firm Office Address',
                'admin_user': {
                    'username': 'hilliard_admin',
                    'email': 'admin@hilliardlaw.com',
                    'first_name': 'Hilliard',
                    'last_name': 'Admin',
                    'password': 'hilliard123'  # Change this in production
                }
            },
            {
                'name': 'Bullock Legal',
                'subdomain': 'bullocklegalgroup',
                'contact_email': 'contact@bullocklegalgroup.com',
                'phone_number': '+1-555-0002',
                'address': 'Bullock Legal Office Address',
                'admin_user': {
                    'username': 'bullock_admin',
                    'email': 'admin@bullocklegalgroup.com',
                    'first_name': 'Bullock',
                    'last_name': 'Admin',
                    'password': 'bullock123'  # Change this in production
                }
            },
        ]
        
        created_count = 0
        updated_count = 0
        users_created = 0
        users_updated = 0
        
        for firm_data in law_firms:
            # Extract admin user data
            admin_user_data = firm_data.pop('admin_user', None)
            
            # Create/update law firm
            law_firm, created = LawFirm.objects.get_or_create(
                subdomain=firm_data['subdomain'],
                defaults=firm_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created law firm: {law_firm.name} ({law_firm.subdomain})')
                )
            else:
                # Update existing law firm
                for key, value in firm_data.items():
                    if key != 'subdomain':  # Don't update the unique field
                        setattr(law_firm, key, value)
                law_firm.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated law firm: {law_firm.name} ({law_firm.subdomain})')
                )
            
            # Create admin user if requested
            if options['create_users'] and admin_user_data:
                user_created, user_updated = self._create_or_update_admin_user(
                    law_firm, admin_user_data, options['reset_passwords']
                )
                users_created += user_created
                users_updated += user_updated
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Law firm setup complete. Created: {created_count}, Updated: {updated_count}'
            )
        )
        
        if options['create_users']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Admin users - Created: {users_created}, Updated: {users_updated}'
                )
            )
        
        # Show all law firms
        self.stdout.write('\nCurrent law firms:')
        for firm in LawFirm.objects.all().order_by('subdomain'):
            status = '✓ Active' if firm.is_active else '✗ Inactive'
            user_count = firm.users.count()
            self.stdout.write(f'  - {firm.name} ({firm.subdomain}) - {firm.contact_email} [{status}] - {user_count} users')
        
        # Create sample users if requested
        if options['create_sample_users']:
            self._create_sample_users()
    
    def _create_sample_users(self):
        """Create sample users with different roles for testing"""
        self.stdout.write('\n=== Creating Sample Users ===')
        
        sample_users = [
            {
                'law_firm_subdomain': 'hilliard',
                'users': [
                    {
                        'username': 'hilliard_staff',
                        'email': 'staff@hilliardlaw.com',
                        'first_name': 'Jane',
                        'last_name': 'Staff',
                        'password': 'staff123',
                        'role': 'law_firm_staff'
                    },
                    {
                        'username': 'hilliard_viewer',
                        'email': 'viewer@hilliardlaw.com',
                        'first_name': 'John',
                        'last_name': 'Viewer',
                        'password': 'viewer123',
                        'role': 'law_firm_access'
                    }
                ]
            },
            {
                'law_firm_subdomain': 'bullocklegalgroup',
                'users': [
                    {
                        'username': 'bullock_staff',
                        'email': 'staff@bullocklegalgroup.com',
                        'first_name': 'Sarah',
                        'last_name': 'Staff',
                        'password': 'staff123',
                        'role': 'law_firm_staff'
                    },
                    {
                        'username': 'bullock_viewer',
                        'email': 'viewer@bullocklegalgroup.com',
                        'first_name': 'Mike',
                        'last_name': 'Viewer',
                        'password': 'viewer123',
                        'role': 'law_firm_access'
                    }
                ]
            }
        ]
        
        for firm_data in sample_users:
            try:
                law_firm = LawFirm.objects.get(subdomain=firm_data['law_firm_subdomain'])
                
                for user_data in firm_data['users']:
                    created, updated = self._create_or_update_user_with_role(law_firm, user_data)
                    
            except LawFirm.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Law firm not found: {firm_data["law_firm_subdomain"]}')
                )
    
    def _create_or_update_user_with_role(self, law_firm, user_data):
        """Create or update a user with a specific role"""
        username = user_data['username']
        password = user_data['password']
        role = user_data['role']
        
        try:
            # Try to get existing user
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.WARNING(f'  User {username} already exists')
            )
            return 0, 0
                
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password=password,
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            user.is_staff = True
            user.is_active = True
            user.save()
            
            # Create law firm user profile
            LawFirmUser.objects.create(
                user=user,
                law_firm=law_firm,
                role=role,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'  Created {role} user: {username} for {law_firm.name}')
            )
            return 1, 0
    
    def _create_or_update_admin_user(self, law_firm, admin_user_data, reset_password=False):
        """Create or update admin user for a law firm"""
        username = admin_user_data['username']
        password = admin_user_data['password']
        
        try:
            # Try to get existing user
            user = User.objects.get(username=username)
            
            if reset_password:
                user.set_password(password)
                user.email = admin_user_data['email']
                user.first_name = admin_user_data['first_name']
                user.last_name = admin_user_data['last_name']
                user.is_staff = True
                user.is_active = True
                user.save()
                
                # Update or create law firm user profile
                law_firm_user, created = LawFirmUser.objects.get_or_create(
                    user=user,
                    defaults={
                        'law_firm': law_firm,
                        'role': 'law_firm_admin',
                        'is_active': True
                    }
                )
                
                if not created:
                    law_firm_user.law_firm = law_firm
                    law_firm_user.role = 'law_firm_admin'
                    law_firm_user.is_active = True
                    law_firm_user.save()
                
                self.stdout.write(
                    self.style.WARNING(f'  Updated admin user: {username} for {law_firm.name}')
                )
                return 0, 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'  User {username} already exists (use --reset-passwords to update)')
                )
                return 0, 0
                
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=admin_user_data['email'],
                password=password,
                first_name=admin_user_data['first_name'],
                last_name=admin_user_data['last_name']
            )
            user.is_staff = True
            user.is_active = True
            user.save()
            
            # Create law firm user profile
            LawFirmUser.objects.create(
                user=user,
                law_firm=law_firm,
                role='law_firm_admin',
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'  Created admin user: {username} for {law_firm.name}')
            )
            return 1, 0
