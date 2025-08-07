from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from roblex_app.models import LawFirmUser


class Command(BaseCommand):
    help = 'Set up groups and permissions for law firm admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all permissions and recreate groups',
        )

    def handle(self, *args, **options):
        """Create groups and assign permissions for law firm administration"""
        
        if options['reset']:
            # Clear existing groups
            Group.objects.filter(name__in=['Law Firm Admin', 'Law Firm Staff', 'Law Firm Access', 'System Admin']).delete()
            self.stdout.write(self.style.WARNING('Cleared existing groups'))

        # Create Law Firm Admin group
        law_firm_admin_group, created = Group.objects.get_or_create(name='Law Firm Admin')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Law Firm Admin group'))

        # Create Law Firm Staff group
        law_firm_staff_group, created = Group.objects.get_or_create(name='Law Firm Staff')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Law Firm Staff group'))

        # Create Law Firm Access group (read-only)
        law_firm_access_group, created = Group.objects.get_or_create(name='Law Firm Access')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Law Firm Access group'))

        # Create System Admin group
        system_admin_group, created = Group.objects.get_or_create(name='System Admin')
        if created:
            self.stdout.write(self.style.SUCCESS('Created System Admin group'))

        # Define permissions for Law Firm Admins (full access to their firm's data)
        law_firm_admin_permissions = [
            # Core intake management
            'view_userdetail',
            'change_userdetail',
            'add_userdetail',
            'view_intakeform',
            'change_intakeform',
            'add_intakeform',
            
            # Document management
            'view_documentsubmission',
            'change_documentsubmission',
            'add_documentsubmission',
            'view_documentwebhookevent',
            
            # Email management
            'view_emaillog',
            'view_emailtemplate',
            'change_emailtemplate',
            
            # Questions and answers (read-only mostly)
            'view_question',
            'view_option',
            'view_useranswer',
            'change_useranswer',
            
            # Law firm management (limited)
            'view_lawfirm',
            'view_lawfirmuser',
            'change_lawfirmuser',  # Can modify users in their firm
            'add_lawfirmuser',     # Can add users to their firm
            
            # Document templates (view only)
            'view_documenttemplate',
        ]

        # Define permissions for Law Firm Staff (operational access)
        law_firm_staff_permissions = [
            # Core intake management
            'view_userdetail',
            'change_userdetail',
            'add_userdetail',
            'view_intakeform',
            'change_intakeform',
            'add_intakeform',
            
            # Document management (limited)
            'view_documentsubmission',
            'change_documentsubmission',
            'view_documentwebhookevent',
            
            # Email management (limited)
            'view_emaillog',
            'view_emailtemplate',
            
            # Questions and answers
            'view_question',
            'view_option',
            'view_useranswer',
            'change_useranswer',
            'add_useranswer',
            
            # Law firm info (view only)
            'view_lawfirm',
            'view_lawfirmuser',
            
            # Document templates (view only)
            'view_documenttemplate',
        ]

        # Define permissions for Law Firm Access (read-only)
        law_firm_access_permissions = [
            # View-only access to key data
            'view_userdetail',
            'view_intakeform',
            'view_documentsubmission',
            'view_documentwebhookevent',
            'view_emaillog',
            'view_emailtemplate',
            'view_question',
            'view_option',
            'view_useranswer',
            'view_lawfirm',
            'view_lawfirmuser',
            'view_documenttemplate',
        ]

        # System admin gets all permissions
        system_admin_permissions = [
            # All roblex_app permissions
            'add_documentsubmission', 'change_documentsubmission', 'delete_documentsubmission', 'view_documentsubmission',
            'add_documenttemplate', 'change_documenttemplate', 'delete_documenttemplate', 'view_documenttemplate',
            'add_documentwebhookevent', 'change_documentwebhookevent', 'delete_documentwebhookevent', 'view_documentwebhookevent',
            'add_emaillog', 'change_emaillog', 'delete_emaillog', 'view_emaillog',
            'add_emailtemplate', 'change_emailtemplate', 'delete_emailtemplate', 'view_emailtemplate',
            'add_intakeform', 'change_intakeform', 'delete_intakeform', 'view_intakeform',
            'add_lawfirm', 'change_lawfirm', 'delete_lawfirm', 'view_lawfirm',
            'add_lawfirmuser', 'change_lawfirmuser', 'delete_lawfirmuser', 'view_lawfirmuser',
            'add_option', 'change_option', 'delete_option', 'view_option',
            'add_question', 'change_question', 'delete_question', 'view_question',
            'add_useranswer', 'change_useranswer', 'delete_useranswer', 'view_useranswer',
            'add_userdetail', 'change_userdetail', 'delete_userdetail', 'view_userdetail',
        ]

        # Assign permissions to groups
        self._assign_permissions_to_group(law_firm_admin_group, law_firm_admin_permissions, 'roblex_app')
        self._assign_permissions_to_group(law_firm_staff_group, law_firm_staff_permissions, 'roblex_app')
        self._assign_permissions_to_group(law_firm_access_group, law_firm_access_permissions, 'roblex_app')
        self._assign_permissions_to_group(system_admin_group, system_admin_permissions, 'roblex_app')

        # Assign users to groups
        self._assign_users_to_groups(law_firm_admin_group, law_firm_staff_group, law_firm_access_group, system_admin_group)

        self.stdout.write(self.style.SUCCESS('Permission setup complete!'))
        
        # Show summary
        self._show_summary()

    def _assign_permissions_to_group(self, group, permission_codenames, app_label):
        """Assign permissions to a group"""
        assigned_count = 0
        
        for codename in permission_codenames:
            try:
                permission = Permission.objects.get(
                    codename=codename,
                    content_type__app_label=app_label
                )
                group.permissions.add(permission)
                assigned_count += 1
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Permission not found: {codename}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Assigned {assigned_count} permissions to {group.name}')
        )

    def _assign_users_to_groups(self, law_firm_admin_group, law_firm_staff_group, law_firm_access_group, system_admin_group):
        """Assign users to appropriate groups based on their roles"""
        
        # Assign superusers to System Admin group
        superusers = User.objects.filter(is_superuser=True)
        for user in superusers:
            user.groups.add(system_admin_group)
            self.stdout.write(
                self.style.SUCCESS(f'Added {user.username} to System Admin group')
            )

        # Assign law firm users to appropriate groups based on their role
        law_firm_users = LawFirmUser.objects.all()
        for law_firm_user in law_firm_users:
            user = law_firm_user.user
            role = law_firm_user.role
            
            if role == 'law_firm_admin':
                user.groups.add(law_firm_admin_group)
                self.stdout.write(
                    self.style.SUCCESS(f'Added {user.username} to Law Firm Admin group')
                )
            elif role == 'law_firm_staff':
                user.groups.add(law_firm_staff_group)
                self.stdout.write(
                    self.style.SUCCESS(f'Added {user.username} to Law Firm Staff group')
                )
            elif role == 'law_firm_access':
                user.groups.add(law_firm_access_group)
                self.stdout.write(
                    self.style.SUCCESS(f'Added {user.username} to Law Firm Access group')
                )
            elif role == 'super_admin':
                user.groups.add(system_admin_group)
                self.stdout.write(
                    self.style.SUCCESS(f'Added {user.username} to System Admin group (super_admin role)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Unknown role "{role}" for user {user.username}')
                )

    def _show_summary(self):
        """Show summary of groups and users"""
        self.stdout.write('\n=== GROUP SUMMARY ===')
        
        for group in Group.objects.all():
            user_count = group.user_set.count()
            perm_count = group.permissions.count()
            self.stdout.write(f'{group.name}: {user_count} users, {perm_count} permissions')
            
            for user in group.user_set.all():
                role_info = ''
                try:
                    law_firm_user = LawFirmUser.objects.get(user=user)
                    if law_firm_user.law_firm:
                        role_info = f' ({law_firm_user.law_firm.name})'
                except LawFirmUser.DoesNotExist:
                    if user.is_superuser:
                        role_info = ' (Superuser)'
                
                self.stdout.write(f'  - {user.username}{role_info}')
